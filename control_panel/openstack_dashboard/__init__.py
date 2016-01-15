import horizon
from ..abstract import *  # extend module
from ... import api
from ... import model
from openstack_dashboard import views
from horizon import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from openstack_dashboard.api import nova
from openstack_dashboard.api import network
from django.contrib import messages
from horizon import exceptions


class Estimator(Estimator):

    def _estimate_instance(self):
        params = self.request.REQUEST
        flavor = nova.flavor_get(self.request, params['flavor'])
        return self.estimator.estimate_instance(
            flavor_name=flavor.name,
            image_id=(params['image_id'] if params.get('source_type', '').endswith('image_id') else None),
            count=params['count'],
        )

    def _estimate_volume(self):
        return self.estimator.estimate_volume(
            volume_type='volume',  # TODO
            volume_size=self.request.REQUEST['size'],
        )

    def _estimate_ip_floating(self):
        return self.estimator.estimate_ip_floating(instance_id=None)


def get_user_home_url(user):
    return horizon.get_user_home(user)


def init_hooks():
    # Returns the text of error message with "Add funds" link.
    def get_error_message(request, est):
        return _("rs_insufficient_funds_please_fill_s_s") % (
            est['total_amount_text'],
            model.billing_get_pay_url(
                request.user.tenant_name,
                est['total_amount'],
                request.build_absolute_uri(reverse('rs_success_payment'))
            )
        )

    # Form submit hook.
    def assign_clean_method(form_class, resource):
        def new_clean(self):
            try:
                est = api.usage_estimate(self.request.user, resource, self.request)
                if not est['can_purchase']:
                    raise forms.ValidationError(mark_safe(get_error_message(self.request, est)))
            except model.NonRsTenantError:
                pass
            return old_clean(self)
        old_clean = form_class.clean
        form_class.clean = new_clean
    for k, v in init_hooks.forms_to_validate().items():
        assign_clean_method(v, k)

    # Floating IP link & form hook.
    def tenant_floating_ip_allocate(request, pool=None):
        try:
            est = api.usage_estimate(request.user, 'ip.floating', request)
            if not est['can_purchase']:
                messages.add_message(request, messages.ERROR, mark_safe(get_error_message(request, est)))
                raise exceptions.Http302(request.get_full_path())
        except model.NonRsTenantError:
            pass
        return old_tenant_floating_ip_allocate(request, pool)
    old_tenant_floating_ip_allocate = network.tenant_floating_ip_allocate
    network.tenant_floating_ip_allocate = tenant_floating_ip_allocate

    # Login form is replaced by SSO renewal redirect.
    views.splash = api.tenant_sso_login_view_decorator(views.splash)

def forms_to_validate():
    from openstack_dashboard.dashboards.project.instances.workflows.create_instance import SetInstanceDetailsAction
    from openstack_dashboard.dashboards.project.volumes.forms import CreateForm as InstanceCreateForm
    return {
        'instance': SetInstanceDetailsAction,
        'volume': InstanceCreateForm
    }

init_hooks.forms_to_validate = forms_to_validate

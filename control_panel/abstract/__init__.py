import django.contrib.auth
import openstack_auth.user
import django.conf
import re
from ... import usage


def authenticate(request, username, password):
    user = django.contrib.auth.authenticate(
        request=request,
        username=username,
        password=password,
        auth_url=django.conf.settings.OPENSTACK_KEYSTONE_URL,
    )
    django.contrib.auth.login(request, user)
    openstack_auth.user.set_session_from_user(request, user)


def get_user_home_url(user):
    raise NotImplementedError()


def init_hooks():
    """
    This method is automatically called from urls.py. We cannot call it
    directly from the module code, because the stage is not enough late
    for it, and the hooks (e.g. form classes modifications) are not
    applied on the first request (I don't know why).
    """
    raise NotImplementedError()


class Estimator:
    def __init__(self, request, tenant_key, resource, skip_funds_check=False):
        self.tenant_key = tenant_key
        self.resource = resource
        self.request = request
        self.estimator = usage.Estimator(tenant_key, skip_funds_check)

    def get_estimation(self):
        method_name = "_estimate_" + re.sub(r'[^a-zA-Z0-9_]', '_', self.resource)
        if method_name in dir(self):
            return getattr(self, method_name)()
        raise Exception("Unknown resource to estimate: %s" % self.resource)

    def _estimate_instance(self):
        raise NotImplementedError()

    def _estimate_volume(self):
        raise NotImplementedError()

    def _estimate_ip_floating(self):
        raise NotImplementedError()

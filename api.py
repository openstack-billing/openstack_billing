import urllib
from django.http import HttpResponseRedirect
from . import get_control_panel_module
from . import usage
from . import sso
from . import model


def tenant_on(tenant_key, billing_url=None):
    # Deal with tenant.
    model.tenant_create(tenant_key)
    tenant = model.tenant_get(tenant_key)
    model.tenant_set_options(tenant, {'billing_url': billing_url})
    model.tenant_update_enabled(tenant, True)
    # Deal with user.
    model.user_create(tenant_key, tenant.id)
    user = model.user_get(tenant_key, tenant.id)
    model.user_update_enabled(user, True)


def tenant_off(tenant_key, billing_url=None):
    # Deal with tenant.
    tenant = model.tenant_get(tenant_key)
    if tenant is None:
        return
    model.tenant_update_enabled(tenant, False)
    model.tenant_set_options(tenant, {'billing_url': billing_url})
    # Deal with user.
    user = model.user_get(tenant_key, tenant.id)
    if user is None:
        return
    model.user_update_enabled(user, False)


def tenant_sso_get_mark(tenant_key):
    tenant = model.tenant_get(tenant_key)
    if tenant is None:
        raise Exception("Cannot find tenant %s" % tenant_key)
    user = model.user_get(tenant_key, tenant.id)
    if user is None:
        raise Exception("Cannot find a user with username %s and tenant_id %s" % (tenant_key, tenant.id))
    return sso.create_mark(user)


def tenant_sso_login_by_mark(request, mark):
    tenant_key = sso.get_tenant_key_by_mark(mark)
    tenant = model.tenant_get(tenant_key)
    if tenant is None:
        raise sso.SsoException("Cannot find a tenant with key %", tenant_key)
    user = model.user_get(tenant_key, tenant.id)
    if user is None:
        raise sso.SsoException("Cannot find a user with username %s and tenant_id %s" % (tenant_key, tenant.id))
    tmp_pass = model.get_rnd_pass()
    model.user_update(user, password=tmp_pass)
    # Don't throw for failed auth, just return all available information and success flag
    success = get_control_panel_module().authenticate(
        request=request,
        username=user.name,
        password=tmp_pass,
    )
    options = model.tenant_get_options(tenant)
    result = {
        "rs_billing_url": options["billing_url"],
        "rs_last_tenant_key": tenant_key,
    } if "billing_url" in options else {}
    result["auth_success"] = success
    return result


def tenant_sso_login_view_decorator(orig_login_view):
    def handler(request, **args):
        billing_url = request.COOKIES.get("rs_billing_url", None)
        if billing_url and request.GET.get("form", None) is None:
            billing_url += "?" + urllib.urlencode([
                ('action', 'auth'),
                ('tenant_key', request.COOKIES.get('rs_last_tenant_key', '')),
                ('payload', request.GET.get('next', ''))
            ])
            return HttpResponseRedirect(billing_url)
        else:
            resp = orig_login_view(request, **args)
            resp.set_cookie('rs_billing_url', '')
            return resp
    return handler


def usage_fetch(stamp_start, stamp_end):
    return usage.usage_fetch(stamp_start, stamp_end)


def usage_estimate(user, resource, request, skip_funds_check=False):
    return usage.usage_estimate(user, resource, request, skip_funds_check)

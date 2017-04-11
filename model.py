import keystoneclient
import urllib
import json
import os
from keystoneclient.v2_0 import client
from . import settings


keystone = client.Client(
    username=settings.KEYSTONE_ADMIN_USER,
    tenant_name=settings.KEYSTONE_ADMIN_TENANT_NAME,
    password=settings.KEYSTONE_ADMIN_PASSWORD,
    auth_url=settings.KEYSTONE_AUTH_URL
)


class NonRsTenantError(ValueError):
    pass


def get_rnd_pass():
    return os.urandom(16).encode('hex')


def tenant_create(tenant_key):
    try:
        return keystone.tenants.create(tenant_name=tenant_key)
    except keystoneclient.exceptions.Conflict:
        return None


def tenant_update_enabled(tenant, enabled):
    tenant.update(enabled=enabled)


def tenant_get(tenant_key):
    # TODO: speedup (no such API in keystone yet).
    tenants = keystone.tenants.list()
    for tenant in tenants:
        if tenant.name == tenant_key:
            return tenant
    return None


def tenant_get_by_ids(ids):
    # TODO: speedup (no such API in keystone yet).
    if len(ids) == 0:
        return []
    ids = set(ids)
    result = []
    tenants = keystone.tenants.list()
    for tenant in tenants:
        if tenant.id in ids:
            result.append(tenant)
    return result


def user_create(tenant_key, tenant_id):
    try:
        keystone.users.create(name=tenant_key, password=get_rnd_pass(), email=None, tenant_id=tenant_id)
    except keystoneclient.exceptions.Conflict:
        pass


def user_update_enabled(user, enabled):
    keystone.users.update_enabled(user, enabled)


def user_update(user, **kwargs):
    keystone.users.update(user, **kwargs)


def user_get(tenant_key, tenant_id):
    users = keystone.users.list(tenant_id=tenant_id)
    for user in users:
        if user.name == tenant_key:
            return user
    return None


def tenant_set_options(tenant, options):
    descr = json.dumps(options)
    tenant.update(description=descr)


def tenant_get_options(tenant):
    try:
        return json.loads(tenant.description)
    except (ValueError, TypeError):
        raise NonRsTenantError("Cannot decode description of tenant %s" % tenant.name)


def billing_get_pay_url(tenant_key, amount, retpath):
    options = tenant_get_options(tenant_get(tenant_key))
    return options['billing_url'] + "?" + urllib.urlencode([
        ('action', 'pay'),
        ('sum', amount),
        ('retpath', retpath)
    ])


def billing_get_estimate_url(tenant_key):
    options = tenant_get_options(tenant_get(tenant_key))
    return options['billing_url'] + "?action=estimate"


_rs_tenant_keys_cache = {}
def billing_get_top_iframe_url(tenant_key):
    if tenant_key not in _rs_tenant_keys_cache:
        tenant = tenant_get(tenant_key)
        try:
            tenant_get_options(tenant)
            _rs_tenant_keys_cache[tenant_key] = True
        except Exception:
            _rs_tenant_keys_cache[tenant_key] = False
    return settings.TOP_IFRAME_URL if _rs_tenant_keys_cache[tenant_key] else ""

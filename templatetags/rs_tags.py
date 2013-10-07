from django import template
from .. import settings
from .. import model

register = template.Library()


@register.simple_tag
def rs_settings(k):
    return getattr(settings, k)


@register.simple_tag(takes_context=True)
def rs_top_iframe_url(context):
    return model.billing_get_top_iframe_url(context['request'].user.tenant_name)


@register.simple_tag(takes_context=True)
def rs_full_root_url(context):
    return context['request'].build_absolute_uri('/')

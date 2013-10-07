from . import settings
from . import api
from . import model
from . import usage
from . import get_control_panel_module
from django.http import (HttpResponse, HttpResponseRedirect)
from django.core.urlresolvers import reverse
from django.shortcuts import render
import traceback
import urllib
import sys


def _format_exception():
    exc_type, exc_value, exc_traceback = sys.exc_info()
    return (
        "".join(traceback.format_exception(exc_type, exc_value, tb=None)) +
        "Traceback:\n" +
        "".join(traceback.format_tb(exc_traceback))
    )


def api_handler_decorator(handler):
    def wrapper(request):
        try:
            if request.REQUEST.get("secret") != settings.SECRET:
                raise Exception("Invalid 'secret' value!")
            result = handler(request)
            return HttpResponse(result, content_type="text/plain")
        except:
            return HttpResponse("Error: " + _format_exception(), content_type="text/plain", status=500)
    return wrapper


def web_handler_decorator(handler):
    def wrapper(request):
        try:
            return handler(request)
        except:
            return HttpResponse("Error: " + _format_exception(), content_type="text/plain", status=500)
    return wrapper


@api_handler_decorator
def provisioning_api_handler(request):
    params = request.REQUEST
    tenant_key = params['tenant_key']
    tenant_state = params['tenant_state']
    tenant_billing_url = params['tenant_billing_url']
    if int(tenant_state) != 0:
        api.tenant_on(tenant_key, billing_url=tenant_billing_url)
    else:
        api.tenant_off(tenant_key, billing_url=tenant_billing_url)
    return 'OK'


@api_handler_decorator
def sso_api_handler(request):
    params = request.REQUEST
    tenant_key = params['tenant_key']
    payload = params['payload'] if 'payload' in params else None
    args = dict()
    args["mark"] = api.tenant_sso_get_mark(tenant_key)
    if payload is not None:
        args["payload"] = payload
    url = request.build_absolute_uri(reverse('sso_api_login') + "?" + urllib.urlencode(args))
    return url


@web_handler_decorator
def sso_api_login_handler(request):
    params = request.REQUEST
    mark = params['mark']
    cookies = api.tenant_sso_login_by_mark(request, mark)
    payload = params['payload'] if 'payload' in params else get_control_panel_module().get_user_home_url(request.user)
    response = HttpResponseRedirect(payload)
    for k, v in cookies.items():
        response.set_cookie(k, v, expires="Mon, 18-Jan-2038 13:01:52 GMT")
    return response


@api_handler_decorator
def usage_api_handler(request):
    params = request.REQUEST
    stamp_start = params['stamp_start']
    stamp_end = params['stamp_end'] if 'stamp_end' in params else None
    response = list()
    response.append(usage.protocol_start())
    for row in api.usage_fetch(stamp_start, stamp_end):
        response.append(usage.protocol_row(row))
    response.append(usage.protocol_end())
    return "".join(response)


@web_handler_decorator
def estimate_ajax_handler(request):
    params = request.REQUEST
    resource = params['resource']
    try:
        result = api.usage_estimate(request.user, resource, request, skip_funds_check=True)
        response = render(request, '_estimate_' + resource + '.html', result)
    except model.NonRsTenantError:
        response = HttpResponse('', 'text/html')
    return response


@web_handler_decorator
def success_payment_handler(request):
    response = render(request, '_success_payment.html')
    return response

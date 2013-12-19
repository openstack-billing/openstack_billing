from django.conf.urls import *
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import views
from . import handlers
from . import api

urlpatterns = patterns(
    '',
    url(r'^provisioning_api/?$', csrf_exempt(handlers.provisioning_api_handler)),
    url(r'^sso_api/?$', csrf_exempt(handlers.sso_api_handler)),
    url(r'^sso_api/login/(?P<mark>\w+)/?$', csrf_exempt(handlers.sso_api_login_handler), name='sso_api_login'),
    url(r'^usage_api/?$', csrf_exempt(handlers.usage_api_handler)),
    url(r'^estimate_ajax/?$', handlers.estimate_ajax_handler, name='rs_estimate_ajax'),
    url(r'^success_payment/?$', handlers.success_payment_handler, name='rs_success_payment'),
)

# Redefine login page.
views.login = api.tenant_sso_login_view_decorator(views.login)

OpenStack Dashboard Billing Integration Plug-in
===============================================

This is an OpenStack Dashboard plug-in that provides a way to integrate third-party billing solution to your OpenStack deployment.

The plug-in was originally developed by Velvica inc. to integrate Velvica Billing and Management Platform
with OpenStack Horizon and Ceilometer. The plug-in can be extended to support custom OpenStack Dashboard implementations as well.

Installation
------------

1. Place the module directory to the place where your regular Python packages
   and Django apps reside, e.g. `/usr/lib/python2.7/dist-packages`

2. Add the following lines to your OpenStack Dashboard `settings.py` right after
   `TEMPLATE_DIRS` and `INSTALLED_APPS` variables set:

   ```python
   # Install billing hooks AND add it to settings for later usage in urls.py
   import openstack_billing as BILLING_APP
   BILLING_APP.django_install_hooks(__name__)
   ```

3. Add to `urls.py`:

   ```python
   # Install billing hooks.
   settings.BILLING_APP.django_install_hooks(__name__)
   ```

4. Configure options in /etc/openstack_billing/local_settings file:

   ```python
   SECRET = "secret_string_to_control_access_to_api_endpoints"
   KEYSTONE_AUTH_URL = "http://keystone_ip_address:and_port/v2.0"
   KEYSTONE_ADMIN_USER = "admin"
   KEYSTONE_ADMIN_PASSWORD = "qwerty"
   TOP_IFRAME_URL = "http://billing_account_info_widget_url/"
   CONTROL_PANEL = "openstack_dashboard_icehouse"
   ```

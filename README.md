OpenStack Dashboard Billing Integration Plug-in
===============================================

This is an OpenStack Dashboard plug-in that provides a way to integrate third-party billing solution to your OpenStack deployment.

The plug-in was originally developed by Velvica Inc. to integrate Velvica Billing and Management Platform
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

4. Create the file `/etc/openstack_billing/local_settings` and configure options in it:

   ```python
   SECRET = "paste here a secret string from Velvica's service edit form"
   TOP_IFRAME_URL = "http://billing_dashboard_domain/header/"
   KEYSTONE_AUTH_URL = "http://keystone_ip_address:and_port/v2.0"
   KEYSTONE_ADMIN_USER = "admin"
   KEYSTONE_ADMIN_PASSWORD = "admin's password"
   KEYSTONE_ADMIN_TENANT_NAME = "admin"
   CONTROL_PANEL = "openstack_dashboard_icehouse"
   ```

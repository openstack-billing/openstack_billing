This is a Django app which adds support of RentSoft billing to an OpenStack
control panels (like openstack_dashboard and horizon).

RentSoft Corp. (http://rentsoftcorp.com) provides a cloud billing solution
for OpenStack installations.

To make the app workable:

1. Place the module directory to the place where your regular Python packages
   and Django apps reside, e.g. /usr/lib/python2.7/dist-packages

2. Add following lines to settings.py of your openstack_dashboard after
   TEMPLATE_DIRS and INSTALLED_APPS variables, but NOT too low (not at the
   end of the file, because else local messages of the module may not be
   properly initialized):

   # Install billing hooks AND add it to settings for later usage in urls.py.
   import openstack_billing as BILLING_APP
   BILLING_APP.django_install_hooks(__name__)

3. Add to urls.py:

   # Install billing hooks.
   settings.BILLING_APP.django_install_hooks(__name__)

4. Configure options in /etc/openstack_billing/local_settings file:
   - SECRET
   - KEYSTONE_AUTH_URL
   - KEYSTONE_ADMIN_USER
   - KEYSTONE_ADMIN_PASSWORD
   - TOP_IFRAME_URL

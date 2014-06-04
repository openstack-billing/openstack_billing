import sys
from os.path import abspath, dirname
from django.conf.urls import url, include
from . import settings
from . import control_panel


def get_control_panel_module():
    return control_panel.get_control_panel_module(settings.CONTROL_PANEL)


def django_install_hooks(caller_module_name):
    """
    This method must be called at the very end of the caller
    Django app's settings.py and urls.py.

    Add to settings.py:
      # Install billing hooks AND add it to settings for later usage in urls.py.
      import openstack_billing as BILLING_APP
      BILLING_APP.django_install_hooks(__name__)

    Add to urls.py:
      # Install billing hooks.
      settings.BILLING_APP.django_install_hooks(__name__)
    """
    # We do not use too many logic in this hook, because it is called
    # on a very early stage (in settings.py).
    caller = sys.modules[caller_module_name]

    if hasattr(caller, "TEMPLATE_DIRS"):
        # Build path manually, do not use get_control_panel_module() here
        # because it initializes lots of libraries. These libraries may expect
        # settings.py already filled, but we are in the middle of settings.py
        # now with this hook...
        panels_dir = dirname(abspath(__file__)) + "/control_panel"
        cur_panel_dir = panels_dir + "/" + settings.CONTROL_PANEL
        caller.TEMPLATE_DIRS = (
            # Inject parent's ROOT_PATH to access parent templates.
            dirname(abspath(caller.__file__)),
            # Inject path to other panels to allow template inheritance
            panels_dir,
            cur_panel_dir
        ) + caller.TEMPLATE_DIRS

    if hasattr(caller, "INSTALLED_APPS"):
        caller.INSTALLED_APPS += (__name__, )  # note that INSTALLED_APPS may be list(), not tuple()

    if hasattr(caller, "urlpatterns"):
        caller.urlpatterns += (
            url(r'^billing/', include(__name__ + '.urls')),
        )
        # It's safe to call init_hooks() from this point, because we
        # are in urls.py, and the stage is late enough.
        get_control_panel_module().init_hooks()


# In debug mode we reload the server
if settings.APP_RELOADER:
    from . import app_reloader
    app_reloader.start(interval=1)

# All control panel specific things are in this directory.
# E.g. openstack_dashboard.py contains all stuff related
# to openstack_dashboard and horizon.
import sys


def get_control_panel_module(control_panel_name):
    mod_name = __name__ + "." + control_panel_name
    __import__(mod_name)
    return sys.modules[mod_name]

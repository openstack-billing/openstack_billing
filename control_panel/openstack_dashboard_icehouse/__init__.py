from ..openstack_dashboard import *

def forms_to_validate():
    from openstack_dashboard.dashboards.project.instances.workflows.create_instance import SetInstanceDetailsAction
    from openstack_dashboard.dashboards.project.volumes.volumes.forms import CreateForm as InstanceCreateForm
    return {
        'instance': SetInstanceDetailsAction,
        'volume': InstanceCreateForm
    }

init_hooks.forms_to_validate = forms_to_validate

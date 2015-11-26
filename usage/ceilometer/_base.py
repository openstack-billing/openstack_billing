from novaclient.exceptions import NotFound
from novaclient.v1_1 import client

from .. import abstract
from ... import settings


class NovaBased(abstract.Meter):

    def __init__(self):
        self.api = client.Client(
            settings.KEYSTONE_ADMIN_USER,
            settings.KEYSTONE_ADMIN_PASSWORD,
            settings.KEYSTONE_ADMIN_USER,
            settings.KEYSTONE_AUTH_URL,
            service_type="compute"
        )

    def assert_resource_terminated(self, resource_class, resource_id):
        try:
            self.api.servers.get(resource_id)
            terminated = False
        except NotFound as e:
            terminated = True
        if not terminated:
            raise Exception((
                "Fatal error! Last meter for resource %s (%s) was too long ago "
                "but according to Nova API this resource is currently alive. "
                "Maybe ceilometer is down! Recheck ASAP" % (resource_class, resource_id)
            ))

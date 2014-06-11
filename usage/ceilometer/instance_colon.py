from . import _base
from ... import usage


class Meter(_base.NovaBased):

    selectors = [
        "resource_id",
        "counter_volume",
        "resource_metadata.image_meta.base_image_ref",
        "resource_metadata.image.id"
    ]

    def matches(self, obj_class, sample):
        return str(obj_class).startswith("instance:")

    def process_sample(self, sample):
        if sample.get("event_type", "exists") == "end":
            self.assert_resource_terminated(sample["counter_name"], sample["resource_id"])
        try:
            image_id = sample['resource_metadata']['image_meta']['base_image_ref']
        except KeyError:
            try:
                image_id = sample['resource_metadata']['image']['id']
            except KeyError:
                raise Exception(repr(sample))
        return {
            "obj_class": usage.usage_build_instance_class(sample['counter_name'], image_id),
            "obj_key": str(sample['resource_id']),
            "owner_key": "",
            "volume": 1,
        }

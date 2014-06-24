from . import _base


class Meter(_base.NovaBased):

    selectors = ["resource_id", "counter_volume"]
    matches = "cpu"

    def process_sample(self, sample):
        if sample.get("event_type", "exists") == "end":
            self.assert_resource_terminated("cpu", sample["resource_id"])
        return {
            "obj_class": "cpu",
            "obj_key": sample['resource_id'] + ":cpu",
            "owner_key": str(sample['resource_id']),
            "volume": float(sample.get("counter_volume", None)) / 1000000000,  # ns -> s
            "track_activity": True
        }

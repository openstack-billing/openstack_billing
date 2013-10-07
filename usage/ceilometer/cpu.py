from .. import abstract


class Meter(abstract.Meter):

    selectors = ["resource_id", "counter_volume"]
    matches = "cpu"

    def process_sample(self, sample):
        return {
            "obj_class": "cpu",
            "obj_key": sample['resource_id'] + ":cpu",
            "owner_key": str(sample['resource_id']),
            "volume": float(sample.get("counter_volume", None)) / 1000000000,  # ns -> s
        }

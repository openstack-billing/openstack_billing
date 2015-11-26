from .. import abstract


class Meter(abstract.Meter):

    selectors = ["resource_id"]
    matches = "ip.floating"

    def process_sample(self, sample):
        return {
            "obj_class": "ip.floating",
            "obj_key": sample['resource_id'] + ":ip.floating",
            "owner_key": str(sample['resource_id']),
            "volume": 1,
            "delta": 60
        }

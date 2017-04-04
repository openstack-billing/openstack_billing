from .. import abstract


class Meter(abstract.Meter):

    selectors = ["resource_id", "resource_metadata.event_type"]
    matches = "volume.size"  # volume counter is just for volume existance fact

    def process_sample(self, sample):
        is_end = sample['resource_metadata']['event_type'] == 'volume.delete.end'
        return {
            "obj_class": "volume",
            "obj_key": sample['resource_id'] + ":volume",
            "owner_key": None,
            "volume": int(sample["counter_volume"]) if not is_end else 0,
            "event_type": "end" if is_end else "exists",
            "delta": 60
        }


from . import _base
import pymongo
from ... import settings

class Meter(_base.NovaBased):

    selectors = ["resource_id", "counter_volume"]
    matches = "cpu"

    def process_sample(self, sample):
        if sample.get("event_type", "exists") == "end":
            self.assert_resource_terminated("cpu", sample["resource_id"])

        conn = pymongo.mongo_client.MongoClient(settings.CEILOMETER_DSN)
        db = conn[pymongo.uri_parser.parse_uri(settings.CEILOMETER_DSN)['database']]
        db.meter.ensure_index([("timestamp", 1), ("_id", 1)])
        prev_meter = db.meter.find({"timestamp":  {"$lt": sample['timestamp']}, "resource_id": sample['resource_id'], "counter_name": "cpu"}).sort([("timestamp", -1)]).limit(1)
        prev_volume = 20
        for prev_sample in prev_meter:
            prev_volume = float(prev_sample.get("counter_volume", None))
        
        return {
            "obj_class": "cpu",
            "obj_key": sample['resource_id'] + ":cpu",
            "owner_key": str(sample['resource_id']),
            "volume": (float(sample.get("counter_volume", None)) - prev_volume) / 1000000000,  # ns -> s
            "track_activity": True
        }

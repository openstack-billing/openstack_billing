import datetime
import time
import pymongo
from pymongo.errors import DuplicateKeyError
from ... import settings
from ... import model
from .. import abstract


class MeterSet(abstract.MeterSet):

    def __init__(self):
        self.tenant_key_by_project_id = {}
        abstract.MeterSet.__init__(self, __name__)

    def get_sample_obj_class(self, s):
        return s['counter_name']

    def get_sample_project_id(self, s):
        return s['project_id']


def usage_fetch(stamp_start, stamp_end):
    time_start = datetime.datetime.fromtimestamp(float(stamp_start))
    if stamp_end is not None:
        time_end = datetime.datetime.fromtimestamp(float(stamp_end))
    else:
        time_end = datetime.datetime.now();
    meter_set = MeterSet()

    # Use Ceilometer database directly because there is no such API
    # to get all meters for the given time period
    conn = pymongo.mongo_client.MongoClient(settings.CEILOMETER_DSN)
    db = conn[pymongo.uri_parser.parse_uri(settings.CEILOMETER_DSN)['database']]

    # Fetch meters for existed resources
    tsquery = {"$gte": time_start, "$lte": time_end}
    selectors = {
        "_id": 1,
        "project_id": 1,
        "timestamp": 1,
        "counter_name": 1,
    }
    for v in meter_set.get_selectors():
        selectors[v] = 1
    # In MongoDB _id has timestamp at its front so we can sort by this value
    db.meter.ensure_index([("timestamp", 1), ("_id", 1)])
    ceilometer_cursor = db.meter.find({"timestamp": tsquery}, selectors).sort([("timestamp", 1), ("_id", 1)])

    # Try to find terminated resources
    # We are maintaining and using collection called `resource_last_meter` in ceilometer db where
    # we store last recorded meters for each known resource.
    # Resource is treated as terminated if it has no meters recorded for the last
    # USAGE_RESOURCE_MAX_INACTIVITY seconds.
    inactivity_delta = datetime.timedelta(seconds=settings.USAGE_RESOURCE_MAX_INACTIVITY)
    db.resource_last_meter.ensure_index([("timestamp", 1)])
    db.resource_last_meter.ensure_index([("obj_key", 1)], unique=True)
    tsquery = {"$gte": time_start - inactivity_delta, "$lte": time_end - inactivity_delta}

    def inactive_resource_cursor():
        cursor = db.resource_last_meter.find({"timestamp": tsquery})
        for sample in cursor:
            # TODO: recheck that resource is really terminated using some other API e.g. Nova or Cinder
            sample["timestamp"] = time_start
            yield sample

    def record_resource_activity(row, sample):
        if sample.get("event_type") == "end" or not row.get("track_activity"):
            return
        # Prepare meter to be used as "end" sample
        sample.pop("_id")
        sample["obj_key"] = row["obj_key"]
        sample["event_type"] = "end"
        try:
            db.resource_last_meter.update({"obj_key": sample["obj_key"], "timestamp": {"$lt": sample["timestamp"]}}, sample, True)
        except DuplicateKeyError as e:
            pass

    # ATTENTION! We do not use cursor.limit() here, because we do not know it
    # before filtering by billing-related project_id. We MUST return at least
    # one sample row per request, else timestamp will not be moved forward, and
    # the next request will not return anything again. So e.g. if we set
    # limit(10000), and all these 10000 samples are not billing-related,
    # but 10001'th sample IS billing-related, we will never see it. That's
    # why we do not use limit()

    # Build resulting table for as much time as we could.
    fetch_start_time = time.time()
    yielded_count = iteration_no = 0
    chunk = []
    for cursor in [inactive_resource_cursor(), ceilometer_cursor]:
        for sample in cursor:
            iteration_no += 1
            if iteration_no % 1000 == 0 and yielded_count > 0 and time.time() - fetch_start_time > settings.USAGE_API_LIMIT_FETCH_TIME:
                break
            chunk.append(sample)
            if len(chunk) > settings.USAGE_API_CHUNK_SIZE:
                for result_row, sample in _process_samples_chunk(meter_set, chunk):
                    record_resource_activity(result_row, sample)
                    yield result_row
                    yielded_count += 1
                chunk = []
    if len(chunk) > 0:
        for result_row, sample in _process_samples_chunk(meter_set, chunk):
            record_resource_activity(result_row, sample)
            yield result_row

    conn.close()


def _process_samples_chunk(meter_set, samples):
    for sample, processed in meter_set.process_samples(samples):
        row = {
            'id':         sample['_id'],
            'event_type': sample.get("event_type", "exists"),
            'timestamp':  int(time.mktime(sample['timestamp'].timetuple())),
            'tenant_key': None, # filled in abstract.MeterSet.process_samples()
            'obj_class':  None,
            'obj_key':    None,
            'volume':     None,
            'owner_key':  None,
        }
        row.update(processed)
        yield row, sample

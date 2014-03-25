import datetime
import time
import pymongo
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
    time_end = datetime.datetime.fromtimestamp(float(stamp_end)) if stamp_end is not None else None
    meter_set = MeterSet()

    conn = pymongo.mongo_client.MongoClient(settings.CEILOMETER_DSN)
    db = conn[pymongo.uri_parser.parse_uri(settings.CEILOMETER_DSN)['database']]

    # Fetch samples from Mongo.
    tsquery = {}
    if time_start is not None:
        tsquery["$gte"] = time_start
    if time_end is not None:
        tsquery["$lte"] = time_end
    selectors = {
        "_id": 1,
        "project_id": 1,
        "timestamp": 1,
        "counter_name": 1,
    }
    for v in meter_set.get_selectors():
        selectors[v] = 1
    cursor = db.meter.find({"timestamp": tsquery}, selectors)
    db.meter.ensure_index([("timestamp", 1), ("_id", 1)])
    cursor = cursor.sort([("timestamp", 1), ("_id", 1)])  # because _id in mongo has timestamp at its front

    # ATTENTION! We do not use cursor.limit() here, because we do not know it
    # before filtering by RentSoft-related project_id. We MUST return at least
    # one sample row per request, else timestamp will not be moved forward, and
    # the next request will not return anything again. So e.g. if we set
    # limit(10000), and all these 10000 samples are not RentSoft-related,
    # but 10001'th sample IS RentSoft-related, we will never see it. That's
    # why we do not use limit()

    # Build resulting table for as much time as we could.
    time_start = time.time()
    yielded_count = iteration_no = 0
    chunk = []
    for sample in cursor:
        iteration_no += 1
        if iteration_no % 1000 == 0 and yielded_count > 0 and time.time() - time_start > settings.USAGE_API_LIMIT_FETCH_TIME:
            break
        chunk.append(sample)
        if len(chunk) > settings.USAGE_API_CHUNK_SIZE:
            for sample in _process_samples_chunk(meter_set, chunk):
                yield sample
                yielded_count += 1
            chunk = []

    if len(chunk) > 0:
        for sample in _process_samples_chunk(meter_set, chunk):
            yield sample

    conn.close()


def _process_samples_chunk(meter_set, samples):
    for sample, processed in meter_set.process_samples(samples):
        row = {
            'id':         sample['_id'],
            'event_type': "exists",  # TODO
            'timestamp':  int(time.mktime(sample['timestamp'].timetuple())),
            'tenant_key': None, # filled in abstract.MeterSet.process_samples()
            'obj_class':  None,
            'obj_key':    None,
            'volume':     None,
            'owner_key':  None,
        }
        row.update(processed)
        yield row

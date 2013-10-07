from .. import settings
from .. import model
from .. import get_control_panel_module
from . import ceilometer
import urllib
import urllib2
import time
import json
import re

_header = [
    ("id", 24),
    ("tenant_key", 10),
    ("obj_class", 64),
    ("obj_key", 45),
    ("event_type", 10),
    ("timestamp", 10),
    ("volume", 16),
    ("owner_key", 0),
]


def protocol_start():
    return protocol_row(None)


def protocol_row(data):
    if data is None:
        row = map(lambda r: r[0].ljust(r[1]), _header)
    else:
        row = []
        for k, size in _header:
            row.append((str(data[k]) if k in data else "").ljust(size))
    return " ; ".join(row) + "\n"


def protocol_end():
    return ".\n"


def _log(s):
    print s


class Estimator:
    def __init__(self, tenant_key, skip_funds_check):
        self.tenant_key = tenant_key
        self.skip_funds_check = skip_funds_check

    def _send(self, rows):
        events = list()
        events.append(protocol_start())
        for row in rows:
            events.append(protocol_row(row))
        events.append(protocol_end())
        events = "".join(events)
        url = model.billing_get_estimate_url(self.tenant_key)
        data = [
            ('secret', settings.SECRET),
            ('events', events),
            ('skip_funds_check', int(self.skip_funds_check)),
        ]
#        raise Exception(url + "&" + urllib.urlencode(data))
        _log("*** POST %s\n%s" % (url, events.rstrip()))
        try:
            req = urllib2.Request(url, urllib.urlencode(data))
            resp = urllib2.urlopen(req, None, settings.ESTIMATION_TIMEOUT)
            text = resp.read()
            _log("*** Response text:\n%s" % text.rstrip())
            info = json.loads(text)
            if "error" in info and info["error"] is None:
                return info
            error_text = info.get("error", "?").rstrip() + "\n" + info.get("debug", "?").rstrip()
            error_text = re.sub(r'(?m)^', '# ', error_text)
            raise EstimatorException("Estimator returned the following error:\n%s" % error_text)
        except Exception, e:
            _log("*** Response - ERROR:\n%s" % str(e))
            raise

    def estimate_instance(self, flavor_name, image_id, count):
        volume = 1
        try:
            volume = int(count)
        except ValueError:
            pass
        if volume < 1 or volume > settings.ESTIMATION_MAX_SUB_VOLUME:
            volume = 1
        events = list()
        for i in range(0, volume):
            instance_obj_key = model.get_rnd_pass()
            events.append({
                'id':         model.get_rnd_pass(),
                'obj_class':  usage_build_instance_class('instance:' + flavor_name, image_id),
                'obj_key':    instance_obj_key,
                'event_type': "start",
                'timestamp':  int(time.time()),
                'volume':     settings.ESTIMATION_DEFAULT_INSTANCE_VOLUME,
                'owner_key':  '',
                'tenant_key': self.tenant_key,
            })
            events.append({
                'id':         model.get_rnd_pass(),
                'obj_class':  'cpu',
                'obj_key':    model.get_rnd_pass(),
                'event_type': "exists",
                'timestamp':  int(time.time()),
                'volume':     settings.ESTIMATION_DEFAULT_CPU_VOLUME,
                'owner_key':  instance_obj_key,
                'tenant_key': self.tenant_key,
            })
        result = self._send(events)
        return result

    def estimate_volume(self, volume_type, volume_size):
        volume = 1
        try:
            volume = int(volume_size)
        except ValueError:
            pass
        if volume < 1:
            volume = 1
        events = list()
        events.append({
            'id':         model.get_rnd_pass(),
            'obj_class':  volume_type,
            'obj_key':    model.get_rnd_pass(),
            'event_type': "start",
            'timestamp':  int(time.time()),
            'volume':     volume,
            'owner_key':  '',
            'tenant_key': self.tenant_key,
        })
        result = self._send(events)
        return result

    def estimate_ip_floating(self, instance_id):
        events = list()
        events.append({
            'id':         model.get_rnd_pass(),
            'obj_class':  'ip.floating',
            'obj_key':    model.get_rnd_pass(),
            'event_type': "start",
            'timestamp':  int(time.time()),
            'volume':     '1',
            'owner_key':  instance_id,
            'tenant_key': self.tenant_key,
        })
        result = self._send(events)
        return result



class EstimatorException(Exception):
    pass


def usage_fetch(stamp_start, stamp_end):
    # TODO: add more sources in the future.
    return ceilometer.usage_fetch(stamp_start, stamp_end)


def usage_estimate(user, resource, request, skip_funds_check=False):
    tenant_key = user.tenant_name
    cp_module = get_control_panel_module()
    if not hasattr(cp_module, "Estimator"):
        raise Exception("Debug: " + repr(dir(cp_module)) + "\n" + cp_module.__name__)
    estimator = cp_module.Estimator(
        request,
        tenant_key,
        resource,
        skip_funds_check
    )
    est = estimator.get_estimation()
    # Group similar charges saving their counts.
    uniq_charges = dict()
    has_usage_based_charges = False
    for k, charge in est['charges'].items():
        if 'subscription' not in charge:
            has_usage_based_charges = True
        key = str(charge)
        if key not in uniq_charges:
            charge['count'] = 1
            charge['seq'] = int(k)
            uniq_charges[key] = charge
        else:
            uniq_charges[key]['count'] += 1
    est['charges'] = sorted(uniq_charges.values(), key=lambda x: x['seq'])
    est['has_usage_based_charges'] = has_usage_based_charges
    return est


def usage_build_instance_class(flavor_name, image_id):
    return flavor_name + (("+" + "image:" + image_id) if image_id else "")

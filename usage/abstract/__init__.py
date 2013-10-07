import pkgutil
import sys
from .. import model


class Meter:

    selectors = []

    def __init__(self):
        pass

    def matches(self, obj_class, sample):
        raise NotImplementedError()

    def precache_samples(self, samples):
        pass

    def process_sample(self, sample):
        raise NotImplementedError()


class MeterSet:

    def __init__(self, pkg_name):
        self.meters = {}
        self.meters_static = {}
        self.meters_lambda = []
        self.meters_by_obj_class = {}
        self.tenant_key_by_project_id = {}
        # Load all meters.
        pkg = sys.modules[pkg_name]
        for _, name, _ in pkgutil.iter_modules(pkg.__path__):
            name = pkg.__name__ + "." + name
            __import__(name)
            meter = sys.modules[name].Meter()
            if isinstance(meter.matches, str):
                self.meters_static[meter.matches] = meter
            else:
                self.meters_lambda.append(meter)
            self.meters[id(meter)] = meter

    def get_sample_obj_class(self, sample):
        raise NotImplementedError()

    def get_sample_project_id(self, sample):
        raise NotImplementedError()

    def process_samples(self, samples):
        # Collect project_id -> tenant_key mapping.
        self._precache_project_id_mapping(samples)

        # Group samples by meters to call their precache() methods.
        # Also filter samples which belong to wrong projects and have no meters.
        samples_by_meter = {}
        meters_my_sample = {}
        filtered_samples = []
        for sample in samples:
            if self.get_sample_project_id(sample) not in self.tenant_key_by_project_id:
                continue
            meter = self._get_meter_by_sample(sample)
            if meter is None:
                continue
            if id(meter) not in samples_by_meter:
                samples_by_meter[id(meter)] = []
            samples_by_meter[id(meter)].append(sample)
            meters_my_sample[id(sample)] = meter
            filtered_samples.append(sample)

        # Call meter precachers.
        for meter_id, group in samples_by_meter.items():
            self.meters[meter_id].precache_samples(group)

        # Call meter processors and return results.
        for sample in filtered_samples:
            processed = meters_my_sample[id(sample)].process_sample(sample)
            if processed is not None:
                processed['tenant_key'] = self.tenant_key_by_project_id[self.get_sample_project_id(sample)]
                yield sample, processed

    def get_selectors(self):
        selectors = set()
        for meter in self.meters.values():
            selectors.update(meter.selectors)
        return selectors

    def _get_meter_by_sample(self, sample):
        obj_class = self.get_sample_obj_class(sample)
        if obj_class not in self.meters_by_obj_class:
            if obj_class in self.meters_static:
                found_meter = self.meters_static[obj_class]
            else:
                found_meter = None
                for meter in self.meters_lambda:
                    if meter.matches(obj_class, sample):
                        found_meter = meter
                        break
            self.meters_by_obj_class[obj_class] = found_meter
        return self.meters_by_obj_class[obj_class]


    def _precache_project_id_mapping(self, samples):
        not_yet_seen_project_ids = set()
        for sample in samples:
            project_id = self.get_sample_project_id(sample)
            if project_id not in self.tenant_key_by_project_id:
                not_yet_seen_project_ids.add(project_id)
        for tenant in model.tenant_get_by_ids(not_yet_seen_project_ids):
            self.tenant_key_by_project_id[tenant.id] = None  # mark this project_id as seen
            try:
                options = model.tenant_get_options(tenant)
                if "billing_url" not in options:
                    raise ValueError("No billing_url found in description of tenant %s", tenant.name)
                self.tenant_key_by_project_id[tenant.id] = tenant.name
            except ValueError:
                # Skip tenants which have no properly-formatted metadata in description.
                pass

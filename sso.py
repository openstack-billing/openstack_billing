import anydbm
import time
from . import settings
from . import model


class SsoException(Exception):
    pass


def create_mark(user):
    mark_db = _open_db()
    try:
        tenant_key = user.name
        cur_ts = time.time()
        mark = model.get_rnd_pass()
        mark_db[mark] = _mark_assemble(tenant_key=tenant_key, ts=cur_ts)
        for k in mark_db.keys():
            try:
                tmp = _mark_parse(mark_db[k])
                if tmp['ts'] < cur_ts - settings.MARK_STORAGE_LIFETIME:
                    del mark_db[k]
            except KeyError:
                pass
    finally:
        # Close DB to flush the data on disk (sometimes it cannot be read
        # from another process until it is flushed).
        mark_db.close()
    return mark


def get_tenant_key_by_mark(mark):
    mark_db = _open_db()
    try:
        mark = str(mark)  # for anydbm
        parsed = _mark_parse(mark_db[mark])
        if parsed['ts'] < time.time() - settings.MARK_STORAGE_LIFETIME:
            raise SsoException("Authentication mark is expired")
    except KeyError:
        raise SsoException("Unknown or expired authentication mark")
    finally:
        # Close DB to flush the data on disk (sometimes it cannot be read
        # from another process until it is flushed).
        mark_db.close()
    return parsed["tenant_key"]


def _open_db():
    return anydbm.open(settings.MARK_STORAGE_FILE, "c", 0600)


def _mark_assemble(tenant_key, ts):
    return tenant_key + ":" + str(ts)


def _mark_parse(s):
    parts = s.split(":")
    info = {
        "tenant_key": parts[0],
        "ts": float(parts[1]),
    }
    return info

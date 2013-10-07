# Must be overriden in /etc/openstack_billing/local_settings:
SECRET = None
KEYSTONE_AUTH_URL = None
KEYSTONE_ADMIN_PASSWORD = None
TOP_IFRAME_URL = None  # TODO: deduce from billing_url etc.

# May not be overriden:
APP_RELOADER = True
CONTROL_PANEL = "openstack_dashboard"  # TODO: try to deduce
KEYSTONE_ADMIN_USER = "admin"
CEILOMETER_DSN = None
MARK_STORAGE_FILE = "/tmp/openstack_billing_tmp_storage"
MARK_STORAGE_LIFETIME = 60
USAGE_API_LIMIT_FETCH_TIME = 10
USAGE_API_CHUNK_SIZE = 1000
ESTIMATION_TIMEOUT = 10
ESTIMATION_MAX_SUB_VOLUME = 100
ESTIMATION_DEFAULT_CPU_VOLUME = 3600
ESTIMATION_DEFAULT_INSTANCE_VOLUME = 6   # 1 per each 10 minute = 6 per hour

#
# Read defaults from ceilometer.conf.
#
execfile("/etc/openstack_billing/local_settings")

import ConfigParser
ceilometer_config = ConfigParser.ConfigParser()
ceilometer_config.read('/etc/ceilometer/ceilometer.conf')

if CEILOMETER_DSN is None:
    try:
        CEILOMETER_DSN = ceilometer_config.get('database', 'connection')
    except ConfigParser.NoOptionError:
        CEILOMETER_DSN = ceilometer_config.get('DEFAULT', 'database_connection')

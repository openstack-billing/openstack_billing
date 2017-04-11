# Must be overriden in /etc/openstack_billing/local_settings:
SECRET = None
KEYSTONE_AUTH_URL = None
KEYSTONE_ADMIN_PASSWORD = None
KEYSTONE_ADMIN_TENANT_NAME = None
TOP_IFRAME_URL = None  # TODO: deduce from billing_url etc.
CONTROL_PANEL = "openstack_dashboard"  # TODO: try to deduce

# May not be overriden:
APP_RELOADER = True
KEYSTONE_ADMIN_USER = "admin"
CEILOMETER_DSN = None
MARK_STORAGE_FILE = "/tmp/openstack_billing_tmp_storage"
MARK_STORAGE_LIFETIME = 60
USAGE_API_LIMIT_FETCH_TIME = 10
USAGE_API_CHUNK_SIZE = 1000
USAGE_RESOURCE_MAX_INACTIVITY = 60 * 2 + 100  # two ceilometer polls plus minor timeout
ESTIMATION_TIMEOUT = 10
ESTIMATION_MAX_SUB_VOLUME = 100
ESTIMATION_DEFAULT_CPU_VOLUME = 3600
ESTIMATION_DEFAULT_INSTANCE_VOLUME = 6   # 1 per each 10 minutes = 6 per hour
ESTIMATION_VOLUME_VOLUME_MULTIPLIER = 6  # one event with volume-size volume per 10 minutes

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

'''
This is example configuration for Stratum server.
Please rename it to config.py and fill correct values.

This is already setup with sane values for solomining.
You NEED to set the parameters in BASIC SETTINGS
'''

# ******************** BASIC SETTINGS ***************
# These are the MUST BE SET parameters!

CENTRAL_WALLET = 'XiB2rj7PdESyaxJVsnmjhXf9D9bYJjX7ob'  # local dashcoin pubkey or address where money goes

DASHCOIN_TRUSTED_HOST = '192.168.1.124'
DASHCOIN_TRUSTED_PORT = 38990
DASHCOIN_TRUSTED_USER = 'a'
DASHCOIN_TRUSTED_PASSWORD = 'b'

# ******************** BASIC SETTINGS ***************
# Backup Dashcoind connections (consider having at least 1 backup)
# You can have up to 99

# DASHCOIN_TRUSTED_HOST_1 = 'localhost'
# DASHCOIN_TRUSTED_PORT_1 = 8332
# DASHCOIN_TRUSTED_USER_1 = 'user'
# DASHCOIN_TRUSTED_PASSWORD_1 = 'somepassword'

# DASHCOIN_TRUSTED_HOST_2 = 'localhost'
# DASHCOIN_TRUSTED_PORT_2 = 8332
# DASHCOIN_TRUSTED_USER_2 = 'user'
# DASHCOIN_TRUSTED_PASSWORD_2 = 'somepassword'

# ******************** GENERAL SETTINGS ***************

# Enable some verbose debug (logging requests and responses).
DEBUG = False

# Destination for application logs, files rotated once per day.
LOGDIR = 'log/'

# Main application log file.
LOGFILE = 'stratum.log'  # eg. 'stratum.log'

# Possible values: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOGLEVEL = 'DEBUG'

# Logging Rotation can be enabled with the following settings
# It if not enabled here, you can set up logrotate to rotate the files.
# For built in log rotation set LOG_ROTATION = True and configrue the variables
LOG_ROTATION = True
LOG_SIZE = 10485760  # Rotate every 10M
LOG_RETENTION = 10  # Keep 10 Logs
# How many threads use for synchronous methods (services).
# 30 is enough for small installation, for real usage
# it should be slightly more, say 100-300.
THREAD_POOL_SIZE = 300

# Disable the example service
ENABLE_EXAMPLE_SERVICE = False

# ******************** TRANSPORTS *********************

# Hostname or external IP to expose
HOSTNAME = 'localhost'

# Port used for Socket transport. Use 'None' for disabling the transport.
LISTEN_SOCKET_TRANSPORT = 3333
# Port used for HTTP Poll transport. Use 'None' for disabling the transport
LISTEN_HTTP_TRANSPORT = None
# Port used for HTTPS Poll transport
LISTEN_HTTPS_TRANSPORT = None
# Port used for WebSocket transport, 'None' for disabling WS
LISTEN_WS_TRANSPORT = None
# Port used for secure WebSocket, 'None' for disabling WSS
LISTEN_WSS_TRANSPORT = None

# Salt used when hashing passwords
PASSWORD_SALT = 'some_crazy_string'

# ******************** Database  *********************

# MySQL
DB_MYSQL_HOST = 'localhost'
DB_MYSQL_PORT = 3306
DB_MYSQL_DBNAME = 'dashpool'
DB_MYSQL_USER = 'root'
DB_MYSQL_PASS = '123456'

# ******************** Adv. DB Settings *********************
#  Don't change these unless you know what you are doing

DB_LOADER_CHECKTIME = 15  # How often we check to see if we should run the loader
DB_LOADER_REC_MIN = 10  # Min Records before the bulk loader fires
DB_LOADER_REC_MAX = 50  # Max Records the bulk loader will commit at a time

DB_LOADER_FORCE_TIME = 300  # How often the cache should be flushed into the DB regardless of size.

DB_STATS_AVG_TIME = 300  # When using the DATABASE_EXTEND option, average speed over X sec
#	Note: this is also how often it updates
DB_USERCACHE_TIME = 600  # How long the usercache is good for before we refresh

# ******************** Pool Settings *********************

# User Auth Options
USERS_AUTOADD = True  # Automatically add users to db when they connect.
# This basically disables User Auth for the pool.
USERS_CHECK_PASSWORD = False  # Check the workers password? (Many pools don't)

# Transaction Settings
COINBASE_EXTRAS = '/stratumPool/'  # Extra Descriptive String to incorporate in solved blocks
ALLOW_NONLOCAL_WALLET = False  # Allow valid, but NON-Local wallet's

# Dashcoind communication polling settings (In Seconds)
PREVHASH_REFRESH_INTERVAL = 5  # How often to check for new Blocks
#	If using the blocknotify script (recommended) set = to MERKLE_REFRESH_INTERVAL
#	(No reason to poll if we're getting pushed notifications)
MERKLE_REFRESH_INTERVAL = 60  # How often check memorypool
#	This effectively resets the template and incorporates new transactions.
#	This should be "slow"

INSTANCE_ID = 31  # Used for extranonce and needs to be 0-31

# ******************** Pool Difficulty Settings *********************
#  Again, Don't change unless you know what this is for.

# Pool Target (Base Difficulty)
POOL_TARGET = 0.1  # Pool-wide difficulty target int >= 1

# Variable Difficulty Enable
VARIABLE_DIFF = True  # Master variable difficulty enable

# Variable diff tuning variables
# VARDIFF will start at the POOL_TARGET. It can go as low as the VDIFF_MIN and as high as min(VDIFF_MAX or Liteconin's difficulty)
USE_DASHCOIN_DIFF = False  # Set the maximum difficulty to the dashcoin difficulty.
DIFF_UPDATE_FREQUENCY = 86400  # Update the dashcoin difficulty once a day for the VARDIFF maximum
VDIFF_MIN_TARGET = 0.1  # Minimum Target difficulty
VDIFF_MAX_TARGET = 5  # Maximum Target difficulty
VDIFF_TARGET_TIME = 30  # Target time per share (i.e. try to get 1 share per this many seconds)
VDIFF_RETARGET_TIME = 120  # Check to see if we should retarget this often
VDIFF_VARIANCE_PERCENT = 20  # Allow average time to very this % from target without retarget

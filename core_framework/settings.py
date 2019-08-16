import os
import getpass

framework_folder= r'C:\Users\{}\Documents\crawler_framework'.format(getpass.getuser())
database_config = r'{}\db_config.pkl'.format(framework_folder)
ua_data = r'{}\user_agent.pkl'.format(framework_folder)
database_log_folder = r'{}\logs'.format(framework_folder)
tor_config = r'{}\tor_config.pkl'.format(framework_folder)


# ---------------------------------------------------------------------------
# PROXY CARWLER SETTINGS
# ---------------------------------------------------------------------------
# webpage that returns nothing but your ip
ip_checker = "http://codearbiter.pythonanywhere.com/httpx"

# judges are webpages that return request headers to us so we could check proxy anonymity level
judges = {'http': ['http://codearbiter.pythonanywhere.com/', 'http://crodesigner.pythonanywhere.com/',
                   'http://bisn001.pythonanywhere.com/','http://bisn002.pythonanywhere.com/',
                   'http://bisn003.pythonanywhere.com/'],
          'https': ['https://codearbiter.pythonanywhere.com/', 'https://crodesigner.pythonanywhere.com/',
                    'https://bisn001.pythonanywhere.com/','https://bisn002.pythonanywhere.com/',
                    'https://bisn003.pythonanywhere.com/']}

# number of judges that will be used for  analyzing proxy before giving up
# (for example 1st judge give  exception such as ConnecionTimeot or something)
max_judges = 3

# ---------------------------------------------------------------------------
# TOR SETTINGS
# ---------------------------------------------------------------------------
tor_table_name = 'tor_list'
tor_base_url = 'https://www.torproject.org'
tor_url = f'{tor_base_url}/download/tor/'
tor_dir = f'{framework_folder}\Tor'  # default install path
tor_user_path = f'{framework_folder}'
tor_ip_check = 'https://check.torproject.org/'
tor_setup_default = {1: {'number of tor instances': 10}, 2: {'reset identity': 30}, 'tor_path': tor_dir }

tor_settings = r'''# Where data will be stored?
DataDirectory {0}\TorData\data\{1}

# Countdown time before exit
ShutdownWaitLength 5

# Where to write PID
PidFile {0}\TorData\data\{1}\pid

# Communication ports
SocksPort {3}:{1}
ControlPort {3}:{2}

# Authentication of Tor
CookieAuthentication 1

# GeoIP file paths?
GeoIPFile {0}\Data\Tor\geoip
GeoIPv6File {0}\Data\Tor\geoip6

SocksListenAddress {3}
SocksPolicy accept {3}/24
'''

# ---------------------------------------------------------------------------
# DATABASE SETTINGS
# ---------------------------------------------------------------------------
db_types = {'ms': 'Microsoft SQL Server', 'ora': 'Oracle', 'pstg': 'Postgre'}

engine_connection_strings = {'pstg': {'default': 'postgresql://{username}:{password}@{servername}/{databasename}',
                                      'psycopg2': 'postgresql+psycopg2://{username}:{password}@{servername}/{databasename}',
                                      'pg8000': 'postgresql+pg8000://{username}:{password}@{servername}/{databasename}'},

                             'ora': {'default': 'oracle://{username}:{password}@{serverip}:{serverport}/{sidname}',
                                     'cx_oracle': 'oracle+cx_oracle://{username}:{password}@{tnsname}'},

                             'ms': {
                                 'default': 'mssql+pyodbc://{username}:{password}@{dsnname}',
                                 'pymssql': 'mssql+pymssql://{username}:{password}@{serverip}:{serverport}/{databasename}'}
                             }
pstg_req = ['username', 'password', 'servername', 'databasename']

connection_requirements = {'pstg': {'default': pstg_req,
                                    'psycopg2': pstg_req,
                                    'pg8000': pstg_req},

                             'ora': {'default': ['username', 'password', 'serverip', 'serverport', 'sidname'],
                                     'cx_oracle': ['username', 'password', 'tnsname'] },

                             'ms': {
                                 'default': ['username', 'password', 'dsnname'],
                                 'pymssql':  ['username', 'password', 'serverip', 'serverport', 'databasename']}
                             }




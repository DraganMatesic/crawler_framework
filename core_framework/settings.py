import os
import getpass

framework_folder= r'C:\Users\{}\Documents\crawler_framework'.format(getpass.getuser())
database_config = r'{}\db_config.pkl'.format(framework_folder)
ua_data = r'{}\user_agent.pkl'.format(framework_folder)
database_log_folder = r'{}\logs'.format(framework_folder)


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


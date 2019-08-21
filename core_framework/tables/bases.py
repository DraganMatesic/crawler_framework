from sqlalchemy.ext.declarative import declarative_base

BaseMs = declarative_base()
BaseOra = declarative_base()
BasePstg = declarative_base()


tor_table = "tor_list"
proxy_table = "proxy_list"
anonymity_table = 'anonymity_codes'
proxy_distribution_table = 'proxy_dist'
proxy_ban_table = 'proxy_ban'
column_description_table = 'tablecol_descriptor'
proxy_usage_table = 'proxy_usage'
proxy_log_table = 'proxy_log'
proxy_error_log_table = 'proxy_error_log'
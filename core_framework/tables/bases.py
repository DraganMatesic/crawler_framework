from sqlalchemy.ext.declarative import declarative_base

BaseMs = declarative_base()
BaseOra = declarative_base()
BasePstg = declarative_base()

tor_table = "tor_list"
proxy_table = "proxy_list"
column_description_table = 'tablecol_descriptor'
proxy_usage_table = 'proxy_usage'
proxy_log_table = 'proxy_log'
proxy_error_log_table = 'proxy_error_log'
import hashlib
from sqlalchemy import *
from core_framework.tables.bases import *

list_desc = [{"column_name": 'ip', "table_name": proxy_table, "column_description": "proxy ip we are going to use"},
             {"column_name": 'port', "table_name": proxy_table, "column_description": "proxy port that is open for above ip"},
             {"column_name": 'sha', "table_name": proxy_table, "column_description": "hash value of ip and port"},
             {"column_name": 'avg_resp', "table_name": proxy_table, "column_description": "average response rate of proxy"},
             {"column_name": 'protocols', "table_name": proxy_table, "column_description": "protocols that are available are separated by semicolon (http;https;socks5...)"},
             {"column_name": 'proxy_type', "table_name": proxy_table, "column_description": "proxy type can be public, vpn, private, residential, dedicated, shared, data center etc.."},
             {"column_name": 'last_checked', "table_name": proxy_table, "column_description": "date and time when this proxy was checked is it functional and lvl of anonymity"},
             {"column_name": 'anonymity', "table_name": proxy_table, "column_description": "after check is done it will get anonymity rating 0 = elite, 1 = anonymous, 2 = transparent"},
             {"column_name": 'disabled', "table_name": proxy_table, "column_description": "status of proxy server if 0 it is up runing if 1 proxy server is down"},
             {"column_name": 'username', "table_name": proxy_table, "column_description": "username for connection on private proxy/VPN/datacenter"},
             {"column_name": 'password', "table_name": proxy_table, "column_description": "password for connection on private proxy/VPN/datacenter"},
             {"column_name": 'proxy_source', "table_name": proxy_table, "column_description": "name of proxy source can be scraping web page url, shot url to data center like 'zproxy.lum-superproxy.io'"},
             {"column_name": 'date_created', "table_name": proxy_table, "column_description": "date and time when the record was created"},

             {"column_name": 'date_created', "table_name": tor_table, "column_description": "date and time when the record was created"},
             {"column_name": 'pid', "table_name": tor_table, "column_description": "process id on host machine where tor is running"},
             {"column_name": 'ipv4', "table_name": tor_table, "column_description": "ip of machine where tor is deployed"},
             {"column_name": 'ip', "table_name": tor_table, "column_description": "contains public ip of tor that was identified"},
             {"column_name": 'port', "table_name": tor_table, "column_description": "socket port to tor browser"},
             {"column_name": 'control_port', "table_name": tor_table, "column_description": "control port to tor browser"},
             {"column_name": 'torrc_path', "table_name": tor_table, "column_description": "path on host machine where torrc.config can be found"},
             {"column_name": 'pid_file', "table_name": tor_table, "column_description": "path on host machine where pid file can be found"},
             {"column_name": 'data_dir', "table_name": tor_table, "column_description": "path on host machine where tor data file can be found"},
             {"column_name": 'identity_time', "table_name": tor_table, "column_description": "last time identity of tor has been changed"},
             {"column_name": 'date_closed', "table_name": tor_table, "column_description": "date and time from when this tor is not functional"},

             {"column_name": 'anonymity', "table_name": anonymity_table, "column_description": "anonymity rating null, 0, 1, 2"},
             {"column_name": 'description', "table_name": anonymity_table, "column_description": "anonymity description null = bad proxy, 0 = unprocessed, 1 = anonymous/transparent, 2 = elite"},
             {"column_name": 'sha', "table_name": anonymity_table, "column_description": "hash value of ip and port"},

             {"column_name": 'ip', "table_name": proxy_distribution_table, "column_description": "proxy ip or tor ipv4 that is in use"},
             {"column_name": 'port', "table_name": proxy_distribution_table, "column_description": "proxy port or tor socket port that is open for above ip/ipv4"},
             {"column_name": 'sha', "table_name": proxy_distribution_table, "column_description": "hash value of ip and port"},
             {"column_name": 'web_base', "table_name": proxy_distribution_table, "column_description": "base url of some webpage, based on this we control that same proxy is not being used by any other program that crawls same base domain name"},
             {"column_name": 'tic_time', "table_name": proxy_distribution_table, "column_description": "date and time when the program that use this proxy reported that it is still using this proxy. General idea is to free proxy if it is not being used more then 1h"},
             {"column_name": 'date_created', "table_name": proxy_distribution_table, "column_description": "date and time when some proxy has began of being used"},

             {"column_name": 'ip', "table_name": proxy_ban_table, "column_description": "proxy ip or tor ip(not ipv4) that is banned"},
             {"column_name": 'port', "table_name": proxy_ban_table, "column_description": "proxy port or tor port(by default -99 represents tor) that is open for above ip"},
             {"column_name": 'sha', "table_name": proxy_ban_table, "column_description": "hash value of ip and port"},
             {"column_name": 'web_base', "table_name": proxy_ban_table, "column_description": "base url of some webpage where proxy is banned"},
             {"column_name": 'webpage', "table_name": proxy_ban_table, "column_description": "specific webpage where proxy is banned"},
             {"column_name": 'date_created', "table_name": proxy_ban_table, "column_description": "date and time when some proxy has been blocked"},

]


anonymity_desc = [{'anonymity': None, 'description': 'bad proxy'},
                  {'anonymity': 0, 'description': 'unprocessed'},
                  {'anonymity': 1, 'description': 'anonymous/transparent'},
                  {'anonymity': 2, 'description': 'elite'}]



# apply sha- hash value
[row.update({'sha': hashlib.sha3_256(str(row).encode()).hexdigest()}) for row in list_desc]
[row.update({'sha': hashlib.sha3_256(str(row).encode()).hexdigest()}) for row in anonymity_desc]


class TableRowDescriptionsAll:
    __tablename__ = column_description_table

    column_name = Column(String(1000))  # column name
    table_name = Column(String(1000))  # table name
    column_description = Column(String(4000))  # description od column
    sha =  Column(String(64))  # hash value of record


class TableRowDescriptionOra(BaseOra, TableRowDescriptionsAll):
    id = Column('id', Integer, Sequence('tablecol_id_seq'), primary_key=True)


class TableRowDescriptionMS(BaseMs, TableRowDescriptionsAll):
    id = Column('id', Integer, primary_key=True)


class TableRowDescriptionPstg(BasePstg, TableRowDescriptionsAll):
    tablecol_id_seq = Sequence('tablecol_id_seq', metadata=BasePstg.metadata)
    id = Column(
        Integer, tablecol_id_seq,
        server_default=tablecol_id_seq.next_value(), primary_key=True)

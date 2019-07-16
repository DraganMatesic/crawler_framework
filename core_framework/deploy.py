from sqlalchemy import *
from core_framework.sql import *
from sqlalchemy import event, DDL
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from core_framework.db_engine import DbEngine

BaseMs = declarative_base()
BaseOra = declarative_base()
BasePstg = declarative_base()

tor_table = "tor_list"
proxy_table = "proxy_list"
column_description_table = 'tablecol_descriptor'

list_desc = [{"column_name": 'ip', "table_name": proxy_table, "column_description": "proxy ip we are going to use"},
             {"column_name": 'port', "table_name": proxy_table, "column_description": "proxy port that is open for above ip"},
             {"column_name": 'avg_resp', "table_name": proxy_table, "column_description": "average response rate of proxy"},
             {"column_name": 'protocols', "table_name": proxy_table, "column_description": "protocols that are available are separated by semicolon (http;https;socks5...)"},
             {"column_name": 'proxy_type', "table_name": proxy_table, "column_description": "proxy type can be public, vpn, private, residential, dedicated, shared, data center etc.."},
             {"column_name": 'last_checked', "table_name": proxy_table, "column_description": "date and time when this proxy was checked is it functional and lvl of anonymity"},
             {"column_name": 'anonymity', "table_name": proxy_table, "column_description": "after check is done it will get anonymity rating 0 = elite, 1 = anonymous, 2 = transparent"},
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
]


class TableDescriptionsAll:
    __tablename__ = column_description_table

    column_name = Column(String(1000))  # column name
    table_name = Column(String(1000))  # table name
    column_description = Column(String(4000))  # description od column


class TableDescriptionOra(BaseOra, TableDescriptionsAll):
    id = Column('id', Integer, Sequence('tablecol_id_seq'), primary_key=True)


class TableDescriptionMS(BaseMs, TableDescriptionsAll):
    id = Column('id', Integer, primary_key=True)


class TableDescriptionPstg(BasePstg, TableDescriptionsAll):
    tablecol_id_seq = Sequence('tablecol_id_seq', metadata=BasePstg.metadata)
    id = Column(
        Integer, tablecol_id_seq,
        server_default=tablecol_id_seq.next_value(), primary_key=True)


class ProxyListAll:
    __tablename__ = proxy_table
    # __table_args__ = {'extend_existing': True}

    ip = Column(String(64))  # proxy ip we are going to use
    port = Column(Integer)  # proxy port that is open for above ip
    avg_resp = Column(Numeric(18, 2))  # average response rate of  proxy
    protocols = Column(String(1000))  # protocols that are available are separated by semicolon (http;https;socks5...)
    proxy_type = Column(String(1000), server_default='public')  # proxy type can be public, vpn, private, residential, dedicated, shared, data center etc..
    last_checked = Column(DateTime)  # date and time when this proxy was checked is it functional and lvl of anonymity
    anonymity = Column(Integer(), server_default='0')   # after check is done it will get anonymity rating 0 = elite, 1 = anonymous, 2 = transparent
    username = Column(String(1000))  # username for connection on private proxy/VPN
    password = Column(String(1000))  # password for connection on private proxy/VPN
    proxy_source = Column(String(4000))  # name of proxy source can be scraping web page url, shot url to data center like 'zproxy.lum-superproxy.io'
    date_created = Column(DateTime, server_default=func.now())


class ProxyListOra(BaseOra, ProxyListAll):
    id = Column('id', Integer, Sequence('proxy_id_seq'), primary_key=True)


class ProxyListMS(BaseMs, ProxyListAll):
    id = Column('id', Integer, primary_key=True)


class ProxyListPstg(BasePstg, ProxyListAll):
    proxy_id_seq = Sequence('proxy_id_seq', metadata=BasePstg.metadata)
    id = Column(
        Integer, proxy_id_seq,
        server_default=proxy_id_seq.next_value(), primary_key=True)


class TorListAll:
    __tablename__ = tor_table
    # __table_args__ = {'extend_existing': True}

    date_created = Column(DateTime, server_default=func.now())
    pid = Column(Integer)
    ipv4 = Column(String(64))  # ip of machine where tor is deployed
    ip = Column(String(64))  # defines what is public ip of tor
    port = Column(Integer)  # socket port to tor browser
    control_port = Column(Integer)  # control port to tor browser
    torrc_path = Column(String(1000))  # path on host machine where torrc.config can be found
    pid_file = Column(String(1000))  # path on host machine where pid file can be found
    data_dir = Column(String(1000))  # path on host machine where tor data file can be found
    identity_time = Column(DateTime)  # last time identity of tor has been changed
    dat_pro = Column(DateTime)


class TorListOra(BaseOra, TorListAll):
    id = Column('id', Integer, Sequence('tor_id_seq'), primary_key=True)


class TorListMS(BaseMs, TorListAll):
    id = Column('id', Integer, primary_key=True)


class TorListPstg(BasePstg, TorListAll):
    proxy_id_seq = Sequence('tor_id_seq', metadata=BasePstg.metadata)
    id = Column(
        Integer, proxy_id_seq,
        server_default=proxy_id_seq.next_value(), primary_key=True)


class Deploy(DbEngine):
    def __init__(self, conn_id):
        DbEngine.__init__(self)
        self.engine = self.connect(conn_id, echo=False)
        self.start()

    def status(self):
        """return status of deployment 400 = failed, 200= success"""
        if self.engine == 400:
            return 400
        return 200

    def start(self):
        """deploying table structure if it is for first time.
        Don't use this method if you are migrating to another server."""
        if self.engine != 400:

            if self.db_type in ['ora']:
                # prepare triggers
                trigger_sql = DDL(ora_trigger('tr_proxy_list', ProxyListOra.__table__, 'proxy_list_seq'))
                event.listen(ProxyListOra.__table__, 'after_create', trigger_sql)

                trigger_sql = DDL(ora_trigger('tr_tor_list', TorListOra.__table__, 'tor_list_seq'))
                event.listen(TorListOra.__table__, 'after_create', trigger_sql)

                # create tables
                BaseOra.metadata.create_all(self.engine)
            elif self.db_type in ['ms']:
                # creates auto triggers and tables
                BaseMs.metadata.create_all(self.engine)
            elif self.db_type in ['pstg']:
                # creates auto triggers and tables
                BasePstg.metadata.create_all(self.engine)

            # populate initial data
            session = sessionmaker(bind=self.engine)()
            new_rows = []
            session_tables = {'ora': TableDescriptionOra, 'ms': TableDescriptionMS, 'pstg': TableDescriptionPstg}

            for description in list_desc:
                append = True
                new_row = None
                column_name = description.get('column_name')
                table_name = description.get('table_name')
                filter = {'column_name': column_name, 'table_name': table_name}
                session_table = session_tables.get(self.db_type)

                if session_table is not None:
                    existing_row = session.query(session_table).filter_by(**filter).first()
                    column_description = description.get('column_description')
                    if existing_row is None:
                        new_row = session_table(**description)
                    else:
                        session.query(session_table).filter(session_table.id == existing_row.__dict__.get('id')).update({'column_description':column_description})
                        append = False
                    if append and new_row is not None:
                        new_rows.append(new_row)
                if append:
                    new_rows.append(new_row)
            if new_rows:
                session.add_all(new_rows)
            session.commit()


# api = Deploy(3)
from sqlalchemy import *
from core_framework.tables.bases import *


class TorListAll:
    __tablename__ = tor_table

    date_created = Column(DateTime, server_default=func.now())
    pid = Column(Integer)
    ipv4 = Column(String(64))  # ip of machine where tor is deployed
    ip = Column(String(64))  # defines what is public ip of tor
    port = Column(Integer)  # socket port to tor browser
    sha = Column(String(64))  # hash value current tor ip and port(socket port)
    control_port = Column(Integer)  # control port to tor browser
    torrc_path = Column(String(1000))  # path on host machine where torrc.config can be found
    pid_file = Column(String(1000))  # path on host machine where pid file can be found
    data_dir = Column(String(1000))  # path on host machine where tor data file can be found
    identity_time = Column(DateTime)  # last time identity of tor has been changed
    archive = Column(DateTime)  # when the record was closed


class TorListOra(BaseOra, TorListAll):
    id = Column('id', Integer, Sequence('tor_id_seq'), primary_key=True)


class TorListMS(BaseMs, TorListAll):
    id = Column('id', Integer, primary_key=True)


class TorListPstg(BasePstg, TorListAll):
    proxy_id_seq = Sequence('tor_id_seq', metadata=BasePstg.metadata)
    id = Column(
        Integer, proxy_id_seq,
        server_default=proxy_id_seq.next_value(), primary_key=True)
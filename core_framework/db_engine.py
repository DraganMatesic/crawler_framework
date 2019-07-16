import os
import sys
import pickle
from sqlalchemy import create_engine
from core_framework.settings import *


def db_con_list():
    print("\nListing existing connections")
    check_path = os.path.exists(database_config)
    if check_path is True:
        with open(database_config, 'rb') as fr:
            data = pickle.load(fr)
            return data
    else:
        raise FileNotFoundError(f"File does not exist on path: {database_config}")


class DbEngine:
    """Creates instance of sqlalchemy engine connection"""
    def __init__(self):
        self.db_type = None
        self.lib = None

    def connect(self, conn_id, **kwargs):
        connections = db_con_list()
        if connections:
            connection = connections.get('connections').get(conn_id)
            self.db_type = connection.get('db_type')
            self.lib = connection.get('lib')
            string = engine_connection_strings.get(self.db_type).get(self.lib)
            connection_string = string.format(**connection)
            print(connection_string)
            self.engine = create_engine(connection_string, **kwargs)
            try:
                self.engine.connect()
            except Exception as e:
                sys.stdout.write(f"\nCant connect on specified connection. {str(e)}")
                return 400
            return self.engine

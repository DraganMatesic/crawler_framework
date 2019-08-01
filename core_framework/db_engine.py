import os
import sys
import pickle
import logging
import pandas as pd
from time import sleep
from random import randrange
from core_framework.settings import *
# from core import database
import traceback

import sqlalchemy
from sqlalchemy import *
from datetime import datetime
from sqlalchemy.orm import mapper
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.url import URL

datetime_string = datetime.now().strftime('%y%m%d')
file_path = os.path.join(database_log_folder,f'{datetime_string}_log.txt')
log_format = '[{"error_time": "%(asctime)s", "error_level": "%(levelname)s"}, %(message)s]'
logging.basicConfig(filename=file_path, format=log_format,
                    level=logging.ERROR, datefmt='%d-%m-%y %H:%M:%S')


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
    primary_key = 'id'  # default primary key is id
    archive_date = "archive"  # default archive column name

    def __init__(self):
        self.db_type = None
        self.lib = None
        # cache if changes have been made to connection variables
        variables = [i for i in dir(self) if not i.__contains__('__') and type(self.__getattribute__(i)) is str]
        [setattr(self, variable, self.__getattribute__(variable)) for variable in variables]

    def connect(self, conn_id=None, **kwargs):
        connections = db_con_list()

        if conn_id is None:
            # print("conn_id is None searching for db deploy string")
            conn_data = connections.get('connections')
            for k, v in conn_data.items():
                if v.get('deploy') is True:
                    conn_id = k
                    break

        if conn_id is None:
            raise ConnectionError("Program can't find any db deploy string in that case conn_id must be specified")

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
                error_info = traceback.extract_stack(limit=1)[0]
                exc_type, exc_obj, exc_tb = sys.exc_info()
                self.error_logger(error_info.filename, error_info.name, exc_type, exc_tb.tb_lineno, e)
                return 400
            return self.engine

    # Predefined methods that are are used in 99% cases while communicating with db
    @staticmethod
    def lower(table):
        for child in table.get_children():
            child.name = child.name.lower()
            child.key = child.key.lower()

    def and_connstruct(self, table, data):
        filter_data = []
        for attr, value in data.items():
            if value is True:
                and_clause = (and_(getattr(table, attr).isnot(None)))
            elif type(value) is list:
                and_clause = (and_(getattr(table, attr).in_(value)))
            else:
                and_clause = (and_(getattr(table, attr) == value))
            filter_data.append(and_clause)
        return filter_data

    @staticmethod
    def error_logger(filename, method, exc_type, lineno, e):
        error = {"filename": filename, "method": method, "err_type": str(exc_type), 'err_line': str(lineno), 'err_desc': str(e)}
        logging.error(error)

    def select(self, tablename, columns=None, filters=None, sql=None, schema=None, index=False, view=True, freeze=False):
        """
        :param str tablename:
        :param list columns:
        :param dict filters:
        :param str sql:
        :param str schema:
        :param bool index:
        :param bool view:
        Description:
            usage: selects data from specified table in database
            filters: is where clause that will look all as and value of column when set to True = is not Null when set to None = is Null
            columns: final columns to pick
            sql: return results from str query
            schema: if schema is needed to be specified
            index: if index True select will return index data and records
            view: if view is True then mapper needs column name 'id' so it can
                declare it as prmary key - this is only applicable for mssql since
                you cant add primary key in mssql views
            freeze: don't change columns to lower util data is grabed from database
        """
        for tries in range(5):
            try:

                class DbTable(object):
                    pass

                engine = self.engine
                if sql is None:
                    metadata = MetaData(engine)
                    table = Table(tablename, metadata, autoload=True, schema=schema)

                    if freeze is False:
                        self.lower(table)
                    if view is True:
                        try:
                            mapper(DbTable, table, primary_key=[table.c.ID])
                        except:
                            mapper(DbTable, table, primary_key=[table.c.id])
                    else:
                        mapper(DbTable, table)

                    session = sessionmaker(bind=engine)()

                    if filters is not None:
                        if freeze is False:
                            filters = {k.lower(): v for k, v in filters.items()}

                        filter_and, or_groups = [], []
                        if 'or' in filters.keys():
                            or_data = filters.get('or').copy()
                            filters.pop('or')
                            for od in or_data:
                                or_groups.append(and_(*self.and_connstruct(DbTable, od)))
                                pass

                        filter_and = self.and_connstruct(DbTable, filters)
                        results = session.query(DbTable).filter(and_(*filter_and).self_group(), or_(*[or_(g).self_group() for g in or_groups])).statement
                    else:
                        results = session.query(DbTable).statement
                    db_df = pd.read_sql(results, engine, index_col=self.primary_key)

                else:
                    results = sql
                    db_df = pd.read_sql(results, engine)

                db_df.columns = map(str.lower, db_df.columns)

                if columns is not None:
                    columns = [k.lower()for k in columns]
                    db_df = db_df[columns]

                db_df.drop_duplicates(inplace=True)
                if index is False:
                    final_select = db_df.to_dict('records')
                else:
                    final_select = db_df.to_dict()
                return final_select

            except (sqlalchemy.exc.OperationalError, sqlalchemy.exc.ResourceClosedError) as e:
                sys.stdout.write(f"+ reconecting: sqlalchemy connection Error")
                print(traceback.extract_stack())
                error_info = traceback.extract_stack(limit=1)[0]
                exc_type, exc_obj, exc_tb = sys.exc_info()
                self.error_logger(error_info.filename, error_info.name, exc_type, exc_tb.tb_lineno, e)
                sleep(randrange(5, 20))
                self.connect()
                continue
            except Exception as e:
                error_info = traceback.extract_stack(limit=1)[0]
                exc_type, exc_obj, exc_tb = sys.exc_info()
                self.error_logger(error_info.filename, error_info.name, exc_type, exc_tb.tb_lineno, e)
                break

    def insert(self):
        pass

    def delete(self):
        pass

    def merge(self):
        pass

    def proc(self):
        pass


# ================  EXAMPLES:
# api = DbEngine()
# api.connect(0)


# returns data that is NOT NULL in column status
# filters = {'status': True, 'thread': [1,2,3]}

# returns data that IS NULL in column status
# filters = {'status': None}

# returns data that contains values in specified table IN clause
# maximum of 2100 parameters can be in - IN clause
# filters = {'thread': [1,2,3]}

# returns data where column thread contains numbers (1,2,3) or column ime_procesa ¸is equal to HTTPSCrawler
# filters = {'or': [{'thread': [1,2,3]}, {'ime_procesa': 'HTTPSCrawler'}]}

# returns data where column val IS NULL AND ((thread in (1,2,3) and ime_procesa= 'HTTPSCrawler') OR (status is null and rs is null) )
# filters = {'or': [{'thread': [1,2,3], 'ime_procesa': 'HTTPSCrawler'}, {'status': None, 'rs': None}], 'val': None}
# filters = {'or': [{'thread': [1,2,3], 'ime_procesa': 'HTTPSCrawler'}], 'val': None}

# data = api.select('procesi', filters=filters)
# data = api.select('proxy_list')
# print(data)


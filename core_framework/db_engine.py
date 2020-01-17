import os
import sys
import pyodbc
import pickle
import logging
import hashlib
import numpy as np
import pandas as pd
from time import sleep
from random import randrange

from core_framework.settings import *
import traceback

import sqlalchemy
from sqlalchemy import *
from datetime import datetime, timedelta
from sqlalchemy.orm import mapper
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.url import URL


datetime_string = datetime.now().strftime('%y%m%d')
log_path = os.path.join(database_log_folder,f'{datetime_string}_log.txt')

log_format = '[{"error_time": "%(asctime)s", "error_level": "%(levelname)s", "error_line": %(lineno)d}, "module_name": %(pathname)s, %(message)s]'
formatter = logging.Formatter(log_format, datefmt='%d-%m-%y %H:%M:%S')

logger = logging.getLogger('db_log')
logger.setLevel(logging.ERROR)
fh = logging.FileHandler(log_path)
fh.setFormatter(formatter)
fh.setLevel(logging.ERROR)
logger.addHandler(fh)


def db_con_list():
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

    def __init__(self, ):
        self.db_type = None
        self.lib = None
        # cache if changes have been made to connection variables
        variables = [i for i in dir(self) if not i.__contains__('__') and type(self.__getattribute__(i)) is str]
        [setattr(self, variable, self.__getattribute__(variable)) for variable in variables]

    def connect(self, conn_id=None, archive_date='archive', **kwargs):
        connections = db_con_list()

        self.conn_id = conn_id
        self.kwargs = kwargs
        self.archive_date = archive_date

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
            self.engine = create_engine(connection_string, max_identifier_length=128, **kwargs)
            try:
                self.connection = self.engine.connect()
            except Exception as e:
                sys.stdout.write(f"\nCant connect on specified connection. {str(e)}")
                error_info = traceback.extract_stack(limit=1)[0]
                exc_type, exc_obj, exc_tb = sys.exc_info()
                self.error_logger(error_info.filename, error_info.name, exc_type, exc_tb.tb_lineno, e)
                return 400
            return self.engine

    def disconnect(self):
        self.connection.close()

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
            elif type(value) is str:
                if value.startswith(">="):
                    value = value.strip(">=")
                    and_clause = (and_(getattr(table, attr) >= value))
                elif value.startswith("<="):
                    value = value.strip("<=")
                    and_clause = (and_(getattr(table, attr) <= value))
                else:
                    and_clause = (and_(getattr(table, attr) == value))
            else:
                and_clause = (and_(getattr(table, attr) == value))

            filter_data.append(and_clause)
        return filter_data

    @staticmethod
    def error_logger(filename, method, exc_type, lineno, e):
        error = {"filename": filename, "method": method, "err_type": str(exc_type), 'err_line': str(lineno), 'err_desc': str(e)}
        logger.error(error)

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
                    session.commit()
                    session.flush()
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
                self.connect(self.conn_id, **self.kwargs)
                continue

            except Exception as e:
                error_info = traceback.extract_stack(limit=1)[0]
                exc_type, exc_obj, exc_tb = sys.exc_info()
                self.error_logger(error_info.filename, error_info.name, exc_type, exc_tb.tb_lineno, e)
                break

    @staticmethod
    def order_data(data):
        """method converts dataframe row to text and sorts characters alphabetically"""
        data = [str(d) for d in data]
        data = ''.join(sorted(''.join(data).lower()))
        return data

    def merge(self, tablename, data, filters, popkeys=None, schema=None, insert=True, update=True, on=False, delete=False, freeze=False):
        """
        :param str tablename:
        :param dict data:
        :param dict filters:
        :param str schema:
        :param bool insert:
        :param bool update:
        :param list on:
        Description:
            usage: Compartment of web data with current database data.. insert of new and archive of old data.
            data: dictionary where keys are int and values are dictionary that represents single row of data
            filter: dictionary that contains data that will filter database table data that is needed to compare
            schema: if schema is needed to be specified
            insert: if insert is False no data will be inserted
            update: if update is False no data will be updated/closed
            on: what columns it will compare default is all cols
            """

        for tries in range(5):
            try:
                class DbTable(object):
                    pass

                filters = {k.lower(): v for k, v in filters.items()}
                # gathering table information from database based on table name
                # aka reflecting database object
                engine = self.engine
                metadata = MetaData(bind=engine)
                table = Table(tablename, metadata, autoload=True, quote=True, schema=schema)
                self.lower(table)

                # loading gathered table information to sqlalchemy object
                mapper(DbTable, table)
                DbTable.__getattribute__(DbTable, self.primary_key)

                # selecting data from database based on filters
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

                # convert data to pandas object
                db_df = pd.read_sql(results, engine)
                db_df.columns = map(str.lower, db_df.columns)

                # convert dictionary data to pandas data frame object
                web_df = pd.DataFrame.from_dict(data, orient='index')
                web_df = web_df.where((pd.notnull(web_df)), None)
                web_df.replace({np.nan: None}, inplace=True)
                web_df.replace({pd.NaT: None}, inplace=True)

                # change df column names to lower_letters
                web_df.columns = map(str.lower, web_df.columns)

                # calculate sha value and append to df if sha parameter is True
                if not 'sha' in web_df.columns:
                    web_df['sha'] = [hashlib.sha3_256(str(self.order_data(row)).encode()).hexdigest() for row in web_df.values]
                web_columns = list(web_df.columns)

                # +========  COMPARE DATA ========+
                # if there is already existing data in database compare two tables based on their sha has value column
                if db_df.empty is False:
                    # converting all values that are NaT or NaN to None
                    db_df = db_df.where((pd.notnull(db_df)), None)
                    db_df.replace({pd.NaT: None}, inplace=True)
                    db_df.replace({np.nan: None}, inplace=True)

                    # default comparation is done over sha column unless overridden
                    if on is False:
                        on = ['sha']

                    # find all record id's in database frame that does not exist in web frame
                    # +------------ CLOSE ------------+ "
                    close_ids = list()
                    df_all = db_df.merge(web_df.drop_duplicates(), on=on, how='left', indicator=True)
                    close_rows = df_all[df_all['_merge'].isin(['left_only'])]

                    # if there is row ids that need to be closed and update is True append ids
                    if not close_rows.empty and update is True:
                        close_records = close_rows.to_dict('records')
                        for close_record in close_records:
                            rowid = close_record.get(self.primary_key)
                            close_ids.append(rowid)

                    # find all that does not exist in database frame and exist in web frame
                    # +------------  INSERT ------------+ "
                    # if insert is True compare data
                    if insert is True:
                        web_new = web_df.merge(db_df.drop_duplicates(), on=on, how='left', indicator=True, suffixes=('','_y'))

                        # removing pandas calculation columns
                        web_new = web_new[web_new['_merge'].isin(['left_only'])]
                        web_new = web_new[web_columns]
                        web_new = web_new.where((pd.notnull(web_new)), None)
                        web_new.replace({pd.NaT: None}, inplace=True)
                        web_new.replace({np.nan: None}, inplace=True)

                        # if there is new data that doesn't exist in database insert it
                        if web_new.empty is False:
                            insert_data = web_new.to_dict('records')
                            session.bulk_insert_mappings(DbTable, insert_data)

                    # if close id's is not empty
                    if close_ids:
                        if delete is False:
                            session.query(DbTable).filter(DbTable.__getattribute__(DbTable, self.primary_key).in_(close_ids))\
                                .update({self.archive_date: datetime.now()}, synchronize_session='fetch')
                        else:
                            session.query(DbTable).filter(DbTable.__getattribute__(DbTable, self.primary_key).in_(close_ids))\
                                .delete(synchronize_session='fetch')

                # if there is no prexisting data in database then insert without comparing
                elif insert is True:
                    web_df.replace({pd.NaT: None}, inplace=True)
                    web_df.replace({np.nan: None}, inplace=True)
                    insert_data = web_df.to_dict('records')
                    session.bulk_insert_mappings(DbTable, insert_data)

                session.commit()
                session.flush()
                return 200

            except (sqlalchemy.exc.OperationalError, sqlalchemy.exc.ResourceClosedError) as e:
                sys.stdout.write(f"+ reconecting: sqlalchemy connection Error")
                print("extract_stack", traceback.extract_stack())
                error_info = traceback.extract_stack(limit=1)[0]
                exc_type, exc_obj, exc_tb = sys.exc_info()
                self.error_logger(error_info.filename, error_info.name, exc_type, exc_tb.tb_lineno, e)
                sleep(randrange(5, 20))
                # self.connect(connect_args={"application_name": "db_engine/merge/OperationalError"})
                self.connect(self.conn_id, **self.kwargs)
                continue

            except Exception as e:
                print("error in merge", str(e))
                error_info = traceback.extract_stack(limit=1)[0]
                exc_type, exc_obj, exc_tb = sys.exc_info()
                self.error_logger(error_info.filename, error_info.name, exc_type, exc_tb.tb_lineno, e)
                return 400

    def insert(self, tablename, data, primary_key=None, schema=None):
        """
        Method is used for inserting records in specified table
        :param str tablename:
        :param dict data:
        :return:
        """
        insert_data = None
        for tries in range(5):
            try:
                class DbTable(object):
                    pass

                engine = self.engine
                metadata = MetaData(bind=engine)
                table = Table(tablename, metadata, autoload=True, quote=True, schema=schema)
                self.lower(table)

                # loading gathered table information to sqlalchemy object
                mapper(DbTable, table)
                if primary_key is None:
                    DbTable.__getattribute__(DbTable, self.primary_key)
                else:
                    DbTable.__getattribute__(DbTable, primary_key)

                data_df = pd.DataFrame.from_dict(data, orient='index')
                data_df = data_df.where((pd.notnull(data_df)), None)
                # change df column names to lower_letters
                data_df.columns = map(str.lower, data_df.columns)
                data_df.replace({pd.NaT: None}, inplace=True)
                data_df.replace({np.nan: None}, inplace=True)

                # calculate sha value and append to df
                if not 'sha' in data_df.columns:
                    data_df['sha'] = [hashlib.sha3_256(str(self.order_data(row)).encode()).hexdigest() for row in data_df.values]
                insert_data = data_df.to_dict('records')

                session = sessionmaker(bind=engine)()
                session.bulk_insert_mappings(DbTable, insert_data)
                session.commit()
                session.flush()
                return 200

            except (sqlalchemy.exc.OperationalError, sqlalchemy.exc.ResourceClosedError) as e:
                sys.stdout.write(f"+ reconecting: sqlalchemy connection Error")
                print(traceback.extract_stack())
                error_info = traceback.extract_stack(limit=1)[0]
                exc_type, exc_obj, exc_tb = sys.exc_info()
                self.error_logger(error_info.filename, error_info.name, exc_type, exc_tb.tb_lineno, e)
                sleep(randrange(5, 20))
                # self.connect(connect_args={"application_name": "db_engine/insert/OperationalError"})
                self.connect(self.conn_id, **self.kwargs)
                continue

            except Exception as e:
                error_info = traceback.extract_stack(limit=1)[0]
                exc_type, exc_obj, exc_tb = sys.exc_info()
                self.error_logger(error_info.filename, error_info.name, exc_type, exc_tb.tb_lineno, e)
                break

    def delete(self, tablename, filters=None, schema=None):
        """
        deletes records from selected table.
        :param str tablename:
        :param list isin:
        """
        for tries in range(5):
            try:
                class DbTable(object):
                    pass

                # filters = {k.lower(): v for k, v in filters.items()}

                engine = self.engine
                metadata = MetaData(engine)
                table = Table(tablename, metadata, autoload=True, schema=schema)
                mapper(DbTable, table)
                session = sessionmaker(bind=engine)()

                filter_and, or_groups = [], []
                if 'or' in filters.keys():
                    or_data = filters.get('or').copy()
                    filters.pop('or')
                    for od in or_data:
                        or_groups.append(and_(*self.and_connstruct(DbTable, od)))
                        pass

                filter_and = self.and_connstruct(DbTable, filters)
                # for checking statments construct uncoment
                # print(session.query(DbTable).filter(and_(*filter_and).self_group(), or_(*[or_(g).self_group() for g in or_groups])).statement)
                n_rows_deleted = session.query(DbTable).filter(and_(*filter_and).self_group(), or_(*[or_(g).self_group() for g in or_groups])).delete(synchronize_session='fetch')
                session.commit()
                session.flush()
                return 200

            except (sqlalchemy.exc.OperationalError, sqlalchemy.exc.ResourceClosedError) as e:
                sys.stdout.write(f"+ reconecting: sqlalchemy connection Error")
                print(traceback.extract_stack())
                error_info = traceback.extract_stack(limit=1)[0]
                exc_type, exc_obj, exc_tb = sys.exc_info()
                self.error_logger(error_info.filename, error_info.name, exc_type, exc_tb.tb_lineno, e)
                sleep(randrange(5, 20))
                # self.connect(connect_args={"application_name": "db_engine/delete/OperationalError"})
                self.connect(self.conn_id, **self.kwargs)
                continue

            except Exception as e:
                error_info = traceback.extract_stack(limit=1)[0]
                exc_type, exc_obj, exc_tb = sys.exc_info()
                self.error_logger(error_info.filename, error_info.name, exc_type, exc_tb.tb_lineno, e)
                break

    def proc(self, procname, params=None, response=False, one=False):
        """
        calls procedure with return or without
        :param str procname:
        :param params:
        :param bool response:
        :param bool one:

        procname: name of the procedure we are calling
        params: can be dictionary or list or None
        response: return data dat procedure returns
        one: if True returns first record from procedure else retruns all
        """
        for tries in range(5):
            try:
                result = None
                engine = self.engine
                raw_conn = engine.raw_connection()
                cursor = raw_conn.cursor()

                if params is None:
                    params = []

                if type(params) is list or None:
                    cursor.callproc(procname, params)
                elif type(params) is dict:
                    cursor.callproc(procname, keywordParameters=params)
                else:
                    raise TypeError("params must me list, dictionary")

                if response is True:
                    if self.db_type not in ['pstg']:
                        cursor.nextset()
                    if one is True:
                        result = cursor.fetchone()
                    else:
                        result = cursor.fetchall()

                cursor.close()
                raw_conn.commit()
                return result

            except (sqlalchemy.exc.OperationalError, sqlalchemy.exc.ResourceClosedError) as e:
                sys.stdout.write(f"+ reconecting: sqlalchemy connection Error")
                print(traceback.extract_stack())
                error_info = traceback.extract_stack(limit=1)[0]
                exc_type, exc_obj, exc_tb = sys.exc_info()
                self.error_logger(error_info.filename, error_info.name, exc_type, exc_tb.tb_lineno, e)
                sleep(randrange(5, 20))
                # self.connect(connect_args={"application_name": "db_engine/proc/OperationalError"})
                self.connect(self.conn_id, **self.kwargs)
                continue

            except AttributeError as e:
                error_info = traceback.extract_stack(limit=1)[0]
                exc_type, exc_obj, exc_tb = sys.exc_info()
                self.error_logger(error_info.filename, error_info.name, exc_type, exc_tb.tb_lineno, e)
                if str(e) == "'pyodbc.Cursor' object has no attribute 'callproc'":
                    raise NotImplemented("pyodbc does not support callproc create connection string using pymssql")

            except Exception as e:
                error_info = traceback.extract_stack(limit=1)[0]
                exc_type, exc_obj, exc_tb = sys.exc_info()
                self.error_logger(error_info.filename, error_info.name, exc_type, exc_tb.tb_lineno, e)
                break

    def update(self, tablename, filters, values, schema=None, freeze=False, primary_key=None):
        """
        :param str tablename:
        :param dict filters:
        :param dict values2:
        :param str schema:
        :param bool freeze:

        tablename: name of the table we are going to update
        filters: is a dictionary for where clause
        values: dictionary where key is column name and value is value that will be added/updated to
        schema: schema where table is located if it is not in default schema .
        freeze: when we dont want to lower column and table names
        """
        for tries in range(5):
            try:
                class DbTable(object):
                    pass

                if freeze is False:
                    filters = {k.lower(): v for k, v in filters.items()}
                # gathering table information from database based on table name
                # aka reflecting database object
                engine = self.engine
                metadata = MetaData(bind=engine)
                table = Table(tablename, metadata, autoload=True, quote=True, schema=schema)
                if freeze is False:
                    self.lower(table)

                # loading gathered table information to sqlalchemy object
                mapper(DbTable, table)
                if primary_key is None:
                    DbTable.__getattribute__(DbTable, self.primary_key)
                else:
                    DbTable.__getattribute__(DbTable, primary_key)

                where = []
                for k, v in filters.items():
                    col = f"table.c.{k} == '{v}'"
                    where.append(col)

                where = f"and_({','.join(where)})".replace("'None'", 'None')
                where = where.replace("== 'True'", '!= None').replace("== '<=", "<= '").replace("== '>=", ">= '")
                new_values = {}
                for k, v in values.items():
                    if type(v) == pd._libs.tslibs.nattype.NaTType:
                        new_values.update({k: None})
                    if v == np.nan or str(v) == 'nan' or str(v) == 'NaN':
                        new_values.update({k: None})
                if new_values:
                    values.update(new_values)
                statement = table.update().values(values).where(eval(where))
                engine.execute(statement)
                return 200

            except (sqlalchemy.exc.OperationalError, sqlalchemy.exc.ResourceClosedError) as e:
                print(str(e))
                sys.stdout.write(f"+ reconecting: sqlalchemy connection Error")
                print(traceback.extract_stack())
                error_info = traceback.extract_stack(limit=1)[0]
                exc_type, exc_obj, exc_tb = sys.exc_info()
                self.error_logger(error_info.filename, error_info.name, exc_type, exc_tb.tb_lineno, e)
                sleep(randrange(5, 20))
                # self.connect(connect_args={"application_name": "db_engine/update/OperationalError"})
                self.connect(self.conn_id, **self.kwargs)
                continue

            except AttributeError as e:
                error_info = traceback.extract_stack(limit=1)[0]
                exc_type, exc_obj, exc_tb = sys.exc_info()
                self.error_logger(error_info.filename, error_info.name, exc_type, exc_tb.tb_lineno, e)
                if str(e) == "'pyodbc.Cursor' object has no attribute 'callproc'":
                    raise NotImplemented("pyodbc does not support callproc create connection string using pymssql")
                break

            except Exception as e:
                error_info = traceback.extract_stack(limit=1)[0]
                exc_type, exc_obj, exc_tb = sys.exc_info()
                self.error_logger(error_info.filename, error_info.name, exc_type, exc_tb.tb_lineno, e)

    def log_processor(self):
        """When database connection is available this method
         will read all log files that are made in last 5 days
         and insert data into database log table"""
        raise NotImplementedError

    def import_data(self, conn_id, tablename_old, tablename_new):
        """
        imports data from one database to another
        :param int conn_id:
        :param str tablename_old:
        :param str tablename_new:

        conn_id: conn_id of database from where we want to export data
        tablename_old: name of table where data for exporting is
        tablename_new: name of table where exported data will be imported
        """
        raise NotImplementedError


# ================  EXAMPLES:

# ------ SELECT ----------
# api = DbEngine()
# api.connect(0)

# returns data where date is bigger or equal to the desired time
# api.connect()
# now = datetime.today() - timedelta(hours=1)
# filters = {'last_checked': f">={now}", 'anonymity': 2}
# data = api.select('proxy_list', filters=filters)
# print(len(data))


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

# ------ MERGE ----------
# api = DbEngine()
# api.connect(2)
# persons = {0: {'registry_number': '000','pid': '123', 'ime': 'Drаgan', 'prezime': 'Matešić'}, 1: {'registry_number': '000','pid': '345', 'ime': 'Ivan', 'prezime': 'Matešić'},
#            2: {'registry_number': '000','pid': '567', 'ime': 'Marija', 'prezime': 'Matešić'}, 3: {'registry_number': '000','pid': '789','ime': 'Nada', 'prezime': 'Matešić'}}
# api.merge('persons',persons, filters={'archive': None, 'registry_number': '000'})

# api = DbEngine()
# api.connect()
# proxy = {0 : {'ip': '103.106.238.230', 'port': '50941', 'sha': 'a38d4ab1335cc143d1d3ccc46f0be5d5caed63130dc67605e55da15b98773954', 'proxy_source': 'https://www.sslproxies.org/'}}
# api.merge('proxy_list',proxy, filters={'sha': 'a38d4ab1335cc143d1d3ccc46f0be5d5caed63130dc67605e55da15b98773954'}, update=False, sha=False)

# ------ INSERT ----------
# api = DbEngine()
# api.connect(2)
# persons = {0: {'registry_number': '001','pid': '123', 'ime': 'Drаgan', 'prezime': 'Matešić'}, 1: {'registry_number': '001','pid': '345', 'ime': 'Ivan', 'prezime': 'Matešić'}}
# api.insert('persons', persons)

# api = DbEngine()
# api.connect()
# log = {0: {'start_time': datetime.now(), 'webpage': 'https://www.sslproxies.org/', 'proc_id': '90cd4be5e2fc98d44cefbb06703f059dd1dc192fee00b10777f609a2727991e1', 'crawled_urls': 39, 'errors_ratio': 0, 'duration': 2, 'end_time': datetime.now()}}
# api.insert('proxy_log', log)

# ------ DELETE ----------
# api = DbEngine()
# api.connect(2)
# delete filters are same as select filters

# filters = {'sha': ['332f10873dbe4bb6bf67dfe94269e96b77252e8013100902e62fe2e8dd1697b1', "218a20f30cfca471498462d403fd1e8c0d7e16e38902e20b071b109fee893e2a"]}
# filters = {'sha':  ['332f10873dbe4bb6bf67dfe94269e96b77252e8013100902e62fe2e8dd1697b1', "218a20f30cfca471498462d403fd1e8c0d7e16e38902e20b071b109fee893e2a"], 'registry_number': '001'}
# filters = {'sha': None}
# api.delete('persons', filters)

# ------ CALLING PROCEDURE ----------
# api = DbEngine()
# api.connect(3)  # MsSQL
# r = api.proc('apr_list_cnt', response=True, one=True)
# api.connect(2)  # PostGre
# r = api.proc('f_perosn_upd', params=["1acbccf2d79545a0fc0a0ac0b9d11c5971ccd490a8cd5c32e14bec6ec934a497"], response=True, one=True)
# print(r)

# ------ UPDATE ----------
# api = DbEngine()
# api.connect()
# api.update('proxy_list', {'port': '3128'}, {'avg_resp': 10})
# api.update('tor_list' , {'port': 52635, 'archive': None}, {'ip': '23.129.64.163', 'identity_time': datetime.now()})
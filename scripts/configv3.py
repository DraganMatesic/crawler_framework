import os
import re
import sys
import pickle
import getpass
import hashlib
import cx_Oracle
import sqlalchemy
from sys import argv
from time import sleep
from datetime import datetime
from subprocess import Popen, PIPE
from sqlalchemy import create_engine
from distutils.sysconfig import get_python_lib
from core_framework.deploy import Deploy
from core_framework.proxy_server import ProxyServer
from core_framework.tor_network import install as tor_install
from core_framework.proxy_dist import ProxyDist


width = 50
lines = '-' * width
space = " " * round(width / 3.5)
sys.path.insert(0, get_python_lib())

from core_framework.settings import *
from subprocess import Popen, CREATE_NEW_CONSOLE

class DbAttrs:
    username = None
    password = None
    servername = None
    databasename = None
    serverip = None
    serverport = None
    sidname = None
    dsnname = None


class DbConfig:
    pass

        
def create_option_list(options, options_title):
    option_txt = ''
    for k, v in options.items():
        if option_txt == '':
            option_txt += "{}\n[{}] {}".format(options_title, k,v)
        else:
            option_txt += "\n[{}] {}".format(k, v)
    return option_txt


def write_line(print_code=None, txt=None):

    if print_code is not None:
        print_codes = {1: f'''\n+{lines}+\n{space}DATABASE CONFIGURATOR{space}\n+{lines}+\n\n''',
                       2: f"{lines}\nNew db connection form initiated\n{lines}",
                       3: "\nOption must be numeric value. Please try again...\n",
                       4: '> Do you wanna change library that is going to be used by sqlalchemy? [y/n]\n',
                       5: "Answer can be y or n. Try again..\n",
                       6: "That option doesnt exist. Try again..\n",
                       7: f"{lines}\nSetting up string connection arguments\n{lines}\n",
                       8: f"\n+{lines}+\n{space}TOR SETUP{space}\n+{lines}+\n\n"
                       }
        sys.stdout.write(print_codes.get(print_code))
    else:
        sys.stdout.write(txt)
        
        
def input_handler():
    while True:
        option = input()
        if option.isdigit() is False:
            write_line(3)
            continue
        return int(option)


def db_con_list(print_op=True):
    if print_op is True:
        print("\nListing existing connections")
    check_path = os.path.exists(database_config)
    if check_path is True:
        with open(database_config, 'rb') as fr:
            data = pickle.load(fr)
            return data
    else:
        raise FileNotFoundError(f"File does not exist on path: {database_config}")


def create_framework_folders():
    if not os.path.exists(framework_folder):
        os.mkdir(framework_folder)
    if not os.path.exists(database_log_folder):
        os.mkdir(database_log_folder)


def bool_handler():
    while True:
        bool_stat = False
        option = input()
        if option.lower() not in ['y', 'n', 'yes', 'no']:
            write_line(5)
            continue
        if option.lower() in ['y', 'yes']:
            bool_stat = True
        return bool_stat


class Configuration:
    def __init__(self, venv=False):
        self.venv = venv
        create_framework_folders()
        self.commands()

    def bool_handler(self):
        while True:
            bool_stat = False
            option = input()
            if option.lower() not in ['y', 'n', 'yes', 'no']:
                write_line(5)
                continue
            if option.lower() in ['y', 'yes']:
                bool_stat = True
            return bool_stat

    def commands(self):
        while 1:
            master_options ={1: 'Database configuration', 2: 'Deploy framework', 3: 'Run proxy server', 4: 'Tor setup', 5: 'Proxy distributor'}

            master_list = create_option_list(master_options, 'SELECT OPTION:')
            write_line(txt=master_list)
            option = input_handler()

            if option == 1:
                'Database configuration'
                DatabaseConfiguration()

            if option == 2:
                'Deploy framework'
                Deployment()

            if option == 3:
                'Run proxy server'
                proxy_options = {0: 'normal run', 1: 'run without tor', 2: 'run without public proxies', 3: 'only gatherer', 4: 'only tor'}
                proxy_op_list = create_option_list(proxy_options, 'SELECT OPTION:')
                write_line(txt=proxy_op_list)
                suboption = input_handler()

                try:
                    api = ProxyServer()
                    program_location = api.location
                    # getting default interpreter
                    if self.venv is False:
                        py_ver_info = sys.version_info
                        py_version = f"-{py_ver_info[0]}.{py_ver_info[1]}"
                        Popen(['py', py_version, program_location, str(suboption)])
                    else:
                        p = Popen('py -c "import sys; import os; sys.stdout.write(sys.executable)" ', stdout=PIPE)
                        lines = p.stdout.readlines()
                        real_executable = lines[0]
                        if type(real_executable) == bytes:
                            real_executable = real_executable.decode()
                        Popen([real_executable, program_location, str(suboption)])
                    del api
                except Exception as e:
                    print(str(e))

            if option == 4:
                "Tor setup"
                TorSetup()

            if option == 5:
                'Standalone version of proxy distributor'
                check_path = os.path.exists(database_config)
                if check_path is False:
                    sys.stdout.write('create first connection id to the wanted server using config.py')
                    return

                check_path = os.path.exists(proxy_dist)
                if check_path is False:
                    sys.stdout.write('First run - specify connection id where to look for proxy list:')
                    inoption = input_handler()
                    data = {'conn_id': inoption}
                    with open(proxy_dist, 'wb') as fw:
                        pickle.dump(data, fw)
                    sleep(1)

                with open(proxy_dist, 'rb') as fr:
                    data = pickle.load(fr)
                    conn_id = data.get('conn_id')
                    try:
                        api = ProxyDist()
                        program_location = api.location
                        # getting default interpreter
                        if self.venv is False:
                            py_ver_info = sys.version_info
                            py_version = f"-{py_ver_info[0]}.{py_ver_info[1]}"
                            Popen(['py', py_version, program_location, str(conn_id)])
                        else:
                            p = Popen('py -c "import sys; import os; sys.stdout.write(sys.executable)" ', stdout=PIPE)
                            lines = p.stdout.readlines()
                            real_executable = lines[0]
                            if type(real_executable) == bytes:
                                real_executable = real_executable.decode()
                            Popen([real_executable, program_location, str(conn_id)])
                        del api
                    except Exception as e:
                        print(str(e))

            if option not in [3, 5]:
                write_line(txt='Back to main menu? [y/n]')
                exit_a = self.bool_handler()
                if exit_a is False:
                    exit()
            else:
                break


class TorSetup():
    def __init__(self):
        self.commands()

    def commands(self):
        master_options = {1: 'Install', 2: 'Tor options'}
        write_line(8)
        master_list = create_option_list(master_options, 'SELECT OPTION:')
        write_line(txt=master_list)
        option = input_handler()

        if option == 1:
            "install tor with default options"
            tor_install()

        if option == 2:
            "change default options tor with changed parameters"
            current_defaults = ''
            if os.path.isfile(tor_config):
                with open(tor_config, 'rb') as fr:
                    data = pickle.load(fr)
                    for k, v in data.items():
                        if str(k).isdigit() is True:
                            for k1, v1 in v.items():
                                current_defaults += f'\n{k1} = {v1}'
                        else:
                            current_defaults += f'\n{k} = {v}'

            if current_defaults != '':
                print(f"Current defaults {current_defaults}")
                print("----------"*10)

            defaults = tor_setup_default.copy()

            while True:
                setup_info = {0: 'return', 1: 'Number of tor instances (default is 10)', 2: 'Reset identity (default every 30 min)'}
                master_list = create_option_list(setup_info, 'Select parameter to change:')
                write_line(txt=master_list)
                option = input_handler()

                if option == 0:
                    print("returning...")
                    return

                if option not in defaults.keys():
                    write_line(6)
                    continue

                write_line(txt="enter new numerical value:")
                new_val = input_handler()
                get_option = defaults.get(option)

                get_option.update({list(get_option.keys())[0]: new_val})

                write_line(txt="More changes? [y/n]")
                bool_stat = bool_handler()
                if bool_stat is False:
                    print("saving changes")
                    with open(tor_config, 'wb') as fw:
                        pickle.dump(defaults, fw)
                    print("done")
                    break


class DatabaseConfiguration():
    def __init__(self):
        self.commands()

    def delete_db_data(self):
        print("\nDeleting connection file")
        check_path = os.path.exists(database_config)
        if check_path is True:
            os.remove(database_config)
            print("\nDeleted...")
        if check_path is False:
            raise FileNotFoundError(f"File does not exist on path: {database_config}")

    def add_db_conn(self, db_type, username, password, databasename, servername=None, serverip=None, serverport=None,
                    sidname=None, tnsname=None, dsnname=None, lib='default', conn_name=None):
        """
        Description:
            creates new document that will contain all data required for connection strings
            or append to same doc depends on argument append
        :param str db_type: database type ms, ora, pstg
        :param str tnsname: name of the server, used when library is cx_oracle and not default
        :param str dsnname: name of dsn that must me configured in windows it is under odbc data sources
        :param str conn_name: name for the connection if None it will be number
        """
        db_type = db_type.lower()
        arguments = list(locals().keys())

        # check does database type exists
        if db_type not in db_types.keys():
            raise AttributeError(f"db_type (Database type) not recognised supported db types are {db_types.keys()}")

        # check database name type
        if db_type in ['pstg', 'ms'] and type(databasename) is not str:
            if db_type == 'ms' and lib=='default':
                pass
            else:
                raise AttributeError(f"Database can't be {type(databasename)} unless it is ora db_type")

        # check server name for Postgre
        if db_type == 'pstg':
            if servername is None:
                servername = 'localhost'

        # precheck for Oracle database
        if db_type == 'ora':
            if (serverip is None or serverport is None or sidname is None) and tnsname is None:
                raise AttributeError(f"Oracle connection string requires (serverip, serverport, sidname)")

            # if library is cx_oracle is defined and tnsname is not provided it will be made
            if lib.lower() == 'cx_oracle':
                dsn = cx_Oracle.makedsn(serverip, serverport, sid=sidname)
                tnsname = dsn

        # precheck for Micorsoft SQL Server database
        if db_type == 'ms':
            if lib == 'default':
                if dsnname is None:
                    raise AttributeError(f"Microsoft SQL Server connection string requires dsname that can be found in ODBC Data sources. or switch lib to pymssql")
            if lib.lower() == 'pymssql':
                if serverip is None or serverport is None:
                    raise AttributeError(f"Oracle connection string requires (serverip, serverport)")

        check_path = os.path.exists(database_config)
        # create config dict
        for argument in arguments:
            setattr(DbConfig, argument, locals().get(argument))
        config = {k: v for k, v in DbConfig.__dict__.items() if k in arguments and k not in ['self'] and v is not None}

        if check_path is False:
            master_config = {'connections': {}, 'conn_sha': {}}
            if conn_name is None:
                conn_name = 0
            sha = hashlib.sha3_256(str(config).encode()).hexdigest()
            conn_sha = master_config.get('conn_sha')
            if sha not in conn_sha.values():
                config = {conn_name: config}
                conn_sha.update({conn_name: sha})
                connections = master_config.get('connections')
                connections.update(config)

            with open(database_config, 'wb') as fw:
                pickle.dump(master_config, fw)

        else:
            with open(database_config, 'rb') as fr:
                data = pickle.load(fr)
                sha = hashlib.sha3_256(str(config).encode()).hexdigest()
                conn_sha = data.get('conn_sha')
                if sha not in conn_sha.values():
                    connections = data.get('connections')
                    if conn_name is None:
                        connection_id = len(connections)
                        existing_conn_ids = connections.keys()
                        while True:
                            if connection_id in existing_conn_ids:
                                connection_id += 1
                            else:
                                break
                        config = {connection_id: config}
                        conn_sha.update({connection_id: sha})

                    else:
                        config = {conn_name: config}

                    connections.update(config)
                    with open(database_config, 'wb') as fw:
                        pickle.dump(data, fw)
                else:
                    sys.stdout.write("\nThis kind of connection already exist in records. Connection is not appended.")

    def bool_handler(self):
        while True:
            bool_stat = False
            option = input()
            if option.lower() not in ['y', 'n', 'yes', 'no']:
                write_line(5)
                continue
            if option.lower() in ['y', 'yes'] :
                bool_stat = True
            return bool_stat

    @staticmethod
    def basic_args(arg_name, blank=False, edit=False):
        while True:
            if arg_name in ['password']:
                arg_val = getpass.getpass('password:')
            else:
                sys.stdout.write(f"\n{arg_name}:")
                arg_val = input()

            if arg_val.strip() == '' and edit is True:
                return None

            if arg_val.strip() == '' and blank is False:
                if arg_name in ['password']:
                    print(f"{arg_name} cant be blank.  Try again.")
                else:
                    sys.stdout.write(f"{arg_name} cant be blank.  Try again.")
                continue
            if blank is True and arg_name == 'servername':
                if arg_val.strip() == '':
                    arg_val = 'localhost'

            return arg_val

    def test_connection(self, connection_string, data, edit=False):
        try:
            engine = create_engine(connection_string).connect()
        except Exception as e:
            sys.stdout.write(f"\nCant connect with provided data. {str(e)}")
            return 400
        # if engine connection works save connection string
        if edit is False:
            self.add_db_conn(**data)

    def commands(self):
        string = ''
        lib = 'default'
        databasename = None

        login_data = {}
        master_options ={1: 'Add db connection', 2: 'List db connections', 3: 'Edit db connection',
                         4: 'Delete connection', 5: 'Delete db config file'}

        db_conn_type = {1: 'Postgre', 2: 'Microsoft SQL Server', 3: 'Oracle'}
        db_con_alt = {1: 'pstg', 2: 'ms', 3: 'ora'}

        db_libs = {1: {1: 'default', 2: 'pg8000', 3: 'psycopg2'},
                   2: {1: 'default', 2: 'pymssql'},
                   3: {1: 'default', 2: 'cx_oracle'}}

        write_line(1)
        master_list = create_option_list(master_options, 'SELECT OPTION:')
        write_line(txt=master_list)
        option = input_handler()

        if int(option) == 1:
            write_line(2)
            db_list = create_option_list(db_conn_type, '\nDatabase connection type:')
            write_line(txt=db_list)
            db_option = input_handler()

            write_line(4)
            answer = self.bool_handler()
            write_line(txt="\r")

            if answer is True:
                # configuring library that is going to be used for that connection
                lib_option = 1
                load_libs = db_libs.get(db_option)
                db_lib_list = create_option_list(load_libs, '\nLib options:')
                write_line(txt=db_lib_list)
                while True:
                    lib_option = input_handler()
                    if lib_option not in load_libs.keys():
                        write_line(6)
                        continue
                    lib = load_libs.get(lib_option)
                    break

            # loading required fields
            for i in range(5):
                db_alt_name = db_con_alt.get(db_option)
                db_type = db_alt_name
                string = engine_connection_strings.get(db_alt_name).get(lib)
                requirements = connection_requirements.get(db_alt_name).get(lib)

                write_line(7)
                can_be_blank = {1: ['servername']}
                for requirement in requirements:

                    req_blank = can_be_blank.get(db_option)
                    if req_blank is not None:
                        if requirement in req_blank:
                            arg_val = self.basic_args(requirement, blank=True)
                            login_data.update({requirement: arg_val})
                            locals().update({requirement: arg_val})
                            continue

                    arg_val = self.basic_args(requirement)
                    if requirement == 'databasename':
                        databasename = arg_val

                    locals().update({requirement: arg_val})
                    login_data.update({requirement: arg_val})

                login_list = create_option_list(login_data, f'{lines}\nDATA COMFIRMATION:\n{lines}\n')
                write_line(txt=login_list)
                sys.stdout.write("\n> Is data above correct? [y/n]")
                data_check_bool = self.bool_handler()

                if data_check_bool is False:
                    if i == 4:
                        sys.stdout.write("\nMax retries exceeded. Program exiting.")
                        exit()
                    continue
                break

            sys.stdout.write(f'{lines}\nTESTING CONNECTION\n{lines}\n')

            connection_string = string.format(**login_data)
            print(connection_string)
            gathered_data = {k: v for k, v in locals().items() if k in self.add_db_conn.__code__.co_varnames and k != 'self'}
            self.test_connection(connection_string, gathered_data)

        if option == 2:
            connections = db_con_list().get('connections')
            for k, v in connections.items():
                print(k, v)

        if option == 3:
            op_con_list = {}
            connections = db_con_list().get('connections')

            for k, v in connections.items():
                op_con_list.update({len(op_con_list): {k:v}})

            con_list = create_option_list(op_con_list, f'Select connection you want to edit\n{lines}')
            write_line(txt=con_list)
            option = input_handler()
            connection_details = op_con_list.get(option)
            cant_change= ['db_type', 'lib', 'edit_date', 'sha']
            conection_id, db_type, lib = (None,)*3
            sys.stdout.write("\nChange data that is shown. If you dont want to change some argument just hit ENTER key.")
            for i in range(5):
                for k, v in connection_details.items():
                    conection_id = k
                    db_type = v.get('db_type')
                    lib = v.get('lib')
                    can_change = [ink for ink in v.keys() if ink not in cant_change]
                    for change_key in can_change:
                        arg_val = self.basic_args(change_key, edit=True)
                        if arg_val is not None:
                            v.update({change_key: arg_val})

                new_data = connection_details.get(conection_id)
                print(new_data)
                sys.stdout.write("\n> Is data above correct? [y/n]")
                data_check_bool = self.bool_handler()
                if data_check_bool is False:
                    continue
                break

            string = engine_connection_strings.get(db_type).get(lib)
            connection_string = string.format(**new_data)
            test_stat = self.test_connection(connection_string, new_data, edit=True)
            if test_stat != 400:
                not_for_sha = ['edit_date', 'deploy']
                sha_instance = {k:v for k,v in new_data.items() if k not in not_for_sha}
                sha = hashlib.sha3_256(str(sha_instance).encode()).hexdigest()
                new_data.update({"edit_date": datetime.now().strftime("%Y-%m-%d %H:%M:S")})
                with open(database_config, 'rb') as fr:
                    data = pickle.load(fr)
                    sha_new =  data.get('conn_sha')
                    current_sha = sha_new.get(conection_id)
                    if sha != current_sha:
                        connections_new = data.get('connections')
                        connections_new.update({conection_id: new_data})
                        sha_new.update({conection_id: sha})

                        data.update({'connections': connections_new, 'conn_sha': sha_new})

                        with open(database_config, 'wb') as fw:
                            pickle.dump(data, fw)

                    else:
                        sys.stdout.write("\rYou didn't make any changes to existing connection. No changes applied.")

        if option == 4:
            op_con_list = {}
            connections = db_con_list().get('connections')

            for k, v in connections.items():
                op_con_list.update({len(op_con_list): {k:v}})

            con_list = create_option_list(op_con_list, f'Select connection you want to remove\n{lines}')
            write_line(txt=con_list)
            option = input_handler()
            connection_details = op_con_list.get(option)
            conection_id = None
            for k, v in connection_details.items():
                conection_id = k

            with open(database_config, 'rb') as fr:
                data = pickle.load(fr)
                data.get('connections').pop(conection_id)
                data.get('conn_sha').pop(conection_id)

                with open(database_config, 'wb') as fw:
                    pickle.dump(data, fw)

                sys.stdout.write(f"\nConectionid {conection_id} removed successfully.")

        if option == 5:
            self.delete_db_data()


class Deployment:
    """class for deploying crawler framework"""
    def __init__(self):
        """"""
        self.commands()

    def commands(self):
        op_con_list = {}
        data = db_con_list(print_op=False)
        connections_orignal = data.get('connections')

        connections = {k:{x:y for x,y in v.items() if x not in ['password', 'edit_date']} for k, v in connections_orignal.items()}
        for k, v in connections.items():
            op_con_list.update({len(op_con_list): {k: v}})

        conection_id = None
        for k, v in connections_orignal.items():
            print(k, v)
            if v.get('deploy') is True:
                sys.stdout.write(f"\nExisting deploy connection found. Connection id {k}\n")
                conection_id = k
                break

        if conection_id is None:
            sys.stdout.write("\nChoose connection where to deploy framework\n")
            con_list = create_option_list(op_con_list, f'Select connection you want to use\n{lines}')
            write_line(txt=con_list)
            while True:
                option = input_handler()
                if option not in op_con_list.keys():
                    write_line(6)
                    continue
                break
            conection_id = list(op_con_list.get(option).keys())[0]

        deploy_stat = Deploy(conection_id).status()

        if deploy_stat == 400:
            sys.stdout.write(f"\nDeployment failed")
            exit()

        conn = connections_orignal.get(conection_id)
        conn.update({'deploy': True})

        with open(database_config, 'wb') as fw:
            pickle.dump(data, fw)





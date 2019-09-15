import io
import re
import gc
import time
import socket
import pickle
import psutil
import shutil
import zipfile
import hashlib
import requests
import pandas as pd
from time import sleep
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from subprocess import Popen, PIPE
from multiprocessing import Process
from stem.control import Controller
try:
    from core_framework import user_agent
    from core_framework.settings import *
    from core_framework.db_engine import DbEngine
except:
    import user_agent
    from settings import *
    from db_engine import DbEngine

def install(install_path=tor_dir):
    """
    :param str install_path:
    Description:
        install_path = is place where you want Tor to be instaled
            default is in Users\yourusername\Tor
    """
    if os.path.isdir(tor_dir):
        shutil.rmtree(tor_dir)

    print("> acquiring tor expert bundle zip file")
    ses = requests.session()
    ses.headers.update(user_agent.load())
    r = ses.get(tor_url)
    html = r.content

    soup = BeautifulSoup(html, 'lxml')
    tbodies = soup.find_all('tbody')
    tbody = [tbody for tbody in tbodies if tbody.text.__contains__('Contains just Tor and nothing else')]

    dl_link = None
    if tbody:
        a = tbody[0].find('a', {'class': 'downloadLink', 'href': True})
        if a:
            dl_link = a['href']

    if dl_link is None:
        print('Unable to download tor zip package. Try again later.')
        return

    print("> unpacking and installing")
    file = ses.get(dl_link)
    z = zipfile.ZipFile(io.BytesIO(file.content))
    z.extractall(install_path)

    print("> creating additional directories")
    # Deploying additional directories needed for tor_network to work
    for folder in [r'TorData', r'TorData\data', r'TorData\config']:
        os.mkdir(r'{}\{}'.format(tor_dir, folder))

    tor_setup_default.update({'tor_path': install_path})

    with open(tor_config, 'wb') as fw:
        pickle.dump(tor_setup_default, fw)

    print(f"> tor expert bundle installed at {install_path}")


def make_torrc(tor_dir, socket_port, control_port,ipv4):
    """example how torrc file should be constructed"""
    return tor_settings.format(tor_dir, socket_port, control_port, ipv4).replace('        ', "")


def get_ipv4():
    ipv4 = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.connect(("8.8.8.8", 80))
        ipv4 = s.getsockname()[0]
        s.close()
        return ipv4
    except:
        return ipv4


def create_controller(address, control_port):
    tc = TorControl()
    tc.create_controller(address=address, control_port=control_port)
    tc.tor_connect()
    tc.tor_authenticate()
    return tc


def new_id(control_port, address=get_ipv4()):
    tc = create_controller(address=address, control_port=control_port)
    tc.controller.signal('NEWNYM')


def load_defaults():
    # loading tor defaults
    if os.path.isfile(tor_config) is True:
        defaults = dict()
        with open(tor_config, 'rb') as fr:
            data = pickle.load(fr)
            for k, v in data.items():
                if str(k).isdigit() is True:
                    for k1, v1 in v.items():
                        defaults.update({k1: v1})
                else:
                    defaults.update({k: v})
            return defaults
    else:
        raise FileNotFoundError(f"Tor configuration file not found at {tor_config}. "
                                f"Be sure to follow instructions how to install tor:"
                                f"https://github.com/DraganMatesic/crawler_framework")


def check_tor_ip(socket_port, tor_loc_ip=get_ipv4()):
    """
    checks on official tor website what is the node ip address.
    :param int socket_port:
    :param str tor_loc_ip:
    """

    proxies = {
        'http': 'socks5://{0}:{1}'.format(tor_loc_ip, socket_port),
        'https': 'socks5://{0}:{1}'.format(tor_loc_ip, socket_port)}

    ses = requests.session()
    ses.headers.update(user_agent.load())
    r = ses.get(tor_ip_check, proxies=proxies)
    html = r.content

    tor_ip = None
    tor_node = re.search(r'''Your IP address appears to be:\s*<strong>(.*?)</strong>''', html.decode(), re.MULTILINE | re.DOTALL | re.IGNORECASE)
    if tor_node is not None:
        tor_ip = tor_node.group(1).strip()

    return tor_ip


class TorControl(DbEngine):
    """
        Description:
        Class task is to control tor expert programs.
        - Connect python program on it so it can send requests.
        - Change identity(exit node ip) of tor expert if it is needed.
        - Close, Kill or Delete everything for connected tor instance
    """
    socket_port = None
    control_port = None

    def __init__(self):
        DbEngine.__init__(self)
        self.connect()
        self.SocketOriginal = socket.socket
        self.socket_port = self.socket_port
        self.control_port = self.control_port
        self.controller = None

    def create_controller(self, address='127.0.0.1', control_port=None):
        """Creates control instance for a caller"""
        if control_port is None:
            control_port = self.control_port
        self.controller = Controller.from_port(address=address, port=control_port)

    def tor_connect(self):
        """Connects to control instance"""
        self.controller.connect()

    def tor_authenticate(self):
        """Authenticates controller"""
        self.controller.authenticate()

    def tor_reconnect(self):
        """Connects, cleans cache and authenticates"""
        self.controller.reconnect()

    @staticmethod
    def is_tor_up(pid):
        """Checks is the tor expert pid running in processes"""
        for process in psutil.process_iter():
            if process.pid == int(pid) and process.name() == 'tor.exe':
                return True
        return False

    def kill_tor(self, pid, data_dir, torrc_path):
        """
            Kills tor expert pid in running processes.
            Deletes data from data_dir and torrc_path
        """
        for process in psutil.process_iter():
            if process.pid == int(pid) and process.name() == 'tor.exe':
                process.terminate()
        self.clear_data(data_dir, torrc_path)

    def new_id(self, control_port):
        controller = create_controller(address=get_ipv4(), control_port=control_port)
        controller.signal('NEWNYM')

    def new_identity(self, socket_port=None, control_port=9150):
        """Creates new identity(exit node ip) for current tor instance"""
        controller = self.controller
        new_id_status = controller.is_newnym_available()
        new_id_wait_time = controller.get_newnym_wait()
        if new_id_status:
            controller.clear_cache()
            start = time.time()
            process_timeout = 60
            p = Process(target=new_id, args=(control_port,))
            p.start()
            while time.time() - start <= process_timeout:
                if p.is_alive():
                    time.sleep(1)  # Just to avoid hogging the CPU
                else:
                    # All the processes are done, break now.
                    break
            else:
                p.terminate()
                p.join()
            tor_ip = check_tor_ip(socket_port)
            where = {'port': socket_port, 'archive': None}
            values = {'ip': tor_ip, 'identity_time': datetime.now()}
            self.update(tor_table_name, where, values)
        else:
            print("sleeping", new_id_wait_time)
            sleep(new_id_wait_time)

    def clear_socket(self):
        if socket.socket != self.SocketOriginal:
            socket.socket = self.SocketOriginal

    def shutdown_tor(self, data_dir, torrc_path):
        """Shutdowns tor expert and cleans data behind
        Deletes data from data_dir and torrc_path"""
        self.clear_socket()
        self.controller.signal('SHUTDOWN')
        sleep(30)
        self.clear_data(data_dir, torrc_path)

    @staticmethod
    def clear_data(data_dir, torrc_path):
        """Deletes data from data_dir and torrc_path"""
        if os.path.exists(torrc_path):
            os.remove(torrc_path)
        if os.path.isdir(data_dir):
            shutil.rmtree(data_dir, ignore_errors=True)

    def get_pid(self, data_dir):
        pid = None
        pid_file = '{}\pid'.format(data_dir)
        if os.path.exists(pid_file):
            with open(pid_file) as f:
                pid = f.read().strip()
        return pid


def get_free_ports():
    ports = []
    for i in range(2):
        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp.bind(('', 0))
        ports.append(tcp.getsockname()[1])
        tcp.close()
    return ports


class TorBuild(DbEngine):
    """
    Description:
    Class task is to create new instances of tor
    and save that info to the table.
    """

    def __init__(self):
        DbEngine.__init__(self)
        self.defaults = load_defaults()
        self.tormax = self.defaults.get('number of tor instances')
        self.tor_path = self.defaults.get('tor_path')
        self.connect()
        self.tc = TorControl()
        self.tors = {}
        while True:
            tors = self.select(tor_table_name, filters={'ipv4': get_ipv4(), 'archive': None})
            if len(tors) >= self.tormax:
                break
            ports = get_free_ports()
            self.create_tor(*ports)
        self.tc.disconnect()
        del self.tc

    def tor_remove(self, pid, data_dir, torrc_path):
        if pid is not None:
            self.tc.kill_tor(pid, data_dir, torrc_path)
        if pid is None:
            self.tc.clear_data(data_dir, torrc_path)

    def create_tor(self, socket_port, control_port, timeout=60):
        start_time = datetime.now()

        # preparing variables
        tor_exe = r'{0}\Tor\tor.exe'.format(self.tor_path)
        data_dir = r'{0}\TorData\data\{1}'.format(self.tor_path, socket_port)
        torrc_path = r'{0}\TorData\config\torrc{1}.config'.format(self.tor_path, socket_port)

        # create tor expert directory named by socket_port if doesn't exists
        if not os.path.isdir(data_dir):
            os.mkdir(data_dir)

        # create torrc file
        torrc_data = make_torrc(self.tor_path, socket_port, control_port, get_ipv4())
        with open(torrc_path, "w") as f:
            f.write(torrc_data)

        # start instance of tor
        cmd = [tor_exe, '-f', torrc_path]
        self.p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=False)

        while True:
            event = self.p.stdout.readline().strip()
            diff = datetime.now() - start_time
            pid = self.tc.get_pid(data_dir)
            if diff.total_seconds() > timeout:
                self.tor_remove(pid, data_dir, torrc_path)
                err = 'Too long to establish tor circuit over {0} seconds'.format(diff.seconds)
                return 401
            if re.search('Bootstrapped 100%', str(event)):
                tor_ip = check_tor_ip(socket_port)
                pid_file = r'{0}\TorData\data\{1}\pid'.format(self.tor_path, socket_port)
                sha = hashlib.sha3_256(str(str(tor_ip) + str(socket_port)).encode()).hexdigest()
                new_tor = {0: {'pid': pid, 'ipv4': get_ipv4(),
                               'ip': tor_ip, 'port': socket_port, 'sha': sha,
                               'control_port': control_port, 'torrc_path': torrc_path,
                               'pid_file': pid_file, 'data_dir': data_dir}}

                self.insert(tor_table_name, new_tor)
                self.tors.update({control_port: new_tor})
                return 200
            if re.search('No route to host', str(event)):
                self.tor_remove(pid, data_dir, torrc_path)
                return 402


class TorService(DbEngine):
    """
        Description:
        This class task is to run at all times and secure that
        - there is always enough tors running
        - cleaning up tor data that is not longer in use
        - change identity from time to time
    """

    def __init__(self):
        DbEngine.__init__(self)
        self.running_tors = {}
        self.defaults = load_defaults()
        self.tormax = self.defaults.get('number of tor instances')
        self.tor_path = self.defaults.get('tor_path')
        self.reset_time = self.defaults.get('reset identity')
        self.connect()  # connects to database
        self.torrcs, self.bad_tors = {}, []
        self.tors = self.main()
        self.disconnect()

    def scan_torrcs(self):
        torrcs_path = '/'.join([self.tor_path, 'TorData', 'config'])
        gathered_data = {}
        for file in os.listdir(torrcs_path):
            torrc_path = '/'.join([torrcs_path, file])
            torrc_data = {'torrc_path': torrc_path, 'ipv4': get_ipv4()}
            with open(torrc_path) as f:
                rexs = [r'SocksPort\s+(?:\d+\.\d+\.\d+\.\d+:)?(?P<port>\d+)',
                        r'ControlPort\s+(?:\d+\.\d+\.\d+\.\d+:)?(?P<control_port>\d+)',
                        r'PidFile\s+(?P<pid_file>.*?pid)',
                        r'DataDirectory\s+(?P<data_dir>.*?data.\d+)',
                        r'SocksListenAddress\s+(?P<ip>\d+\.\d+\.\d+\.\d+)']
                text = f.read()
                for rex in rexs:
                    x = re.search(rex, text, re.IGNORECASE | re.DOTALL)
                    if x is not None:
                        torrc_data.update(x.groupdict())
            self.torrcs.update({len(self.torrcs): torrc_data})

    def pid_data(self, data):
        pid_file = data.get('pid_file')
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as fr:
                pid = fr.read().strip()
        else:
            return None
        return pid

    def test_torccs(self):
        for k, v in self.torrcs.items():
            tc = TorControl()
            pid, torrc, data_dir = None, v.get('torrc_path'), v.get('data_dir')
            ipv4, control_port = v.get('ipv4'),int(v.get('control_port'))

            delete_data = False
            pid = self.pid_data(v)
            if pid is None:
                self.bad_tors.append((control_port))
                continue

            # check is tor running
            tor_stat = tc.is_tor_up(pid)
            if tor_stat is False:
                "tor is not runing on that pid clean data"
                delete_data = True

            # if delete_data is True than tor is not running and we will delete data
            if delete_data is True:
                tc.clear_data(data_dir, torrc)
                self.bad_tors.append((control_port))

            else:
                # if tor is running we will test can we connect to it
                try:
                    # > create controller
                    tc.create_controller(ipv4, control_port)

                    # > try to connect
                    tc.tor_connect()

                    # > try to tor_authenticate
                    tc.tor_authenticate()

                except Exception as e:
                    "cannot connect to tor"
                    tc.kill_tor(pid, data_dir, torrc)
                    self.bad_tors.append(control_port)
            tc.disconnect()
            del tc
        # delete those from database who failed test
        self.delete(tor_table_name, filters={'control_port': self.bad_tors, 'ipv4': get_ipv4()})

    def main(self, id_change=None):
        if id_change is None:
            id_change = self.defaults.get('reset identity')

        # scan existing torrc files
        self.scan_torrcs()
        # test tor connectivity if failed then remove them from database and from system
        self.test_torccs()
        # clean memory garbage
        gc.collect()

        # get curent tor_list from database
        tor_list = self.select(tor_table_name, filters={'ipv4': get_ipv4()})
        db_df = pd.DataFrame.from_records(tor_list)

        # filter only with defined public ip
        tor_change = dict()
        if db_df.empty is False:
            db_df = db_df[~db_df['ip'].isin(['127.0.0.1'])]

            # get all that dont have changed public ip in last 30 min
            db_df['identity_time'] = pd.DatetimeIndex(db_df['identity_time']) + timedelta(minutes=id_change)
            change_id = db_df[(db_df.identity_time.isnull()) | (db_df['identity_time'] < datetime.now())]

            # change tor identity
            tor_change = {records.get('control_port'): records for records in change_id.to_dict('records')}

        # print(" + changing ip addres for {} tors".format(len(tor_change)))
        for k, v in tor_change.items():
            tc = TorControl
            try:
                tc.control_port = k
                tc.socket_port = v.get('port')
                tc = tc()
                tc.control_port = None
                tc.create_controller(v.get('ipv4'), control_port=k)
                tc.new_identity(v.get('port'), control_port=k)

                tor_ip = check_tor_ip(v.get('port'))
                sha = hashlib.sha3_256(str(str(tor_ip) + str(v.get('port'))).encode()).hexdigest()
                self.update(tor_table_name, {'control_port': k}, {'identity_time': datetime.now(), 'sha': sha})
                tc.disconnect()
                del tc
            except Exception as e:
                "Can't create since there is no control_auth_cookie"
                print(str(e))
                torrc, data_dir = v.get('torrc_path'), v.get('data_dir')
                ipv4, control_port = v.get('ipv4'), int(v.get('control_port'))
                pid = self.pid_data(v)
                if pid is not None:
                    tc.kill_tor(pid, data_dir, torrc)
                self.delete(tor_table_name, filters={'control_port': control_port, 'ipv4': ipv4})
                tc.disconnect()
                del tc

        # add new tors if rquired
        # print("+ Creating new tors if needed")
        start = time.time()
        process_timeout = 180
        p = Process(target=TorBuild)
        p.start()
        while time.time() - start <= process_timeout:
            if p.is_alive():
                time.sleep(1)  # Just to avoid hogging the CPU
            else:
                # All the processes are done, break now.
                break
        else:
            # We only enter this if we didn't 'break' above.
            # print("timed out on creating tor, killing Process")
            p.terminate()
            p.join()

        return self.select(tor_table_name, filters={'archive': None}, columns=['pid', 'ipv4', 'ip', 'port', 'control_port'])

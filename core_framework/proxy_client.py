import socket
import pickle
from abc import ABC
from datetime import datetime, timedelta
from core_framework.db_engine import DbEngine
from core_framework.settings import proxy_path


def load_proxy_server_data():
    with open(proxy_path, 'rb') as fr:
        data = pickle.loads(fr.read())
        proxy_server = data.get("proxy_server")
    return proxy_server


class ProxyClient(DbEngine, ABC):
    def __init__(self, web_base):
        DbEngine.__init__(self)
        self.host, self.port = load_proxy_server_data()
        self.web_base = web_base
        self.last_tic = {}

    def send_request(self, data):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((self.host, self.port))
            sock.sendall(data)
            # Receive data from the server, unpickle it and close connection
            return_data = sock.recv(1024)
            return_data = pickle.loads(return_data)
        finally:
            sock.close()
        return return_data

    def get_proxy(self, proxy_type='public', website=None, protocols=None):
        """
        :param str proxy_type:
        :param str website:
        :param list website:
        proxy_type = public, tor
        """
        data = pickle.dumps({'command': 'get proxy', 'web_base': self.web_base, 'proxy_type': proxy_type, 'website': website, 'protocols': protocols})
        return self.send_request(data)

    def release_proxy(self, sha):
        data2 = pickle.dumps({'command': 'pop proxy', 'sha': sha, 'web_base': self.web_base})
        return self.send_request(data2)

    def bad_proxy(self, sha, proxy_data, web_page=None):
        data3 = pickle.dumps({'command': 'bad proxy', 'sha': sha, 'web_base': self.web_base, 'proxy_data': proxy_data, 'webpage': web_page})
        return self.send_request(data3)

    def tic_time(self, sha, proc_id):
        if proc_id not in list(self.last_tic.keys()):
            self.last_tic.update({proc_id : datetime.now()})

        last_tic = self.last_tic.get(proc_id)
        low_datetime = datetime.now() - timedelta(minutes=2)

        if last_tic <= low_datetime:
            self.connect()
            self.update('proxy_dist', {'web_base': self.web_base, 'sha': sha}, {'tic_time': datetime.now()})
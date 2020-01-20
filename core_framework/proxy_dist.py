# standalone version of proxy distributor so that others users can fetch proxies that are already gathered
import os
import sys
import socket
import pickle
import socketserver
from core_framework.crawlers import *
from core_framework.db_engine import DbEngine
from core_framework.tor_network import get_ipv4
from core_framework.proxy_server import ProxyDistributor


def get_free_port():
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.bind(('', 0))
    port = tcp.getsockname()[1]
    tcp.close()
    return port


def set_free_port():
    data = {'proxy_server': (get_ipv4(), get_free_port())}
    with open(proxy_path, 'wb') as fw:
        pickle.dump(data, fw)


def load_proxy_server_data():
    with open(proxy_path, 'rb') as fr:
        data = pickle.loads(fr.read())
        proxy_server = data.get("proxy_server")
    return proxy_server


class ProxyDist:
    def __init__(self):
        self.location = os.path.realpath(__file__)

    @staticmethod
    def proxy_distributor(argv):
        print("> proxy distributor started")
        set_free_port()
        host, port = load_proxy_server_data()
        if argv[0] == 'config':
            dist_config_name = "proxy_dist_config.pkl"
            crawlers_sm_config_dir = r'C:\Users\{}\Documents\crawler_framework'.format(getpass.getuser())
            storage_path = os.path.join(crawlers_sm_config_dir, dist_config_name)
            if os.path.exists(storage_path) is True:
                with open(storage_path, 'rb') as fr:
                    data = pickle.load(fr)
                    conn_id = data.get('conn_id')
            else:
                raise FileNotFoundError("Use config.py to first run to set db connection id where proxies are")
        else:
            conn_id = int(argv[0])

        print(f"proxy distributor runs at {host}:{port}, db conn_id: {conn_id}")

        engine = DbEngine()
        engine.connect(conn_id=conn_id, connect_args={"application_name": "proxy_server/ProxyDistributor"})

        ProxyDistributor.engine = engine
        server = socketserver.TCPServer((host, port), ProxyDistributor)
        server.serve_forever()


if __name__ == '__main__':
    print('''
+-------------------------------------------------+
|         Proxy Distributor - Standalone          |
+-------------------------------------------------+
    ''')
    if os.path.exists(database_config):
        api = ProxyDist()
        api.proxy_distributor(sys.argv[1:])

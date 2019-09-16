"""Proxy server runs constantly checking existing proxies and adding new ones"""
import pickle
import socket
import requests
from abc import ABC
import pandas as pd
import socketserver
import multiprocessing.pool
import multiprocessing as mp
from subprocess import Popen, PIPE
from datetime import datetime, timedelta
from core_framework.settings import *
from core_framework.crawlers import *
from core_framework.db_engine import DbEngine
from core_framework.tor_network import get_ipv4
from core_framework.tor_network import TorService


# default settings for host and port where proxy server will communicate


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


def db_con_list():
    check_path = os.path.exists(database_config)
    if check_path is True:
        with open(database_config, 'rb') as fr:
            data = pickle.load(fr)
            return data
    else:
        raise FileNotFoundError(f"File does not exist on path: {database_config}")


class NoDaemonProcess(mp.Process):
    def _get_daemon(self):
        return False

    def _set_daemon(self, value):
        pass
    daemon = property(_get_daemon, _set_daemon)


class MyPool(multiprocessing.pool.Pool):
    Process = NoDaemonProcess


class Provider:
    def __init__(self, url, parser, crawler, cookies=None):
        self.url, self.parser, self.crawler = url, parser, crawler


class ProxyDistributor(socketserver.BaseRequestHandler):
    conn_established = False

    def make_connection(self):
        self.proxy_dist = dict()
        self.engine = DbEngine()
        self.engine.connect()

    def handle(self):
        if self.conn_established is False:
            self.make_connection()
        # receive request
        data = self.request.recv(1024).strip()

        # evaluate incoming request
        data_unp = pickle.loads(data)
        command = data_unp.get('command')
        if command == 'get proxy':
            proxy = self.get_proxy(data_unp)
            self.request.sendall(pickle.dumps(proxy))
        elif command == 'pop proxy':
            self.delete_proxy(data_unp)
            self.request.sendall(pickle.dumps('OK'))
        elif command == 'bad proxy':
            self.bad_proxy(data_unp)
            self.request.sendall(pickle.dumps('OK'))
        else:
            error = "there is not such command"
            self.request.sendall(pickle.dumps(error))

    def bad_proxy(self,data_unp):
        sha = data_unp.get('sha')
        web_base = data_unp.get('web_base')
        proxy_data = data_unp.get('proxy_data')
        web_page = data_unp.get('web_page')
        data = {'ip': proxy_data.get('ip'), 'port': proxy_data.get('port'), 'sha': proxy_data.get('sha'), 'web_base': proxy_data.get('web_base') , 'webpage': proxy_data.get('webpage')}
        self.engine.merge('proxy_ban', {0: data}, filters={'sha': sha, 'web_base': web_base, 'webpage': web_page}, on=['sha', 'web_base', 'webpage'], update=False)

    def delete_proxy(self,data_unp):
        sha = data_unp.get('sha')
        web_base = data_unp.get('web_base')
        self.engine.delete('proxy_dist', filters={'sha': sha, 'web_base': web_base})

    def get_proxy(self, data_unp):
        proxy_type = 'public'

        web_base = data_unp.get('web_base')
        website = data_unp.get('website')
        protocol_types = data_unp.get('protocols')

        if protocol_types is None:
            protocol_types = ['https', 'http;https']

        if data_unp.get('proxy_type') is not None:
            proxy_type = data_unp.get('proxy_type')

        proxy = list()
        if proxy_type == 'public':
            proxy = self.engine.select('proxy_list', filters={'anonymity': 2, 'disabled': 0, 'last_checked': True, 'protocols': protocol_types})

        if proxy_type == 'tor':
            proxy = self.engine.select('tor_list', filters={'archive': None})

        # get list of proxies in use for this web base
        proxy_dist = self.engine.select('proxy_dist', filters={'web_base': web_base})
        proxy_dist_sha = [row.get('sha') for row in proxy_dist]

        # get list of proxies banned for this web base and specific website url if is not None
        proxy_ban = self.engine.select('proxy_ban', filters={'web_base': web_base, 'webpage': website})
        proxy_ban_sha = [row.get('sha') for row in proxy_ban]

        # filter out all that are in this other two tables
        proxy = [row for row in proxy if row.get('sha') not in proxy_dist_sha and row.get('sha') not in proxy_ban_sha and row.get('sha')]

        # order data by average response if proxy type is public
        if proxy_type in ['public']:
            data = pd.DataFrame.from_records(proxy).sort_values(by=['avg_resp'])
            proxy = data.to_dict('records')

        if proxy:
            proxy = proxy[0]
            sha = proxy.get('sha')
            proxy.update({'web_base': web_base, 'tic_time': datetime.now(), 'date_created': datetime.now()})
            self.engine.merge('proxy_dist', {0: proxy}, filters={'sha': sha, 'web_base': web_base})

        return proxy


class Providers:
    def classic(self):
        return [
            Provider('http://www.proxylists.net/', ParserType1, ClassicProxy),
            Provider('https://www.sslproxies.org/', ParserType1, ClassicProxy),
            Provider('https://freshfreeproxylist.wordpress.com/', ParserType1, ClassicProxy),
            Provider('http://proxytime.ru/http', ParserType1, ClassicProxy),
            Provider('https://free-proxy-list.net/', ParserType1, ClassicProxy),
            Provider('https://us-proxy.org/', ParserType1, ClassicProxy),
            Provider('https://t.me/s/proxiesfine', ParserType1, ClassicProxy),
            Provider('http://www.httptunnel.ge/ProxyListForFree.aspx', ParserType1, ClassicProxy),
            Provider('http://cn-proxy.com/', ParserType1, ClassicProxy),
            Provider('https://hugeproxies.com/home/', ParserType1, ClassicProxy),
            Provider('http://pubproxy.com/api/proxy?limit=200&format=txt', ParserType1, ClassicProxy),
            # Provider('http://ipaddress.com/proxy-list/', ParserType1, ClassicProxy), #  drukčiji parser ili prilagodba klasičnog
                ]


class ProxyServer(DbEngine, ABC):
    def __init__(self):
        DbEngine.__init__(self)
        self.my_ip = requests.get(ip_checker).content
        self.location = os.path.realpath(__file__)

    @staticmethod
    def providers(data):
        if isinstance(data, Provider):
            start = datetime.now()
            process_id = hashlib.sha3_256(str(start).encode()).hexdigest()
            log = {'start_time': start, 'webpage': data.url, 'proc_id': process_id}

            crawler = data.crawler
            crawler = crawler(data, 5, log=log)

            ips = crawler.start()

            ips_clean = []
            for ip in ips:
                if ip not in ips_clean:
                    ips_clean.append(ip)

            end = datetime.now()
            diff = end - start
            duration = round(diff.total_seconds())

            crawler.log.update({'duration': duration, 'end_time': end})
            return crawler.log, crawler.error_log, data.url, duration, ips_clean

    def gather(self):
        print("> ip gatherer started")
        tick = 12000
        wait_time = 12000
        sql_lastcheck = datetime.now()
        self.connect()
        while True:
            try:
                # check how many proxies that are elite exist in table.. if any from protocols is below 80 and wait time passed at least 20min
                # set flag gather_status to True
                tick += 1
                protocols = ['http', 'https', "http;https"]
                gather_status = False
                # to not overload server with constant select we will check every 5min
                if (datetime.now() - sql_lastcheck).total_seconds() > 300:
                    for protocol in protocols:
                        count = len(self.select('proxy_list', filters={'anonymity': 2, 'protocols': protocol}))
                        if count < 80 and tick > 1200:
                            gather_status = True
                    sql_lastcheck = datetime.now()

                # if gather status is True or more than 12000 sec has passed crawl proxy webpages again
                if gather_status is True or tick > wait_time:
                    tick = 0
                    existing_proxies = [r.get('sha') for r in self.select('proxy_list', columns=['sha'])]

                    providers = Providers()
                    provider_data = providers.classic()
                    pool = mp.Pool(4)
                    crawled_data = pool.map(self.providers, provider_data)
                    pool.close()
                    pool.join()

                    proxy_error_log, proxy_log = dict(), dict()

                    for data in crawled_data:
                        log, error_log, webpage, crawling_time, proxies = data
                        for proxy in proxies:
                            # preparing data for check
                            ip, port = proxy
                            sha = hashlib.sha3_256(str(proxy).encode()).hexdigest()
                            packed = {'ip': ip, 'port': port, 'sha': sha, 'proxy_source': webpage}

                            # skipping any existing proxies that we have in database to speed up process
                            if sha in existing_proxies:
                                continue

                            # check if proxy exists if not then add
                            self.merge('proxy_list', {0: packed}, filters={'sha': sha}, update=False)

                        # preparing logs for insert
                        for errrid, error_data in error_log.items():
                            proc_id = log.get('proc_id')
                            error_data.update({'proc_id': proc_id})
                            proxy_error_log.update({len(proxy_error_log): error_data})
                        proxy_log.update({len(proxy_log): log})

                    # insert results of crawling in logs
                    self.insert('proxy_log', proxy_log)
                    if proxy_error_log :
                        self.insert('proxy_error_log', proxy_error_log)
            except Exception as e:
                print("gather", str(e))
            sleep(1)

    def ip_checker(self):
        print("> ip checker started")
        self.connect()
        while True:
            try:
                # check new proxies and then check old proxies that were last checked 1h ago
                now = datetime.today() - timedelta(hours=1)
                lists = {'new_proxies': {'anonymity': 0}, 'old_proxies': {'last_checked': f"<={now}", 'anonymity': 2}}

                for list_type, filters in lists.items():
                    proxies = self.select('proxy_list', filters=filters, columns=['ip', 'port', 'sha'])
                    proxies = proxies[:100]
                    crawler = CrawlerChecker(proxies, self.my_ip)
                    checked = crawler.start()
                    for row in checked:
                        # sys.stdout.write(f"\r{row}")
                        sha = row.get('sha')
                        bad_proxy = row.get('bad_proxy')
                        avg_resp = row.get('avg_resp')
                        protocols = row.get('protocols')
                        values = {'avg_resp': avg_resp, 'protocols': protocols, 'last_checked': datetime.now()}
                        if bad_proxy is True:
                            if 'noresp_http' in row.keys() and 'noresp_https' in row.keys():
                                values.update({'anonymity': None, 'disabled': 1})
                            else:
                                values.update({'anonymity': 1})
                        if bad_proxy is False:
                            values.update({'anonymity': 2})
                        self.update('proxy_list', {'sha': sha}, values)
            except Exception as e:
                print("ip_checker", str(e))
            sleep(1)

    def tor_service(self):
        print("> tor service started")
        while True:
            ts = TorService()
            reset_time = ts.reset_time
            # print("Listing running tors")
            # for tor in ts.tors:
            #     print(tor)
            ts.disconnect()
            del ts
            wait_time = reset_time*60
            sleep(wait_time)
            # for i in range(wait_time + 1):
            #     sys.stdout.write("\rwait {}/{}".format(i, wait_time))
            #     sleep(1)
            # print("=======" * 10)
            # print("\n")

    @staticmethod
    def proxy_distributor():
        print("> proxy distributor started")
        set_free_port()
        host, port = load_proxy_server_data()
        print(f"proxy distributor runs at {host}:{port}")
        server = socketserver.TCPServer((host, port), ProxyDistributor)
        server.serve_forever()

    def proxy_guard(self, seconds=0, minutes=30, hours=0, days=0):
        print("> proxy guard started")
        # connect to database
        self.connect()
        while True:
            try:
                # Removes all proxies from proxy_dist table that are not being use over specified amount of time.
                datetime_ = datetime.now()-timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
                self.delete('proxy_dist', filters={'tic_time': f"<={datetime_}"})

                # Removes all proxies from proxy_list that are older than 15 days and are disabled.
                datetime2 = datetime.now() - timedelta(days=15)
                self.delete('proxy_list', filters={'date_created': f"<={datetime2}", "disabled": 1, "anonymity": None})

                sleep(60)
            except Exception as e:
                print("proxy_guard", str(e))

    def task_handler(self, task):
        task()

    def run(self, argv):
        try:
            suboption = 0
            if argv:
                suboption = int(argv[0])

            task_sets = {0: [self.gather, self.ip_checker, self.tor_service, self.proxy_distributor, self.proxy_guard],
                         1: [self.gather, self.ip_checker, self.proxy_distributor, self.proxy_guard],
                         2: [self.tor_service, self.proxy_distributor, self.proxy_guard]}

            task_set = task_sets.get(suboption)
            pool = MyPool(5)
            pool.map(self.task_handler, task_set)
            pool.close()
            pool.join()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    print('''
+-----------------------------------+
|           Proxy Server            |
+-----------------------------------+
    ''')
    if os.path.exists(database_config):
        api = ProxyServer()
        # pool = MyPool(5)
        # pool.map(api.task_handler, [api.proxy_distributor])
        # pool.close()
        # pool.join()
        # api.run(None)
        api.run(sys.argv[1:])



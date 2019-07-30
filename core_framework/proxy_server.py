"""Proxy server runs constantly checking existing proxies and adding new ones"""
import pickle
import requests
from time import sleep
from random import shuffle
import multiprocessing.pool
from datetime import datetime
import multiprocessing as mp
from core_framework.settings import *
from core_framework.crawlers import *
from core_framework.db_engine import DbEngine



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


class Providers:
    def classic(self):
        return [
            # Provider('http://www.proxylists.net/', ParserType1, ClassicProxy),
            # Provider('https://www.sslproxies.org/', ParserType1, ClassicProxy),
            # Provider('https://freshfreeproxylist.wordpress.com/', ParserType1, ClassicProxy),
            # Provider('http://proxytime.ru/http', ParserType1, ClassicProxy),
            # Provider('https://free-proxy-list.net/', ParserType1, ClassicProxy),
            # Provider('https://us-proxy.org/', ParserType1, ClassicProxy),
            # Provider('https://t.me/s/proxiesfine', ParserType1, ClassicProxy),
            # Provider('http://www.httptunnel.ge/ProxyListForFree.aspx', ParserType1, ClassicProxy),
            # Provider('http://cn-proxy.com/', ParserType1, ClassicProxy),
            Provider('https://hugeproxies.com/home/', ParserType1, ClassicProxy),
            Provider('http://pubproxy.com/api/proxy?limit=200&format=txt', ParserType1, ClassicProxy),
            # Provider('http://ipaddress.com/proxy-list/', ParserType1, ClassicProxy), #  drukčiji parser ili prilagodba klasičnog
                ]


class ProxyServer:
    def __init__(self):
        self.my_ip = requests.get(ip_checker).content

    @staticmethod
    def providers(data):
        if isinstance(data, Provider):
            crawler = data.crawler
            crawler = crawler(data, 5)

            start = datetime.now()
            ips = crawler.start()

            ips_clean = []
            for ip in ips:
                if ip not in ips_clean:
                    ips_clean.append(ip)

            diff = datetime.now() - start
            return (data.url, round(diff.total_seconds()), ips_clean)

    def gather(self):
        providers = Providers()
        provider_data = providers.classic()
        pool = mp.Pool(2)
        crawled_data = pool.map(self.providers, provider_data)
        pool.close()
        pool.join()

        print("======="*25)
        print("Final data")

        for data in crawled_data:
            webpage, crawling_time, proxies = data
            print(webpage, crawling_time, proxies)

    def pull_db_data(self):
        # get server connection string where framework is deployed
        deploy_db_id = None
        conn_strings= db_con_list().get('connections')
        for id, data in conn_strings.items():
            if 'deploy' in data.keys():
                deploy_db_id = id
        if deploy_db_id is None:
            raise FileExistsError(f"cant find deploy connection string in {database_config}")

    # def ip_checker(self):
    #     while True:
    #         print("priter", 1)
    #         sleep(1)

    def task_handler(self, task):
        task()

    def run(self):
        # self.pull_db_data()
        tasks = [self.gather]
        pool = MyPool(4)
        pool.map(self.task_handler, tasks)
        pool.close()
        pool.join()


if __name__ == '__main__':
    # while True:
        api = ProxyServer()
        api.run()



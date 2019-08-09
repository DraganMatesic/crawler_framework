"""Proxy server runs constantly checking existing proxies and adding new ones"""
import pickle
import hashlib
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


class ProxyServer(DbEngine):
    def __init__(self):
        DbEngine.__init__(self)
        self.my_ip = requests.get(ip_checker).content

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
        self.connect()
        existing_proxies = [r.get('sha') for r in self.select('proxy_list', columns=['sha'])]

        providers = Providers()
        provider_data = providers.classic()
        pool = mp.Pool(4)
        crawled_data = pool.map(self.providers, provider_data)
        pool.close()
        pool.join()

        print("\nFinal data")
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

    # def ip_checker(self):
    #     while True:
    #         print("priter", 1)
    #         sleep(1)

    def task_handler(self, task):
        task()

    def run(self):
        tasks = [self.gather]
        pool = MyPool(4)
        pool.map(self.task_handler, tasks)
        pool.close()
        pool.join()


if __name__ == '__main__':
    # while True:
        api = ProxyServer()
        api.run()



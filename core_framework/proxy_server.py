"""Proxy server runs constantly checking existing proxies and adding new ones"""
import pickle
import hashlib
import requests
from time import sleep
from random import shuffle
import multiprocessing.pool
import multiprocessing as mp
from core_framework.settings import *
from core_framework.crawlers import *
from datetime import datetime,timedelta
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
        tick = 0
        wait_time = 12000
        sql_lastcheck = datetime.now()
        while True:
            try:
                # check how many proxies that are elite exist in table.. if any from protocols is below 80 and wait time passed at least 20min
                # set flag gather_status to True
                tick += 1
                protocols = ['http', 'https', "http;https"]
                gather_status = False
                # to not overload server with constant select we will check every 5min
                if (datetime.now() - sql_lastcheck).total_seconds() > 300:
                    self.connect()
                    for protocol in protocols:
                        count = len(self.select('proxy_list', filters={'anonymity': 2, 'protocols': protocol}))
                        if count < 80 and tick > 1200:
                            gather_status = True
                    sql_lastcheck = datetime.now()

                # if gather status is True or more than 12000 sec has passed crawl proxy webpages again
                if gather_status is True or tick > wait_time:
                    self.connect()
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
                exit()
            sleep(1)

    def ip_checker(self):
        while True:
            try:
                self.connect()
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
                exit()
            sleep(1)

    def task_handler(self, task):
        task()

    def run(self):
        tasks = [self.gather, self.ip_checker]
        pool = MyPool(4)
        pool.map(self.task_handler, tasks)
        pool.close()
        pool.join()


# if __name__ == '__main__':
#     api = ProxyServer()
#     api.run()



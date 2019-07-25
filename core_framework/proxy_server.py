"""Proxy server runs constantly checking existing proxies and adding new ones"""
import requests
from random import shuffle
import multiprocessing as mp
from core_framework.settings import *
from core_framework.crawlers import *
from core_framework.thread_pool import ThreadPool


class Provider:
    def __init__(self, url, parser, crawler):
        self.url, self.parser, self.crawler = url, parser, crawler


class Providers:
    def classic(self):
        return [Provider('http://www.proxylists.net/', ParserType1, CrawlerType1),
                'http://ipaddress.com/proxy-list/',
                'https://www.sslproxies.org/',
                'https://freshfreeproxylist.wordpress.com/',
                'http://proxytime.ru/http',
                'https://free-proxy-list.net/',
                'https://us-proxy.org/',
                'http://fineproxy.org/eng/fresh-proxies/',
                'http://www.httptunnel.ge/ProxyListForFree.aspx',
                'http://cn-proxy.com/',
                'https://hugeproxies.com/home/',
                'http://proxy.rufey.ru/',
                'https://geekelectronics.org/my-servisy/proxy',
                'http://pubproxy.com/api/proxy?limit=20&format=txt'
                ]

class ProxyServer:
    def __init__(self):
        self.my_ip = requests.get(ip_checker).content

    def check_ip(self, data, **kwargs):
        class ProxyStats:
            bad_http = None
            bad_https = None

        ip, port = data
        protocol_list = list()
        thread_number = kwargs.get('Thread')

        ses = requests.session()
        ses.headers.update(user_agent.load())
        ses.proxies = {'http': f'{ip}:{port}', 'https': f'{ip}:{port}'}

        proxy_stats = ProxyStats
        protocol_checks = ['http', 'https']

        for protocol in protocol_checks:
            tries = 0
            protocol_judges = judges.get(protocol)
            shuffle(protocol_judges)
            for judge in protocol_judges:
                try:
                    r = ses.get(judge, timeout=10)
                    html = r.content
                    if re.search(self.my_ip, html, re.MULTILINE | re.DOTALL) is not None:
                        setattr(proxy_stats, f'bad_{protocol}', True)
                    if re.search(self.my_ip, html, re.MULTILINE | re.DOTALL) is None:
                        setattr(proxy_stats, f'bad_{protocol}', False)
                        if protocol not in protocol_list:
                            protocol_list.append(protocol)
                    protocol_stat = getattr(proxy_stats, f'bad_{protocol}')
                    if protocol_stat is False:
                        break
                except Exception as e:
                    tries += 1
                    if tries >= max_judges:
                        break
                    continue

        bad_proxy = None
        bad_http = proxy_stats.bad_http
        bad_https = proxy_stats.bad_https

        if (bad_http is True and bad_https is True) or (bad_http is None and bad_https is None):
            bad_proxy = True
        if bad_http is False or bad_https is False:
            bad_proxy = False

        protocols = ';'.join(protocol_list)
        print(thread_number, "- bad_proxy: ", bad_proxy, data, bad_http, bad_https, protocols)

        # if proxy is bad than we want to record that proxy so we don't check it again

        # if proxy is good we want to safe that proxy so we can check it again later

    def providers(self, data):
        pid = mp.process.current_process().pid
        if isinstance(data, Provider):
            crawler = data.crawler
            crawler = crawler(data, 1)
            ips = crawler.start()

            proxies = list()
            for proxy in ips:
                if proxy not in proxies:
                    proxies.append(proxy)

            # we are using thread pool since requests dont support async and aiohttp
            # still doesn't support https proxies
            t_pool = ThreadPool(20)
            t_pool.map(self.check_ip, ips)
            t_pool.wait_completion()

    def gather(self):
        providers = Providers()
        provider_data = providers.classic()
        pool = mp.Pool(5)
        pool.map(self.providers, provider_data)


# if __name__ == '__main__':
#     api = ProxyServer()
#     api.gather()






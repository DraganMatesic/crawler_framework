import sys
import asyncio
import aiohttp
import logging
import hashlib
from sys import stdout
from time import time, sleep
from random import shuffle
from urllib.parse import *
from lxml import html as lh
from core_framework.parsers import *
from core_framework import user_agent
from core_framework.settings import *





class ClassicProxy:
    name = 'ClassicProxy'

    def __init__(self, provider_data, depth, max_conn=200, log=None):
        self.log = log
        self.crawled_urls = 1
        self.iterations = 1
        self.error_log = {}
        self.error_count = 0

        self.parser_class = provider_data.parser
        self.start_url = provider_data.url
        self.base_url = '{}://{}'.format(urlparse(self.start_url).scheme, urlparse(self.start_url).netloc)
        self.url_depth = depth
        self.parsed_urls = set()
        self.headers = user_agent.load()
        self.conn_limiter = asyncio.BoundedSemaphore(max_conn)
        self.session = aiohttp.ClientSession(headers=self.headers)

    def error_desc_eval(self, e):
        if type(e) is not None:
            e = str(e)
        if e == '':
            e = None
        return e

    def error_handler(self, errorid, error):
        if errorid not in self.error_log.keys():
            error.update({'err_cnt': 0})
            self.error_log.update({errorid: error})
        else:
            error_id_data = self.error_log.get(errorid)
            error_n = error_id_data.get('err_cnt')
            error_id_data.update({'err_cnt': error_n+1})
        self.error_count += 1
        self.log.update({'errors': self.error_count})

    def start(self):
        future = asyncio.Task(self.crawl())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(future)
        result = future.result()
        return result

    async def crawl(self):
        urls = [self.start_url]
        all_proxies = list()
        for depth in range(self.url_depth + 1):
            data = await self.gather_urls(urls)
            urls.clear()
            for url, data, found_urls in data:
                self.crawled_urls += 1
                parser = self.parser_class()
                proxies = parser.find_ips(data)
                proxies = [proxy for proxy in proxies if proxy not in all_proxies]
                all_proxies.extend(proxies)
                # add new found urls with base name
                urls.extend(found_urls)

        # final loging stuff
        error_ratio = round((self.error_count/self.crawled_urls) * 100)

        self.log.update({'crawled_urls': self.crawled_urls, 'errors_ratio': error_ratio})
        await self.session.close()
        return all_proxies

    async def gather_urls(self, urls):
        method_name = 'gather_urls'
        futures, results = list(), list()
        for url in urls:
            if url in self.parsed_urls:
                continue
            self.parsed_urls.add(url)
            futures.append(self.request_async(url))

        for future in asyncio.as_completed(futures):
            try:
                results.append((await future))
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                error = {'program': self.name, 'method': method_name, 'err_type': str(exc_type), 'err_line': exc_tb.tb_lineno, 'err_desc':  self.error_desc_eval(e)}
                error_id = hashlib.sha3_256(str(error).encode()).hexdigest()
                error.update({'error_id': error_id})
                self.error_handler(error_id, error)

        return results

    async def request_async(self, url):
        """Makes async requests to extract data urls and their htmls"""
        data = await self.http_request(url)
        found_urls = set()
        if data:
            for url in self.extract_urls(data):
                found_urls.add(url)
        return url, data, sorted(found_urls)

    async def http_request(self, url):
        """Makes request on desired page and returns html result"""
        method_name = 'http_request'
        stdout.write(f'\rtotal_urls for {self.start_url}: {len(self.parsed_urls)}')
        self.crawled_urls += 1
        async with self.conn_limiter:
            try:
                async with self.session.get(url, timeout=60) as response:
                    html = await response.read()
                    return html
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                error = {'program': self.name, 'method': method_name, 'err_type': str(exc_type), 'err_line': exc_tb.tb_lineno, 'err_desc': self.error_desc_eval(e), 'url': url}
                error_id = hashlib.sha3_256(str(error).encode()).hexdigest()
                error.update({'error_id': error_id})
                self.error_handler(error_id, error)

    def extract_urls(self, html):
        """Parses html doc to gather other urls with same base_url as the webpage"""
        found_urls = []
        dom = lh.fromstring(html)
        for href in dom.xpath('//a/@href'):
            url = urljoin(self.base_url, href)
            if url not in self.parsed_urls and url.startswith(self.base_url):
                found_urls.append(url)
        return found_urls


class CrawlerChecker:
    name = 'CrawlerChecker'

    def __init__(self, proxy_list, my_ip):
        self.checked_proxies = []
        self.all_proxies = proxy_list
        self.my_ip = my_ip

    async def check_ip(self):
        futures, results = list(), list()

        for proxy in self.all_proxies:
            sha = proxy.get('sha')
            if proxy in self.checked_proxies:
                continue
            futures.append(self.proxy_async(proxy))
            self.checked_proxies.append(sha)

        for future in asyncio.as_completed(futures):
            try:
                results.append((await future))
            except Exception as e:
                logging.warning('Exception in CrawlerType1.check_ip: {}'.format(e))

        return results

    async def proxy_async(self, proxy):

        class ProxyStats:
            bad_http = None
            bad_https = None

        ip, port, sha = proxy.get('ip'), proxy.get('port'), proxy.get('sha')

        protocol_list = list()

        proxy_stats = ProxyStats
        protocol_checks = ['http', 'https']

        for protocol in protocol_checks:
            tries = 0
            protocol_judges = judges.get(protocol)
            shuffle(protocol_judges)
            for judge in protocol_judges:
                html = await self.proxy_request(judge, proxy=f'http://{ip}:{port}')
                if html == 400:
                    tries += 1
                    if tries >= max_judges:
                        setattr(proxy_stats, f'bad_{protocol}', True)
                        break
                    continue

                if re.search(self.my_ip, html, re.MULTILINE | re.DOTALL) is not None:
                    setattr(proxy_stats, f'bad_{protocol}', True)
                    break
                if re.search(self.my_ip, html, re.MULTILINE | re.DOTALL) is None:
                    setattr(proxy_stats, f'bad_{protocol}', False)
                    if protocol not in protocol_list:
                        protocol_list.append(protocol)
                protocol_stat = getattr(proxy_stats, f'bad_{protocol}')
                if protocol_stat is False:
                    break

        bad_proxy = None
        bad_http = proxy_stats.bad_http
        bad_https = proxy_stats.bad_https

        if (bad_http is True and bad_https is True) or (bad_http is None and bad_https is None):
            bad_proxy = True
        if bad_http is False or bad_https is False:
            bad_proxy = False

        protocols = None
        if protocol_list:
            protocols = ';'.join(protocol_list)

        result = {'sha': sha, 'bad_proxy': bad_proxy, 'bad_http': bad_http, 'bad_https': bad_https, 'protocols': protocols}
        self.checked_proxies.append(sha)
        return result

    async def proxy_request(self, url, proxy):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, proxy=proxy, timeout=10) as response:
                    html = await response.read()
                    return html
        except Exception as e:
            # print("ERROR",proxy, str(e))
            return 400

    def start(self):
        future = asyncio.Task(self.check_ip())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(future)
        result = future.result()
        return result
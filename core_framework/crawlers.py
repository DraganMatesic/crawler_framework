import sys
import asyncio
import aiohttp
import logging
import hashlib
from sys import stdout
from urllib.parse import *
from lxml import html as lh
from core_framework.parsers import *
from core_framework import user_agent


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

    # ============= GATHER PROXIES ===================
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
                error = {'program': self.name, 'method': method_name, 'err_type': str(exc_type), 'err_line': exc_tb.tb_lineno, 'err_desc':  str(e)}
                error_id = hashlib.sha3_256(str(error).encode()).hexdigest()
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
                error = {'program': self.name, 'method': method_name, 'err_type': str(exc_type), 'err_line': exc_tb.tb_lineno, 'err_desc': str(e)}
                error_id = hashlib.sha3_256(str(error).encode()).hexdigest()
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
import asyncio
import aiohttp
import logging
from sys import stdout
from urllib.parse import *
from lxml import html as lh
from core_framework.parsers import *
from core_framework import user_agent


class CrawlerType1:

    def __init__(self, provider_data, depth, max_conn=200):
        self.parser_class = provider_data.parser
        self.start_url = provider_data.url
        self.base_url = '{}://{}'.format(urlparse(self.start_url).scheme, urlparse(self.start_url).netloc)
        self.url_depth = depth
        self.parsed_urls = set()
        self.headers = user_agent.load()
        self.conn_limiter = asyncio.BoundedSemaphore(max_conn)
        self.session = aiohttp.ClientSession(headers=self.headers)

    def start(self):
        future = asyncio.Task(self.crawl())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(future)
        loop.close()
        result = future.result()
        return result

    async def crawl(self):
        urls = [self.start_url]
        all_proxies = list()
        for depth in range(self.url_depth + 1):
            data = await self.gather_urls(urls)
            urls.clear()
            for url, data, found_urls in data:
                parser = self.parser_class()
                proxies = parser.find_ips(data)
                proxies = [proxy for proxy in proxies if proxy not in all_proxies]
                all_proxies.extend(proxies)
                urls.extend(found_urls)

        await self.session.close()
        return all_proxies

    async def gather_urls(self, urls):
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
                logging.warning('Exception in CrawlerType1.gather_urls: {}'.format(e))
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
        stdout.write(f'\rtotal_urls for {self.start_url}: {len(self.parsed_urls)}')
        async with self.conn_limiter:
            try:
                async with self.session.get(url, timeout=30) as response:
                    html = await response.read()
                    return html
            except Exception as e:
                logging.warning('Exception at CrawlerType1.http_request: {}'.format(e))

    def extract_urls(self, html):
        """Parses html doc to gather other urls with same base_url as the webpage"""
        found_urls = []
        dom = lh.fromstring(html)
        for href in dom.xpath('//a/@href'):
            url = urljoin(self.base_url, href)
            if url not in self.parsed_urls and url.startswith(self.base_url):
                found_urls.append(url)
        return found_urls
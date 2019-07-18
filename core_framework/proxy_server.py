"""Proxy server runs constantly checking existing proxies and adding new ones"""
import requests


class Provider:
    def __init__(self, url, parser, crawler):
        self.url, self.parser, self.crawler = url, parser, crawler


class CrawlerType1:
    """covers simple crawling with GET method of all links that contain base domain name"""
    def __init__(self, provider_data):
        url = provider_data.url
        parser = provider_data.parser

        ses = requests.session()


class ParserType1:
    pass


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
        pass

    def gather(self):
        providers = Providers()
        provider_data = providers.classic()
        for data in provider_data:
            if isinstance(data, Provider):
                crawler = data.crawler
                crawler(data)






if __name__ == '__main__':
    api = ProxyServer()
    api.crawl()




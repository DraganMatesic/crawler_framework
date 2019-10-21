import re
import sys, os
import aiohttp
import requests
from bs4 import BeautifulSoup
try:
    from core_framework import user_agent
except:
    import user_agent
from aiohttp_socks import SocksConnector
from aiohttp import client_reqrep

_request_types = {
    1: {"Info": "Get without proxies", 'Method': "get"},
    2: {"Info": "Get with proxies", 'Method': "get"},
    3: {"Info": "Post without proxies", 'Method': "post"},
    4: {"Info": "Post with proxies", 'Method': "post"}
}

_proxy_types = {1: {"name": "Tor", 'http': 'socks5://', 'https': 'socks5://'},
                2: {"name": "PublicProxy", 'http': '', 'https': ''},
                3: {"name": "PublicProxy", 'http': '', 'https': ''}}


class Response:
    def __init__(self, data, html=None):
        self.data = data
        self.content = None  # html converted to bs object
        self.content_raw = None  # raw not converted to bs object
        self.text = None # html text
        self.url = None
        self.headers = None
        self.json = None
        self.html = html
        self.content_load()

    def content_load(self):
        if type(self.data) == requests.models.Response:
            self.url = self.data.url
            self.content_raw = self.data.content
            self.content = BeautifulSoup(self.data.content, 'lxml')
            self.text = self.data.text
            self.headers = self.data.headers
            try:
                self.json = self.data.json()
            except:
                pass
            return
        elif type(self.data) == client_reqrep.ClientResponse:
            self.url = self.data.url
            self.content_raw = self.html
            self.content = BeautifulSoup(self.html, 'lxml')
            self.text = self.data.text
            self.headers = self.data.headers
        else:
            self.content = self.data


class Request:

    def __init__(self, proxy_type=1, verify=True, proxy_data=None):
        self.ses = requests.session()
        self.url = None
        self.proxy = None
        self.timeout = 60
        self.payload = {}
        self.preserve = True  # preserve session
        self.proxy_type = proxy_type
        self.ip = "127.0.0.1"
        self.port = "9150"
        self.request_type = 1
        self.response = None
        self.response_raw = None
        self.args = None
        self.verify = verify
        self.headers = None
        self.session()
        self.proxy_data = proxy_data
        self.set_proxy()

    def set_proxy(self):
        if self.proxy_data is not None and self.proxy_data != []:
            if self.proxy_type == 1:
                self.ip = self.proxy_data.get('ipv4')
            if self.proxy_type == 2:
                self.ip = self.proxy_data.get('ip')
            self.port = self.proxy_data.get('port')

    def session(self):
        if self.ses is None or self.preserve is False:
            ses = requests.session()
            if self.headers is not None:
                self.headers = self.headers
            else:
                ses.headers['User-Agent'] = user_agent.load()
            ses.verify =self.verify
            self.ses = ses
        ua = self.ses.headers.get('User-Agent')
        if ua is not None:
            if type(ua) is str:
                if re.search('python', ua) is not None:
                    self.ses.headers.update(user_agent.load())

    def go(self, url, download=False, download_raw=False, args=None):
        "download_raw - we use when we need to get other informations such as headers, cookies etc"
        self.args = args
        self.url = url
        self.session()
        self.prepare_proxy()
        method = _request_types.get(self.request_type).get('Method')
        if args is not None:
            response = getattr(self, method)(args=args)
        else:
            response = getattr(self, method)()

        if download_raw is True:
            if type(response) is dict:
                return response
            return response

        if download is True:
            if type(response) is dict:
                return response
            return response.content
        else:
            self.response_raw = response
            self.response = Response(self.test_response(response))
        return self.response

    def prepare_proxy(self):

        self.proxy = {
            'http': '{0}{1}:{2}'.format(_proxy_types.get(self.proxy_type).get('http'),self.ip, self.port),
            'https': '{0}{1}:{2}'.format(_proxy_types.get(self.proxy_type).get('https'),self.ip, self.port)}

    @staticmethod
    def test_response(response, html=None):
        if type(response)is dict:
            return response
        if type(response) is int:
            return {"RequestError": "BadIp"}
        # requests status checker
        if type(response) is requests.models.Response:
            if 399 < int(response.status_code) < 500:
                return {"RequestError": "Blocked"}
            if int(response.status_code) > 499:
                return {"RequestError": "Page server is down"}
        # aiohttp status checker
        if type(response) is client_reqrep.ClientResponse:
            if 399 < int(response.status) < 500:
                return {"RequestError": "Blocked"}
            if int(response.status) > 499:
                return {"RequestError": "Page server is down"}

        if html is not None:
            if re.search(b'HTTP/1.1\s+400\s+Bad Request', html):
                return {"RequestError": "BadIp"}
        return response

    def get(self, args=None):
        try:
            if self.request_type is 1:
                return self.ses.get(self.url,timeout=self.timeout)
            if self.request_type is 2:
                return self.ses.get(self.url, proxies=self.proxy, timeout=self.timeout)
        except Exception as e:
            return {'RequestError': "{}".format(str(e))}

    def post(self, args=None):
        try:
            if args is None:
                args = {}
            args.update({"timeout": self.timeout})
            if self.args is not None:
                args.update(self.args)
            if self.request_type is 3:
                if args.get('data') is None:
                    return self.ses.post(self.url, self.payload, **args)
                if args.get('data') is not None:
                    return self.ses.post(self.url, **args)
            if self.request_type is 4:
                args.update({"proxies": self.proxy})
                if args.get('data') is None:
                    return self.ses.post(self.url, self.payload, **args)
                if args.get('data') is not None:
                    return self.ses.post(self.url, **args)
        except Exception as e:
            return {'RequestError': "{}".format(str(e))}


class AsyncRequest(Request):
    def __init__(self, proxy_type=1, verify=True, proxy_data=None):
        Request.__init__(self, proxy_type, verify, proxy_data)
        del self.ses  # removing request session since we don't need that here
        if proxy_type != self.proxy_type:
            print("All available provies for type {} are taken, switching to proxy type {}".format(proxy_type, self.proxy_type))
        self.prepare_proxy()
        if self.proxy_type == 1:
            self.connector = self.tor_connector()
        self.async_ses = None
        self.async_session()

    def tor_connector(self):
        proxy = f"{self.proxy.get('http')}"
        connector = SocksConnector.from_url(proxy)
        self.connector = connector
        return connector

    def async_session(self):
        if self.async_ses is None or self.preserve is False:
            if self.headers is not None:
                self.headers = self.headers
            else:
                self.headers = user_agent.load()
            # TOR proxy type
            if self.proxy_type == 1:
                self.async_ses = aiohttp.ClientSession(headers=self.headers, connector=self.tor_connector())
            # Public proxy type
            if self.proxy_type == 2:
                if self.verify is False:
                    connector = aiohttp.TCPConnector(verify_ssl=False)
                    self.async_ses = aiohttp.ClientSession(headers=self.headers, connector=connector)
                else:
                    self.async_ses = aiohttp.ClientSession(headers=self.headers)

    def clean(self):
        self.async_ses = None

    async def go(self, url, download=False, download_raw=False, args=None):
        try:
            self.args = args
            self.url = url
            self.prepare_proxy()
            if self.proxy_type == 1:
                self.tor_connector()
            self.async_session()

            method = _request_types.get(self.request_type).get('Method')
            if args is not None:
                html, response = await getattr(self, method)(args=args)
            else:
                html, response = await getattr(self, method)()

            if download is True:
                if type(response) is dict:
                    return response
                return response.content
            else:
                resp_stat = self.test_response(response, html)
                self.response = Response(resp_stat, html)

            return response
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            e = 'request.py, async def go |+error type: %s | py location: %s | +error line: %s | +error description: %s' % (str(exc_type), os.path.abspath(fname), exc_tb.tb_lineno, str(e))
            print(e)
            return {'RequestError': "{}".format(str(e))}

    async def get(self, args=None):
        """shared session for chain requests GET>POST>GET..."""

        try:
            if args is None:
                args = {}
            # GET method without proxy
            if self.request_type is 1:
                async with self.async_ses.get(self.url, timeout=self.timeout) as response:
                    html = await response.read()
                    return html, response
            # GET method with proxy
            if self.request_type is 2:
                if self.proxy_type == 1:
                    # Proxy type is Tor socks
                    async with self.async_ses.get(self.url, timeout=self.timeout, proxy_auth=None) as response:
                        html = await response.read()
                        return html, response
                if self.proxy_type in [2]:
                    proxy = f"http://{self.proxy.get('http')}"
                    async with self.async_ses.get(self.url, proxy=proxy, timeout=self.timeout) as response:
                        html = await response.read()
                        return html, response

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            e = 'request.py, def get |+error type: %s | py location: %s | +error line: %s | +error description: %s' % (str(exc_type), os.path.abspath(fname), exc_tb.tb_lineno, str(e))
            return '', {'RequestError': "{}".format(str(e))}

    async def post(self, args=None):
        """shared session for chain requests GET>POST>GET..."""
        try:
            if args is None:
                args = {}
            args.update({"timeout": self.timeout})
            if self.args is not None:
                args.update(self.args)

            # POST without proxies
            if self.request_type is 3:
                if args.get('data') is None:
                    async with self.async_ses.post(self.url, data=self.payload, timeout=self.timeout) as response:
                        html = await response.read()
                        return html, response
                if args.get('data') is not None:
                    async with self.async_ses.post(self.url, timeout=self.timeout, **args) as response:
                        html = await response.read()
                        return html, response

            # POST with proxies
            if self.request_type is 4:
                # if proxy is tor
                if self.proxy_type == 1:
                    # if payload is not required
                    if args.get('data') is None:
                        async with self.async_ses.post(self.url, data=self.payload, timeout=self.timeout, proxy_auth=None) as response:
                            html = await response.read()
                            return html, response
                    # if payload is required
                    if args.get('data') is not None:
                        async with self.async_ses.post(self.url, timeout=self.timeout, proxy_auth=None, **args) as response:
                            html = await response.read()
                            return html, response

                # if proxy is public proxy
                if self.proxy_type in [2]:
                    proxy = f"http://{self.proxy.get('http')}"
                    # if payload is not required
                    if args.get('data') is None:
                        async with self.async_ses.get(self.url, proxy=proxy, data=self.payload, timeout=self.timeout) as response:
                            html = await response.read()
                            return html, response

                    # if payload is required
                    if args.get('data') is not None:
                        async with self.async_ses.get(self.url, proxy=proxy, timeout=self.timeout, **args) as response:
                            html = await response.read()
                            return html, response

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            e = 'request.py, def post | +error type: %s | py location: %s | +error line: %s | +error description: %s' % (str(exc_type), os.path.abspath(fname), exc_tb.tb_lineno, str(e))
            print(e)
            return '', {'RequestError': "{}".format(str(e))}


if __name__ == '__main__':
    api = AsyncRequest()
import re
from urllib import parse
from bs4 import BeautifulSoup, Comment


class ParserType1:
    """Searches proxies"""
    def base_urls(self, html, base_url, parsed_links, rex=True):
        soup = BeautifulSoup(html, 'lxml')
        if rex is True:
            links = soup.find_all('a', {'href': rex})
        else:
            links = soup.find_all('a', {'href': re.compile(rex)})
        links = [base_url+link['href'].lstrip('/') for link in links if link['href'].startswith('/') and link['href'] not in ['/']]
        links = [link for link in links if link not in parsed_links]
        return links

    def simple(self, html):
        return re.findall('(\d+\.\d+.\d+\.\d+):(\d+)', html, re.DOTALL | re.IGNORECASE | re.MULTILINE)

    def simple_var2(self, html):
        return [x for x in re.findall(".*?(\d+\.\d+.\d+\.\d+).*?:(\d+).*?", html) if x[0].startswith('0') is False]

    def simple_td(self, html):
        return re.findall('<td>(\d+\.\d+.\d+\.\d+)</td>\s*<td>(\d+)</td>', html, re.DOTALL | re.IGNORECASE | re.MULTILINE)

    def simple_td_v1(self, html):
        return re.findall('<td class="t_ip">(\d+\.\d+.\d+\.\d+)</td>\s*<td class="t_port">.*?(\d+)</td>', html, re.DOTALL | re.IGNORECASE | re.MULTILINE)

    def simple_td_v2(self, html):
        return re.findall('<td.*?>.*?(\d+\.\d+.\d+\.\d+).*?</td>\s*<td.*?">.*?(\d{2,}).*?</td>', html, re.DOTALL | re.IGNORECASE | re.MULTILINE)

    def js_escaped(self, html):
        rex = "<tr><td><script type='text/javascript'>eval\(unescape\('(.*?)'\)\);</script><noscript>" \
              "Please enable javascript</noscript></td><td>(\d+)</td></tr>"
        ips_find = re.findall(rex, html, re.DOTALL | re.IGNORECASE | re.MULTILINE)
        ips_find = [(parse.unquote(ip), port) for ip, port in ips_find]
        ips = []
        for ip, port in ips_find:
            ipsearch = re.search('(\d+\.\d+.\d+\.\d+)', ip)
            if ipsearch is not None:
                ips.append((ipsearch.group(1), port))
        return ips

    def find_ips(self, html):
        ips = []
        if html is not None:
            html = html.decode(errors='ignore')
            ips.extend(self.simple(html))
            ips.extend(self.simple_var2(html))
            ips.extend(self.js_escaped(html))
            ips.extend(self.simple_td(html))
            ips.extend(self.simple_td_v1(html))
            ips.extend(self.simple_td_v2(html))
        return ips


class ParserType2(ParserType1):

    def td_href(self, html):
        return re.findall('<td><a.*?">.*?(\d+\.\d+\.\d+\.\d+).*?</a></td>.*?<td><a.*?">.*?(\d+).*?</a></td>', html, re.DOTALL | re.MULTILINE)

    def xroxy(self, html):
        soup = BeautifulSoup(html, 'lxml')
        for element in soup(text=lambda text: isinstance(text, Comment)):
            element.extract()
        html = str(soup)
        proxies = self.td_href(html)
        return proxies

    def find_ips(self, html, **kwargs):
        ips = list()
        netloc = kwargs.get('netloc')
        if html is not None:
            html = html.decode(errors='ignore')
            if netloc == 'www.xroxy.com':
                ips.extend(self.xroxy(html))
        return ips


import re
from urllib import parse
from bs4 import BeautifulSoup


class ParserType1:
    """Searches proxies"""
    def base_urls(self, html, base_url, parsed_links):
        soup = BeautifulSoup(html, 'lxml')
        links = soup.find_all('a', {'href': True})
        links = [base_url+link['href'].lstrip('/') for link in links if link['href'].startswith('/') and link['href'] not in ['/']]
        links = [link for link in links if link not in parsed_links]
        return links

    def simple(self, html):
        return re.findall('(\d+\.\d+.\d+\.\d+):(\d+)', html, re.DOTALL | re.IGNORECASE | re.MULTILINE)

    def simple_td(self, html):
        return re.findall('<td>(\d+\.\d+.\d+\.\d+)</td>\s*<td>(\d+)</td>', html, re.DOTALL | re.IGNORECASE | re.MULTILINE)

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
            ips.extend(self.js_escaped(html))
            ips.extend(self.simple_td(html))

        return ips
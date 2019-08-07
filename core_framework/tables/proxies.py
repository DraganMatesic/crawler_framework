from sqlalchemy import *
from core_framework.tables.bases import *

# ======================================================================
#                            PROXY LIST
# ======================================================================


class ProxyListAll:
    """Contains all proxies that were ever found and their current stats"""
    __tablename__ = proxy_table

    ip = Column(String(64))  # proxy ip we are going to use
    port = Column(Integer)  # proxy port that is open for above ip
    sha = Column(String(64))  # hash value of ip and port
    avg_resp = Column(Numeric(18, 2))  # average response rate of  proxy
    protocols = Column(String(1000))  # protocols that are available are separated by semicolon (http;https;socks5...)
    proxy_type = Column(String(1000), server_default='public')  # proxy type can be public, vpn, private, residential, dedicated, shared, data center etc..
    last_checked = Column(DateTime)  # date and time when this proxy was checked is it functional and lvl of anonymity
    anonymity = Column(Integer(), server_default='0')   # after check is done it will get anonymity rating 0 = unprocessed, 1 = anonymous, 2 = transparent, 3 = elite
    disabled = Column(Integer(), server_default='0')   # status of proxy server if 0 it is up runing if 1 proxy server is down
    username = Column(String(1000))  # username for connection on private proxy/VPN
    password = Column(String(1000))  # password for connection on private proxy/VPN
    proxy_source = Column(String(4000))  # name of proxy source can be scraping web page url, shot url to data center like 'zproxy.lum-superproxy.io'
    date_created = Column(DateTime, server_default=func.now())


class ProxyListOra(BaseOra, ProxyListAll):
    id = Column('id', Integer, Sequence('proxy_id_seq'), primary_key=True)


class ProxyListMS(BaseMs, ProxyListAll):
    id = Column('id', Integer, primary_key=True)


class ProxyListPstg(BasePstg, ProxyListAll):
    proxy_id_seq = Sequence('proxy_id_seq', metadata=BasePstg.metadata)
    id = Column(
        Integer, proxy_id_seq,
        server_default=proxy_id_seq.next_value(), primary_key=True)

#======================================================================
#                            PROXY LOGS
#======================================================================


class ProxyLog:
    """table contains all records how did crawling finished for specific proxy webpage"""
    __tablename__ = proxy_log_table

    proc_id = Column(String(64))  # it is has value of datetime that serves as unique id for that crawling
    start_time = Column(DateTime)  # time when we started with crawling of some webpage
    end_time = Column(DateTime)  # time when we ended with crawling of some webpage
    duration = Column(Integer())  # how many seconds was needed to finish crawling some webpage
    webpage = Column(String(2000))  # url of page that we are crawling
    errors = Column(Integer())  # number of errors that occurred during crawling time
    crawled_urls = Column(Integer())  # number of urls that have been crawled
    errors_ratio = Column(Integer())  # error ratio between number of crawled webpages and error that appeared

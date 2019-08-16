import io
import re
import pickle
import shutil
import zipfile
import requests
from bs4 import BeautifulSoup
from core_framework import user_agent
from core_framework.settings import *
from core_framework.db_engine import  DbEngine


def install(install_path=tor_dir):
    """
    :param str install_path:
    Description:
        install_path = is place where you want Tor to be instaled
            default is in Users\yourusername\Tor
    """
    if os.path.isdir(tor_dir):
        shutil.rmtree(tor_dir)

    print("> acquiring tor expert bundle zip file")
    ses = requests.session()
    ses.headers.update(user_agent.load())
    r = ses.get(tor_url)
    html = r.content

    soup = BeautifulSoup(html, 'lxml')
    tbodies = soup.find_all('tbody')
    tbody = [tbody for tbody in tbodies if tbody.text.__contains__('Contains just Tor and nothing else')]

    dl_link = None
    if tbody:
        a = tbody[0].find('a', {'class': 'downloadLink', 'href': True})
        if a:
            dl_link = a['href']

    if dl_link is None:
        print('Unable to download tor zip package. Try again later.')
        return

    print("> unpacking and installing")
    file = ses.get(dl_link)
    z = zipfile.ZipFile(io.BytesIO(file.content))
    z.extractall(install_path)

    with open(r'{}\tor_path.txt'.format(tor_user_path), 'w') as f:
        f.write(install_path)
        f.close()

    print("> creating additional directories")
    # Deploying additional directories needed for tor_network to work
    for folder in [r'TorData', r'TorData\data', r'TorData\config']:
        os.mkdir(r'{}\{}'.format(tor_dir, folder))

    with open(tor_config, 'wb') as fw:
        pickle.dump(tor_setup_default, fw)

    print(f"> tor expert bundle installed at {install_path}")


def make_torrc(tor_dir, socket_port, control_port,ipv4):
    """example how torrc file should be constructed"""
    return tor_settings.format(tor_dir, socket_port, control_port, ipv4).replace('        ', "")


class TorNetwork(DbEngine):
    def __init__(self):
        DbEngine.__init__(self)



# install tor expert bundle
# install()

"""Gathering latest user-agent string"""
import os
import json
import pickle
import requests
from datetime import  datetime
from core_framework.settings import *


def get():
    def crawl():
        try:
            ses = requests.session()
            r =ses.get('http://crodesigner.pythonanywhere.com/user/', timeout=10)
            firefox_ua = json.loads(r.content)
        except Exception as e:
            print(f"crawler_framework exception raised {str(e)}")
            return 500

        return firefox_ua

    if os.path.exists(ua_data):
        with open(ua_data, 'rb') as fr:
            data = pickle.load(fr)
            last_update = data.get('last_update')

    else:
        new_data = crawl()
        if new_data != 500:
            with open(ua_data, 'wb') as fw:
                data = pickle.load(fw)
                data.update({'last_update': datetime.now()})
                pickle.dump(data, fw)






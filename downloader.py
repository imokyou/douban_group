# coding=utf8
import traceback
import requests
from fake_useragent import UserAgent
from settings import *
from db import RedisClient


conn = RedisClient()


def get_page(url, headers={}, use_proxy=False, count=0):
    try:
        if count >= DOWNLOAD_RETRY_TIMES:
            return None
        ua = UserAgent()
        headers['User-Agent'] = ua.random
        headers['Accept-Encoding'] = 'gzip, deflate, sdch'
        headers['Accept-Language'] = 'en-US,en;q=0.8'
        headers['Upgrade-Insecure-Requests'] = '1'
        headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        if use_proxy:
            proxy = conn.rand_proxy()
            proxies = {proxy.split('://')[0]: proxy}
            logging.info('get from %s, use proxy %s, retry times %s' % (url, proxy, count))
            resp = requests.get(url, headers=headers, proxies=proxies, timeout=DOWNLOAD_TIMEOUT)
        else:
            logging.info('get from %s' % url)
            resp = requests.get(url, headers=headers, timeout=DOWNLOAD_TIMEOUT)
        if not resp or resp.status_code != 200:
            count = count + 1
            get_page(url, headers=headers, use_proxy=True, count=count)
        return resp.content
    except:
        traceback.print_exc()
        count = count + 1
        get_page(url, headers=headers, use_proxy=True, count=count)
    return None

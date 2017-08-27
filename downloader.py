# coding=utf8
import traceback
import requests
from fake_useragent import UserAgent
from settings import *
from db import RedisClient

conn = RedisClient()

def get_page(url, headers={}, use_proxy=False, count=0):
    try:
        if use_proxy and not conn.proxy_queue_len:
            logging.info('no proxy')
            return None
        if count >= DOWNLOAD_RETRY_TIMES:
            logging.info('Max retries exceeded with url, retry: %s times' % count)
            return None
        ua = UserAgent()
        headers['User-Agent'] = ua.random
        headers['Accept-Encoding'] = 'gzip, deflate, sdch'
        headers['Accept-Language'] = 'en-US,en;q=0.8'
        headers['Upgrade-Insecure-Requests'] = '1'
        headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        if use_proxy:
            proxy = ''
            while 'https' not in proxy:
                proxy = conn.rand_proxy()
            proxy.replace('https', 'http')
            proxies = {'http': proxy, 'https': proxy}
            logging.info('get from %s, CRAWL_MODE: %s, use proxy %s, retry times %s' % (url, CRAWL_MODE, proxy, count))
            resp = requests.get(url, headers=headers, proxies=proxies, timeout=DOWNLOAD_TIMEOUT)
        else:
            logging.info('get from %s, CRAWL_MODE: %s' % (url, CRAWL_MODE))
            resp = requests.get(url, headers=headers, timeout=DOWNLOAD_TIMEOUT)
        if not resp  or not resp.content or resp.status_code != 200:
            count = count + 1
            get_page(url, headers=headers, use_proxy=use_proxy, count=count)
        return resp.text
    except:
        count = count + 1
        get_page(url, headers=headers, use_proxy=use_proxy, count=count)
    return None

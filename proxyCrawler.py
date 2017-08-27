# coding=utf8
from gevent import monkey;monkey.patch_all()
from gevent.pool import Pool
import requests
from time import sleep
from bs4 import BeautifulSoup
import threading
from concurrent.futures import ThreadPoolExecutor
from settings import *
from downloader import get_page
from proxyChecker import Tester
from db import RedisClient


class ProxySpider(object):
    
    def __init__(self):
        self.proxy_api = PROXY_API

    def get_raw_proxies(self):
        try:
            proxies = []
            resp = requests.get(self.proxy_api)
            if resp.status_code == 200 and resp.content:
                proxies = resp.content.split('\r\n')
            proxies = ['https://%s' % x for x in proxies]
        except:
            pass
        return proxies

_WORKER_THREAD_NUM = 100

class ProxyCrawler(object):

    def __init__(self):
        self.conn = RedisClient()
        self.proxy_nums = 0
        self.spider = ProxySpider()
        self.checker = Tester()

    def proxy_enough(self):
        self.proxy_nums = self.conn.proxy_queue_len
        if self.proxy_nums >= THRESHOLD_LOWER:
            return True
        else:
            return False


    def run(self):
        if not IS_SERVER or not ACTIVATE_CRAWL_PROXY:
            return None
        logging.info('proxy crawler start running...')
        pools = Pool(_WORKER_THREAD_NUM)
        while True:
            if self.proxy_enough():
                continue
                logging.info('proxy is enough, proxy crawler has been paused for now...')
                sleep(CRAWL_PAGE_SLEEP)
            proxies = self.spider.get_raw_proxies()
            pools.map(self.checker.test_single, proxies)
            logging.info('waitting for next round..., paused %s seconds for now.' % CRAWL_PAGE_SLEEP)
            sleep(CRAWL_PAGE_SLEEP)
                    

if __name__ == '__main__':
    proxy_crawler = ProxyCrawler()
    proxy_crawler.run()

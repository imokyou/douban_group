# coding=utf8
from gevent import monkey;monkey.patch_all()
from gevent.pool import Pool
from time import sleep
from bs4 import BeautifulSoup
import threading
from concurrent.futures import ThreadPoolExecutor
from settings import *
from downloader import get_page
from proxyChecker import Tester
from db import RedisClient


class ProxyMetaClass(type):
    def __new__(cls, name, bases, attrs):
        attrs['__CrawlFuncCount__'] = 0
        attrs['__CrawlFunc__'] = []
        for k, v in attrs.items():
            if 'crawl_' in k:
                attrs['__CrawlFunc__'].append(k)
                attrs['__CrawlFuncCount__'] = attrs['__CrawlFuncCount__'] + 1
        return type.__new__(cls, name, bases, attrs)


class ProxySpider(object):
    __metaclass__ = ProxyMetaClass

    def get_raw_proxies(self, callback, index=1):
        proxies = []
        for proxy in eval("self.{}({})".format(callback, index)):
            proxies.append(proxy)
        return proxies

    def crawl_daili66(self, index=1):
        start_url = 'http://www.66ip.cn/{}.html'
        html = get_page(start_url.format(index))
        if html:
            bs = BeautifulSoup(html, 'lxml')
            iptrs = bs.select('.containerbox table tr')
            i = 0
            for tr in iptrs:
                if i == 0:
                    i = i + 1
                    continue
                ip = tr.select('td:nth-of-type(1)')[0].get_text().encode('utf8')
                port = tr.select('td:nth-of-type(2)')[0].get_text().encode('utf8')
                i = i + 1
                proxy = 'http://{}:{}'.format(ip, port)
                yield proxy

    def crawl_xici(self, index=1):
        start_url = 'http://www.xicidaili.com/nn/{}'
        html = get_page(start_url.format(index))
        if html:
            bs = BeautifulSoup(html, 'lxml')
            iptrs = bs.select('#ip_list tr')
            i = 0
            for tr in iptrs:
                if i == 0:
                    i = i + 1
                    continue
                ip = tr.select('td:nth-of-type(2)')[0].get_text().encode('utf8')
                port = tr.select('td:nth-of-type(3)')[0].get_text().encode('utf8')
                proto = tr.select('td:nth-of-type(6)')[0].get_text().encode('utf8').lower()
                i = i + 1
                proxy = '{}://{}:{}'.format(proto, ip, port)
                yield proxy

    def crawl_goubanjia(self, index=1):
        start_url = 'http://www.goubanjia.com/free/gngn/index{}.shtml'
        html = get_page(start_url.format(index))
        if html:
            bs = BeautifulSoup(html, 'lxml')
            iptds = bs.select('td.ip')
            for td in iptds:
                ip = []
                for t in td:
                    if t.name not in ['span', 'div'] or not t.string or t.attrs.get('style') == 'display: none;':
                        continue
                    ip.append(t.string)
                proxy = 'http://{}:{}'.format(''.join(ip[0:-2]), ip[-1])
                yield proxy
    
    def crawl_kuaidaili(self, index=1):
        start_url = 'http://www.kuaidaili.com/free/inha/{}/'
        html = get_page(start_url.format(index))
        if html:
            bs = BeautifulSoup(html, 'lxml')
            iptrs = bs.select('#list > table > tbody > tr')
            for tr in iptrs:
                proto = tr.select('td:nth-of-type(4)')[0].get_text().encode('utf8').lower()
                ip = tr.select('td:nth-of-type(1)')[0].get_text().encode('utf8')
                port = tr.select('td:nth-of-type(2)')[0].get_text().encode('utf8')

                proxy = '{}://{}:{}'.format(proto, ip, port)
                yield proxy


_WORKER_THREAD_NUM = 100

class ProxyCrawler(object):

    def __init__(self):
        self.conn = RedisClient()
        self.proxy_nums = 0
        self.spider = ProxySpider()
        self.checker = Tester()

    def proxy_enough(self):
        self.proxy_nums = self.conn.queue_len
        if self.proxy_nums >= THRESHOLD_LOWER:
            return True
        else:
            return False


    def run(self):
        logging.info('proxy crawler start running...')
        pools = Pool(_WORKER_THREAD_NUM)
        while True:
            if self.proxy_enough():
                continue
                logging.info('proxy is enough, proxy crawler has been paused for now...')
                sleep(60)
            for index in xrange(1, 20):
                if not self.proxy_enough():
                    for label in xrange(self.spider.__CrawlFuncCount__):
                        callback = self.spider.__CrawlFunc__[label]
                        if callback in BLOCK_SITE:
                            continue
                        proxies = self.spider.get_raw_proxies(callback, index)
                        pools.map(self.checker.test_single, proxies)
                        logging.info('crawl from %s end, waitting for crawl next web site' % callback)
                        sleep(60)
                    logging.info('round %s end, waitting from next round, paused for %s seconds' % (index, CRAWL_PAGE_SLEEP))

if __name__ == '__main__':
    proxy_crawler = ProxyCrawler()
    proxy_crawler.run()

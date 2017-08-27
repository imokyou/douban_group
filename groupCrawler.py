# coding=utf8
from gevent import monkey;monkey.patch_all()
from gevent.pool import Pool
import traceback
import re
from random import randint
from time import sleep
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from settings import *
from downloader import get_page
from db import RedisClient, MongoClient


class GroupCrawler(object):
    
    def __init__(self):
        self.redisdb = RedisClient()
        self.mongodb = MongoClient()
        self.crawl_urls = []
        self.use_proxy = False
        if CRAWL_MODE == 'proxy':
            self.use_proxy = True

        self.start_urls = [
            'https://www.douban.com/group/explore',
            'https://www.douban.com/group/explore/culture',
            'https://www.douban.com/group/explore/travel',
            'https://www.douban.com/group/explore/ent',
            'https://www.douban.com/group/explore/fashion',
            'https://www.douban.com/group/explore/life',
            'https://www.douban.com/group/explore/tech'
        ]

    def start_requests(self):
        for url in self.start_urls:
            self.redisdb.put_url(url)

    def parse_content(self, html, url):
        if not html:
            logging.info('html is empty, from %s' % url)
            self.redisdb.remove_url_success(url)
            self.redisdb.put_url(url)
            return None
        bs = BeautifulSoup(html, 'lxml')
        # 找下一步要爬取的
        links = bs.find_all('a', href=re.compile('https://www.douban.com/group/\d*-*\w*/$'))
        for l in links:
            new_url = l.attrs.get('href', '')
            if new_url and new_url not in self.crawl_urls and not self.redisdb.is_url_success(new_url):
                self.redisdb.put_url(new_url)
        
        # 解析想要的内容
        info = {'name': '', 'gid': '', 'members': 0, 'created_at': '', 'owner_name': '', 'owner_id': ''}

        try:
            info['name'] = self.parse_content_name(bs)
            info['gid'] = self.parse_content_gid(bs)
            info['members'] = self.parse_content_members(bs)
            info['created_at'] = self.parse_content_createdat(bs)
            info['owner_id'], info['owner_name'] = self.parse_content_owner(bs)
            logging.info(info)
            try:
                if info['gid']:
                    self.mongodb.save_group(info)
                else:
                    self.redisdb.put_url(url)
            except:
                self.redisdb.put_url(url)
                logging.info('insert into mysql error: %s' % info)
                traceback.print_exc()
        except:
            if new_url not in self.start_urls:
                logging.info('parse url %s error' % url)
                self.redisdb.put_url(url)
                # traceback.print_exc()

    def parse_content_name(self, bs):
        try:
            return bs.select_one('#group-info > h1').string.strip().encode('utf8')
        except:
            pass
        return ''

    def parse_content_gid(self, bs):
        try:
            group_members = bs.select_one('#content > div.grid-16-8.clearfix > div.aside > div.mod.side-nav > p > a')
            return group_members.attrs.get('href').split('/group/')[1].split('/')[0]
        except:
            pass
        return ''

    def parse_content_members(self, bs):
        try:
            group_members = bs.select_one('#content > div.grid-16-8.clearfix > div.aside > div.mod.side-nav > p > a')
            pattern = re.compile('.*?\((\d+)\)', re.S)
            match = pattern.match(group_members.string.strip())
            return match.groups()[0].encode('utf8')
        except:
            pass
        return 0

    def parse_content_createdat(self, bs):
        try:
            created_at = ''
            for s in bs.select_one('#content > div.grid-16-8.clearfix > div.article > div.group-board p').strings:
                created_at += s.strip()

            pattern = re.compile('.*?(\d{4}-\d{2}-\d{2})', re.S)
            match = pattern.match(created_at)
            return match.groups()[0].encode('utf8')
        except:
            pass
        return ''

    def parse_content_owner(self, bs):
        try:
            owner = bs.select_one('#content > div.grid-16-8.clearfix > div.article > div.group-board > p > a')
            owner_id = owner.attrs.get('href').split('/people/')[1].split('/')[0]
            owner_name = owner.string.strip().encode('utf8')
            return owner_id, owner_name
        except:
            pass
        return '', ''

    def crawler(self, iurl):
        url, use_proxy = iurl
        self.crawl_urls.remove(url)
        self.redisdb.put_url_success(url)
        headers = {'Referer': 'https://www.douban.com/group/explore'}
        content = get_page(url, headers=headers, use_proxy=use_proxy)
        self.parse_content(content, url)

    def run(self):
        print 'group crawler start runing'
        if IS_SERVER:
            self.start_requests()
        pools = Pool(CRAWL_WORKER_THREAD_NUM)
        while True:
            while self.redisdb.url_queue_len:
                urls = [self.redisdb.pop_url() for x in range(CRAWL_WORKER_THREAD_NUM)]
                urls = filter(None, urls)
                self.crawl_urls = urls

                pools.map(self.crawler, [(x, self.use_proxy) for x in urls])
                logging.info('waitting for next round')
                self.crawl_urls = []
                if CRAWL_MODE == 'mix':
                    self.use_proxy = not self.use_proxy
                sleep(CRAWL_WORKER_SLEEP)
            else:
                print 'url queue len is: %s' % self.redisdb.url_queue_len


if __name__ == '__main__':
    group = GroupCrawler()
    group.run()
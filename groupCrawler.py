# coding=utf8
import traceback
import re
import Queue
from random import randint
from time import sleep
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
import MySQLdb
from settings import *
from downloader import get_page
from db import RedisClient

datadb = MySQLdb.connect("localhost","root","lupin2008cn","douban" )
cursor = datadb.cursor()

redisdb = RedisClient()

_WORKER_THREAD_NUM = 10
start_urls = [
    'https://www.douban.com/group/explore',
    'https://www.douban.com/group/explore/culture',
    'https://www.douban.com/group/explore/travel',
    'https://www.douban.com/group/explore/ent',
    'https://www.douban.com/group/explore/fashion',
    'https://www.douban.com/group/explore/life',
    'https://www.douban.com/group/explore/tech'
]

def start_requests():
    for url in start_urls:
        redisdb.put_url(url)

def parse_content(html, url):
    if not html:
        logging.info('html is empty, from %s' % url)
        redisdb.put_url(url)
        return None
    bs = BeautifulSoup(html, 'lxml')
    # 找下一步要爬取的
    links = bs.find_all('a', href=re.compile('https://www.douban.com/group/\d*-*\w*/$'))
    for l in links:
        url = l.attrs.get('href', '')
        if url and not redisdb.is_url_success(url):
            redisdb.put_url(url)
    
    # 解析想要的内容
    info = {'name': '', 'gid': '', 'members': 0, 'created_at': '', 'owner_name': '', 'owner_id': ''}

    try:
        info['name'] = bs.select_one('#group-info > h1').string.strip().encode('utf8')

        group_members = bs.select_one('#content > div.grid-16-8.clearfix > div.aside > div.mod.side-nav > p > a')
        info['gid'] = group_members.attrs.get('href').split('/group/')[1].split('/')[0]

        pattern = re.compile('.*?\((\d+)\)', re.S)
        match = pattern.match(group_members.string.strip())
        info['members'] = match.groups()[0].encode('utf8')
  
        created_at = ''
        for s in bs.select_one('#content > div.grid-16-8.clearfix > div.article > div.group-board p').strings:
            created_at += s.strip()

        pattern = re.compile('.*?(\d{4}-\d{2}-\d{2})', re.S)
        match = pattern.match(created_at)
        info['created_at'] = match.groups()[0].encode('utf8')

        owner = bs.select_one('#content > div.grid-16-8.clearfix > div.article > div.group-board > p > a')
        info['owner_id'] = owner.attrs.get('href').split('/people/')[1].split('/')[0]
        info['owner_name'] = owner.string.strip().encode('utf8')
    except:
        traceback.print_exc()
    if info['gid']:
        logging.info(info)
        try:
            sql = '''
            INSERT INTO `group` (name, gid, members, created_at, owner_name, owner_id) VALUES
            ('%s', '%s', %s, '%s', '%s', '%s')
            ''' % (info['name'], info['gid'], info['members'], info['created_at'], info['owner_name'], info['owner_id'])
            logging.debug(sql)
            cursor.execute(sql)
            datadb.commit()
        except:
            traceback.print_exc()


def crawler():
    while redisdb.url_queue_len:
        url = redisdb.pop_url()
        if redisdb.is_url_success(url):
            continue
        redisdb.put_url_success(url)
        headers = {
            #'Host': 'www.douban.com',
            'Referer': 'https://www.douban.com/group/explore'
        }
        content = get_page(url)
        parse_content(content, url)

class GroupCrawler(object):
    
    def run(self):
        print 'group crawler start runing'
        start_requests()
        while True:
            with ThreadPoolExecutor(max_workers=_WORKER_THREAD_NUM) as executor:
                executor.submit(crawler)
            sleep(30)


if __name__ == '__main__':
    group = GroupCrawler()
    group.run()
# coding=utf8
import traceback
from random import randint
import urllib
import redis
import pymongo
from settings import *


class RedisClient(object):

    def __init__(self):
        try:
            if REDIS['password']:
                redis_pool = redis.ConnectionPool(host=REDIS['host'], port=REDIS['port'], password=REDIS['password'], db=REDIS['db'])
            else:
                redis_pool = redis.ConnectionPool(host=REDIS['host'], port=REDIS['port'], db=REDIS['db'])
            self._db = redis.Redis(connection_pool=redis_pool)
        except:
            logging.info('connect redis error')
        self._proxy = 'proxy'
        self._proxy_source = 'proxy:source'
        self._url = 'group:new:urls'
        self._old_url = 'group:old:urls'
        self._url_lock = 'group:urls:lock'

    def is_url_lock(self):
        '''群组爬虫加锁'''
        return not self._db.setnx(self.is_url_lock, 1)

    def url_unlock(self):
        '''群组爬虫解锁'''
        self._db.delete(self.is_url_lock)

    def add_new_url(self, url):
        if not url:
            return None
        self._db.sadd(self._url, url)
    
    def add_new_urls(self, urls):
        if not urls:
            return None
        for u in urls:
            self.add_new_url(u)

    def get_new_url(self):
        return self._db.spop(self._url)

    def get_new_urls(self, count=1):
        urls = [self.get_new_url() for i in xrange(count)]
        return filter(None, urls)

    def add_old_url(self, url):
        if not url:
            return None
        self._db.sadd(self._old_url, url)
    
    def add_old_urls(self, urls):
        if not urls:
            return None
        for u in urls:
            self.add_old_url(u)

    def is_old_url(self, url):
        return self._db.sismember(self._old_url, url)

    @property
    def url_len(self):
        return self._db.scard(self._url)

    def add_proxy(self, proxy):
        if not proxy:
            return None
        self._db.sadd(self._proxy, proxy)
    
    def add_proxies(self, proxies):
        if not proxies:
            return None
        for u in proxies:
            self.add_proxies(proxies)

    def add_proxy_source(self, proxy):
        if not proxy:
            return None
        self._db.sadd(self._proxy_source, proxy)

    def add_proxies_source(self, proxies):
        if not proxies:
            return None
        for u in proxies:
            self.add_proxy_source(u)

    def rand_proxy(self):
        return self._db.srandmember(self._proxy)

    def remove_proxy(self, proxy):
        return self._db.srem(self._proxy, proxy)

    def get_allproxy(self):
        proxies = self._db.smembers(self._proxy)
        return proxies

    @property
    def proxy_len(self):
        return self._db.scard(self._proxy)
        

class MongoClient(object):
    def __init__(self):
        try:
            if MONGODB['pwd']:
                mlink = 'mongodb://%s:%s@%s:%s/%s' \
                    % (urllib.quote_plus(MONGODB['user']),
                       urllib.quote_plus(MONGODB['pwd']),
                       MONGODB['host'],
                       MONGODB['port'],
                       MONGODB['db'])
            else:
                mlink = 'mongodb://%s:%s' % (MONGODB['host'], MONGODB['port'])
            self._conn = pymongo.MongoClient(mlink)
            self._db = self._conn[MONGODB['db']]
        except:
            logging.info('connect redis error')

    def save_group(self, info):
        if not self.is_group_exists(info['gid']):
            self._db['group'].save(info)

    def is_group_exists(self, gid):
        return self._db['group'].find({'gid': gid}).count()


if __name__ == '__main__':
    pass

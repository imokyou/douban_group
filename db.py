# coding = utf8
import traceback
from random import randint
import redis
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
        self._dbkey = 'proxy'
        self._group_urls = 'group:urls'
        self._group_urls_successed = 'group:urls:successed'

    def get(self, count=1):
        proxies = []
        try:
            proxies = self._db.lrange(self._dbkey, 0, count-1)
            self._db.ltrim(self._dbkey, count, -1)
        except:
            traceback.print_exc()
            logging.info('get proxy error, count:%s' % count)
        return proxies

    def put(self, proxy):
        try:
            proxies = self._db.lrange(self._dbkey, 0, self.queue_len)
            if proxy not in proxies:
                logging.info('PUT proxy {} INTO DB'.format(proxy))
                proxy = self._db.lpush(self._dbkey, proxy)
        except:
            traceback.print_exc()
            logging.info('pop proxy error')

    def pop(self):
        proxy = ''
        try:
            proxy = self._db.rpop(self._dbkey).encode('utf8')
        except:
            traceback.print_exc()
            logging.info('pop proxy error')
        return proxy

    def rand_proxy(self):
        try:
            proxy = self._db.rpop(self._dbkey).encode('utf8')
            self._db.lpush(self._dbkey, proxy)
            return proxy
        except:
            pass
        return None

    def empty(self):
        self._db.delete(self._dbkey)

    @property
    def queue_len(self):
        return self._db.llen(self._dbkey)

    @property
    def url_queue_len(self):
        return self._db.scard(self._group_urls)

    def put_url(self, url):
        try:
            if not self.is_url_success(url):
                self._db.sadd(self._group_urls, url)
        except:
            traceback.print_exc()
            logging.info('pop url error')
    
    def put_url_success(self, url):
        try:
            self._db.sadd(self._group_urls_successed, url)
        except:
            traceback.print_exc()
            logging.info('put url successed error')

    def is_url_success(self, url):
        return self._db.sismember(self._group_urls_successed, url)

    def pop_url(self):
        try:
            return self._db.spop(self._group_urls).encode('utf8')
        except:
            traceback.print_exc()
            logging.info('pop url error')
        return None


if __name__ == '__main__':
    conn = RedisClient()
    conn.put('xxxx')
    print(conn.pop())

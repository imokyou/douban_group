# coding=utf8
from gevent import monkey;monkey.patch_all()
from gevent.pool import Pool
import traceback
import requests
from concurrent.futures import ThreadPoolExecutor
from time import sleep
from db import RedisClient
from settings import *


def parse_proxy(proxy):
    proto, ip, port = '', '', ''
    proto = proxy.split('://')[0].lower()
    ip = proxy.split('//')[1].split(':')[0]
    port = proxy.split('//')[1].split(':')[1]
    return proto, ip, port

def is_ip_valid(address):
    parts = address.split(".")
    if len(parts) != 4:
        return False
    for item in parts:
        try:
            if not 0 <= int(item) <= 255:
                return False
        except:
            return False
    return True


class Tester(object):
    def __init__(self):
        self.conn = RedisClient()
    
    def test_single(self, proxy):
        try:
            proto, ip, port = parse_proxy(proxy.lower())
            if proto.lower() == 'http':
                logging.info('Invalid proxy %s, http wanted' % proxy)
                return None
            proxies = { proto: 'http://%s:%s' % (ip, port) }
            try:
                if proto.lower() == 'http':
                    resp = requests.get(HTTP_TEST_API, proxies=proxies, timeout=CHECK_TIMEOUT)
                else:
                    resp = requests.get(HTTPS_TEST_API, proxies=proxies, timeout=CHECK_TIMEOUT)
                if resp:
                    logging.info('Valid proxy %s' % proxy)
                    self.conn.put(proxy)
            except:
                logging.info('Invalid proxy %s' % proxy)
        except:
            traceback.print_exc()


_WORKER_THREAD_NUM = 50

class ProxyChecker(object):
    
    def __init__(self):
        self.conn = RedisClient()
        
    def run(self):
        tester = Tester()
        pools = Pool(_WORKER_THREAD_NUM)
        logging.info('proxy checker start running...')
        while True:
            proxies = self.conn.get(2000)
            pools.map(tester.test_single, proxies)
            logging.info('round end, waitting for next round, paused %s seconds for now...' % PROXY_CHECKER_SLEEP)
            sleep(PROXY_CHECKER_SLEEP)


if __name__ == '__main__':
    checker = ProxyChecker()
    checker.run()

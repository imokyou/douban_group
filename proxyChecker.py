# coding=utf8
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
            if proto == 'http':
                logging.info('InValid proxy %s, https wanted' % proxy)
                return None
            proxies = { proto: 'http://%s:%s' % (ip, port) }
            try:
                resp = requests.get(HTTPS_TEST_API, proxies=proxies, timeout=CHECK_TIMEOUT)
                if resp:
                    logging.info('Valid proxy %s' % proxy)
                    self.conn.put(proxy)
            except:
                logging.info('Invalid proxy %s' % proxy)
        except:
            traceback.print_exc()


_WORKER_THREAD_NUM = 10 


class ProxyChecker(object):
    
    def __init__(self):
        self.conn = RedisClient()
        
    def run(self):
        tester = Tester()
        threads = []
        logging.info('proxy checker start running...')
        while True:
            if len(threads) >= 1:
                for t in threads:
                    t.terminate() 
    
            threads = []
            proxies = self.conn.get(2000)
            with ThreadPoolExecutor(max_workers=_WORKER_THREAD_NUM) as executor:
                for proxy in proxies:
                    executor.submit(tester.test_single, proxy)
            sleep(PROXY_CHECKER_SLEEP)


if __name__ == '__main__':
    checker = ProxyChecker()
    checker.run()

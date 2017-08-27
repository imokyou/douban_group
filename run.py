# coding=utf8
from settings import *
from multiprocessing import Process
from groupCrawler import GroupCrawler
from proxyChecker import ProxyChecker
from proxyCrawler import ProxyCrawler
from settings import *


def run_as_server():
    logging.info('server start running...')  

    proxy_crawler = ProxyCrawler()
    proxy_checker = ProxyChecker()
    group_crawler = GroupCrawler()

    proxy_crawler_process = Process(target=proxy_crawler.run)
    proxy_checker_process = Process(target=proxy_checker.run)
    group_crawler_process = Process(target=group_crawler.run)
    group_crawler_process2 = Process(target=group_crawler.run)

    proxy_crawler_process.start()
    proxy_checker_process.start()
    group_crawler_process.start()
    group_crawler_process2.start()
    
    proxy_crawler_process.join()
    proxy_checker_process.join()
    group_crawler_process.join()
    group_crawler_process2.start()


def run_as_client():
    logging.info('server start running...')
    group_crawler = GroupCrawler()

    group_crawler_process = Process(target=group_crawler.run)
    group_crawler_process2 = Process(target=group_crawler.run)

    group_crawler_process.start()
    group_crawler_process2.start()

    group_crawler_process.join()
    group_crawler_process2.start()



def main():
    if IS_SERVER:
        run_as_server()
    else:
        run_as_client()

if __name__ == '__main__':
    main()
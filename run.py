# coding=utf8
from settings import *
from multiprocessing import Process
from groupCrawler import GroupCrawler
from proxyChecker import ProxyChecker
from proxyCrawler import ProxyCrawler


def main():
    logging.info('server start running...')
    if IS_SERVER and ACTIVATE_CRAWL_PROXY:    
        proxy_crawler = ProxyCrawler()
        proxy_checker = ProxyChecker()

        proxy_crawler_process = Process(target=proxy_crawler.run)
        proxy_checker_process = Process(target=proxy_checker.run)

        proxy_crawler_process.start()
        proxy_checker_process.start()
        
        proxy_crawler_process.join()
        proxy_checker_process.join()

    
    group_crawler = GroupCrawler()
    group_crawler_process = Process(target=group_crawler.run)
    group_crawler_process.start()
    group_crawler_process.join()

if __name__ == '__main__':
    main()
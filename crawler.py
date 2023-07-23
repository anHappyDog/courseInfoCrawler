import concurrent.futures

from imooc import imoocCrawler
from bilibili import bilibiliCrawler
from cnmooc import cnmoocCrawler
from icourse163 import icourse163Crawler
from icourse import icourseCrawler

class Crawler:

    @staticmethod
    def crawler():
        crawlers = [imoocCrawler, cnmoocCrawler, icourse163Crawler, bilibiliCrawler, icourseCrawler]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for webcrawler in crawlers:
                executor.submit(webcrawler.crawler)

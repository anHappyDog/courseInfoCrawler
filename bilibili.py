import re
from urllib.parse import quote
import warnings
import requests
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning

from common import WebCrawler, Video

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept': 'text/html, text/plain, */*'}


class BilibiliCralwler(WebCrawler):
    def __init__(self, setting=None):
        if setting is None:
            setting = WebCrawler.CrawlerSetting(maxPages=7)
        self.cookies = requests.get('https://www.bilibili.com', headers=headers).cookies
        super().__init__('bilibili', headers, setting)

    def _crawlerForSingleCourseAndPage(self, course, page):
        searchUrl = "https://api.bilibili.com/x/web-interface/search/type?" \
                    "keyword={}&page={}&search_type=video&pagesize=40".format(quote(course), page)
        videoList = requests.get(searchUrl, cookies=self.cookies).json()['data']['result']
        t = 0
        for videoInfo in videoList:

            name = BeautifulSoup(videoInfo['title'], 'html.parser').get_text()
            addr = videoInfo['arcurl']
            videoJson = requests.get('https://api.bilibili.com/x/web-interface/view?aid=%d' % videoInfo['aid']).json()
            duration = '{:.1f}'.format(videoJson['data']['duration'] / 3600)
            plays = videoJson['data']['stat']['view']
            comments = videoJson['data']['stat']['reply']
            video = Video(name, self.platform, course, plays, comments, addr, duration)
            # print('{}crawling {} for {} in {}\n addr is {}\npage is {}'.format(threading.current_thread().name, name,
            #                                                                   course, self.platform, addr, page))
            t += 1
            self.dataQueue.put(video)
        print(course + 'in {} collected {}'.format(page, t))


bilibiliCrawler = BilibiliCralwler()

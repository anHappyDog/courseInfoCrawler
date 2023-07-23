# -- coding: utf-8 --**
import re
import threading
from urllib.parse import quote

from bs4 import BeautifulSoup

from common import Video, WebCrawler
import requests

url = "https://www.imooc.com/search/course?words={}&source=&easy_type=&skill=&page={}"

payload = {}
headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.82',
    'X-Requested-With': 'XMLHttpRequest',
    'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Microsoft Edge";v="114"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"'
}


def processTime(timeDesc: str) -> float:
    x, timeCnt = 0, 0
    time = re.findall(r'\d+', timeDesc)
    re.sub(r'\d', '', timeDesc)

    for t in timeDesc:
        if t == '时':
            timeCnt += int(time[x])
            x += 1
        elif t == '分':
            timeCnt += int(time[x]) / 60
    return timeCnt


class ImoocCrawler(WebCrawler):
    def __init__(self, setting=None):
        if setting is None:
            setting = WebCrawler.CrawlerSetting(maxPages=7)
        super().__init__('imooc', headers, setting)

    def _crawlerForSingleCourseAndPage(self, course, page):
        try:
            response = requests.request("GET", url.format(quote(course), page)).json()
        except:
            print('sad')
        videoList = response['data']['hits']
        for videoInfo in videoList:
            name = videoInfo['_source']['title']
            addr = videoInfo['_source']['target_url']
            videoPage = requests.get(addr)
            videoBs = BeautifulSoup(videoPage.text, 'html.parser')
            try:
                comments = videoBs.find(string=re.compile('.*评价')).find_parent('li').find('span').get_text()
            except AttributeError:
                comments = None
            if '/class/' in addr:
                try:
                    plays = videoBs.find('span', string='学习人数').find_next_sibling('span').get_text()
                except:
                    plays = None
                try:
                    timeDesc = videoBs.find('span', string=re.compile('.*小时')).get_text()
                    duration = processTime(timeDesc)
                except:
                    duration = None

            elif '/sales/' in addr:
                plays = videoBs.find('em', {'class': 'js-numbers'}).get_text()
                duration = videoBs.find('span', string=re.compile('.*小时')).find('em').get_text()
            elif '/learn/' in addr:

                timeDesc = videoBs.find('span', string='时长').find_next_sibling('span').get_text()
                duration = processTime(timeDesc)
                plays = videoBs.find('span', string='学习人数').find_next_sibling('span').get_text()
            else:
                plays, comments, duration = None, None, None
            video = Video(name, self.platform, course, plays, comments, addr, duration)
            self.dataQueue.put(video)
            print('{}crawling {} for {} in {}\n addr is {}\npage is {}'.format(threading.current_thread().name, name,
                                                                               course, self.platform, addr, page))


imoocCrawler = ImoocCrawler()

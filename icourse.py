import threading
from urllib.parse import quote

import pymysql
import requests
from bs4 import BeautifulSoup

from common import WebCrawler, Video

url = "https://www.icourses.cn/web/sword/portalsearch/searchPage"

headers = {
    'Accept': 'text/html, */*; q=0.01',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Cookie': 'portaltikerviewcookiesys=6b614ed3797940768a0c0d300e5c9bea; Hm_lvt_787dbcb72bb32d4789a985fd6cd53a46=1689940719,1689986695; acw_tc=2760820416899914679502900e9096a824bf2004b1a65e340b139c076cecd4; JSESSIONID=5E2AF3E3BDB66FB5EB0C2F714D4C6F91-n1; Hm_lpvt_787dbcb72bb32d4789a985fd6cd53a46=1689991892',
    'Origin': 'https://www.icourses.cn',
    'Referer': 'https://www.icourses.cn/web/sword/portalsearch/homeSearch',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.82',
    'X-Requested-With': 'XMLHttpRequest',
    'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Microsoft Edge";v="114"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"'
}

'''
course:
name,playCnt,commentCnt,belongedCourse,platform,address,duration
'''


class IcourseCrawler(WebCrawler):
    def __init__(self,  setting=None):
        if setting is None:
            setting = WebCrawler.CrawlerSetting()
        super().__init__('icourse', headers, setting)

    def _crawlerForSingleCourseAndPage(self, course, page):
        payload = "kw={}&curPage={}".format(quote(course), page)
        response = requests.request("POST", url, headers=headers, data=payload)
        bs = BeautifulSoup(response.text, 'html.parser')
        for videoAddress in bs.find_all('a', {'class': 'icourse-desc-title'}):
            name = videoAddress.get_text()
            addr = videoAddress.attrs['href']
            addr = addr if "https:" in addr else "https:" + addr
            duration, plays, comments = self._getVideoInfos(addr)
            video = Video(name=name, platform=self.platform, duration=duration, course=course, plays=plays,
                          comments=comments, addr=addr)
            print('{}crawling {} for {} in {}\n addr is {}\npage is {}'.format(threading.current_thread().name, name,
                                                                               course, self.platform, addr, page))
            self.dataQueue.put(video)
        bs.clear()
        response.close()

    def __forPublicCourse(self, addr):
        import subprocess
        output = subprocess.check_output(['node', 'icourse.js', addr])
        bs = BeautifulSoup(output.decode('utf-8'), 'html.parser')
        hour = bs.find('span', {'class': 'hour', 'id': 'source-duration-hour'}).get_text()
        minute = bs.find('span', {'class': 'minute', 'id': 'source-duration-minute'}).get_text()
        duration = '{:.1f}'.format((int(hour) * 60 + int(minute)) / 60)
        comments = bs.find("span", {"class": "icourse-list-number-comment"}).get_text()
        plays = bs.find("span", {'class': "icourse-list-number"}).get_text()
        return duration, plays, comments

    def _getVideoInfos(self, addr):
        # duration,playCnt,commentCnt
        videoPage = requests.get(addr)
        # if 'videoDetail' in addr:
        #     return self.__forPublicCourse(addr)
        bs = BeautifulSoup(videoPage.text, 'html.parser')
        if 'icourse163.org' not in addr:
            desc = bs.find('div', {'class': 'course-information boxstyle'})
            if desc is None:
                duration = None
                comments = bs.find("span", {"class": "icourse-list-number-comment"}).get_text()
                plays = bs.find("span", {'class': "icourse-list-number"}).get_text()
            else:
                t = desc.find_all('p', {'class': 'course-information-suit pull-left'})
                duration = desc.find('p', {'class': 'course-information-hour pull-left'}).get_text()
                plays = t[-2].get_text()
                comments = t[-1].get_text()
        else:
            duration, plays = None, None
            comments = bs.find('span', {'id': 'review-tag-num'}).get_text()
        videoPage.close()
        return duration, plays, comments


icourseCrawler = IcourseCrawler()

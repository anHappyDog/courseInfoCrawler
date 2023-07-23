import re
import threading
from urllib.parse import quote

from bs4 import BeautifulSoup

from common import WebCrawler, Video

import requests

headers = {
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Origin': 'https://www.cnmooc.org',
    'Referer': 'https://www.cnmooc.org/portal/frontCourseIndex/course.mooc?keyWord=asd',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.82',
    'X-Requested-With': 'XMLHttpRequest',
    'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Microsoft Edge";v="114"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"'
}
payload = "keyWord={}&openFlag=0&fromType=&learningMode=0&certType=&languageId=&categoryId=&menuType=course&schoolId=&pageIndex={}&postoken="


class CnmoocCrawler(WebCrawler):
    def __init__(self, setting=None):
        if setting is None:
            setting = WebCrawler.CrawlerSetting()
        self.cookie = requests.get('https://www.cnmooc.org', headers=headers).cookies
        super().__init__('icourse163', headers, setting)

    def _crawlerForSingleCourseAndPage(self, course, page):
        payload = "keyWord={}&openFlag=0&fromType=&learningMode=0&certType=&languageId=&categoryId=&menuType=c" \
                  "ourse&schoolId=&pageIndex={}&postoken=" + self.cookie.get_dict()['cpstk']
        url = 'https://www.cnmooc.org/portal/ajaxCourseIndex.mooc'
        response = requests.request("POST", url, headers=headers, cookies=self.cookie,
                                    data=payload.format(quote(course), page))
        bs = BeautifulSoup(response.text, 'html.parser')
        for videoAddress in bs.find_all('li', {'class': 'view-item'}):
            try:
                name = re.sub(r'\s*', '',
                              videoAddress.find('a', {'class': 'link-default link-course-detail'}).get_text())
                addr = 'https://www.cnmooc.org' + videoAddress.find('div', {'class': 'view-img'}).attrs['href']
            except:
                print('page is %d ,course %s not found!' % (page, course))
                break
            try:
                plays = videoAddress.find('div', {'class': 'progressbar-text'}).find('em').get_text()
            except:
                plays = None
            coursePage = requests.get(addr, cookies=self.cookie, headers=headers)
            courseBs = BeautifulSoup(coursePage.text, 'html.parser')

            sideBar = courseBs.find('div', {'class': 'sidebar'})
            attrs = sideBar.find_all('p', {'class': 'panel-col substr'})
            try:
                weeks = int(re.findall(r'\d+', attrs[0].get_text())[0])
            except:
                weeks = 14
            try:
                hour = int(re.findall(r'\d+', attrs[1].get_text())[0])
            except:
                hour = 2
            duration = '{:.1f}'.format(weeks * hour)
            comments = None
            video = Video(name, self.platform, course, plays, comments, addr, duration)
            print('{}crawling {} for {} in {}\n addr is {}\npage is {}'.format(threading.current_thread().name, name,
                                                                               course, self.platform, addr, page))

            self.dataQueue.put(video)

        response.close()


cnmoocCrawler = CnmoocCrawler()

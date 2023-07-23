import re
import threading
from urllib.parse import quote

import requests

from common import WebCrawler, Video

headers = {
    'authority': 'www.icourse163.org',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'content-type': 'application/x-www-form-urlencoded',
    'origin': 'https://www.icourse163.org',

    'Accept-Encoding': 'gzip, deflate, br',
    'Accept': '*/*'}


class Icourse163Crawler(WebCrawler):
    def __init__(self, setting=None):
        if setting is None:
            setting = WebCrawler.CrawlerSetting()
        self.cookie = requests.get('https://www.icourse163.org/', headers=headers).cookies
        super().__init__('icourse163', headers, setting)

    def _crawlerForSingleCourseAndPage(self, course, page):
        payload = payload = 'mocCourseQueryVo=%7B%22keyword%22%3A%22{}%22%2C%22p' \
                            'ageIndex%22%3A{}%2C%22highlight%22%3Atrue%2C%22ord' \
                            'erBy%22%3A0%2C%22stats%22%3A30%2C%22pageSize%22%3A20%7D'.format(quote(course), page)
        url = 'https://www.icourse163.org/web/j/mocSearchBean.searchCourse.rpc?csrfKey=' + self.cookie.get_dict()[
            'NTESSTUDYSI']
        response = requests.request("POST", url, headers=headers, cookies=self.cookie, data=payload)
        videoList = response.json()['result']['list']
        for videoInfo in videoList:
            try:
                name = videoInfo['mocCourseCard']['highlightName']
            except:
                name = videoInfo['highlightName']
            name = re.sub(r'#|\{|}|','',name)
            try:
                courseId = videoInfo['mocCourseCard']['mocCourseCardDto']['id']
            except:
                courseId = videoInfo['courseId']
            try:
                shortName = videoInfo['mocCourseCard']['mocCourseCardDto']['schoolPanel']['shortName']
            except:
                shortName = None
            if shortName is not None:
                addr = 'https://www.icourse163.org/course/%s-%d' % (shortName, courseId)
            else:
                if videoInfo['mocCourseCard'] is not None:
                    termid = videoInfo['mocCourseCard']['termId']
                    addr = f'https://kaoyan.icourse163.org/course/terms/{termid}.htm?courseId={courseId}'
                else:
                    if videoInfo['mocCoursePackageKyCardBaseInfoDto'] is not None:
                        packageId = videoInfo['mocCoursePackageKyCardBaseInfoDto']['packageId']
                        addr = f'https://kaoyan.icourse163.org/course/packages/{packageId}.htm'
                    else:
                        continue
            try:
                comments = \
                    requests.post(
                        'https://www.icourse163.org/web/j/mocCourseV2RpcBean.getEvaluateAvgAndCount.rpc?csrfKey='
                        + self.cookie.get_dict()['NTESSTUDYSI'], cookies=self.cookie,
                        headers=headers, data='courseId=%d' % courseId).json()['result']['evaluateCount']
            except:
                print('course id %d' % courseId)
                comments = None
            plays, duration = None, None
            video = Video(name, 'icourse163', course, plays, comments, addr, duration)

            print('{}crawling {} for {} in {}\n addr is {}\npage is {}'.format(threading.current_thread().name, name,
                                                                               course, self.platform, addr, page))
            self.dataQueue.put(video)
        response.close()


icourse163Crawler = Icourse163Crawler()

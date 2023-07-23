import concurrent
import queue
import threading
import concurrent.futures

import pymysql
from pymysql import IntegrityError


class Video:
    # (name, platform, course, plays, comments, addr) = ('' for i in range(6))
    fixedPassTuple = "(name,platform,course,plays,comments,address,duration) VALUES ('%s','%s','%s','%s','%s','%s','%s')"

    def __init__(self, name, platform, course, plays, comments, addr, duration):
        (self.name, self.platform, self.course, self.plays, self.comments, self.addr, self.duration) = (
            name, platform, course, plays, comments, addr, duration)

    def __str__(self):
        print('-' * 30)
        print(f"name:{self.name}\nplatform:{self.platform}")
        print(f"course:{self.course}\nplays:{self.plays}\ncomments:{self.comments}")
        print(f"addr:{self.addr}")
        print('-' * 30)

    def __iter__(self):
        yield self.name
        yield self.platform
        yield self.course
        yield self.plays
        yield self.comments
        yield self.addr
        yield self.duration

    def passSqlValues(self):
        return self.name, self.platform, self.course, self.plays, self.comments, self.addr, self.duration


class DatabaseInfo:
    def __init__(self, user, password, host, database=None, table=None):
        self.user = user
        self.password = password
        self.host = host
        self.database = database
        self.table = table

    def __iter__(self):
        yield self.user
        yield self.password
        yield self.host
        if self.database is not None:
            yield self.database
        if self.table is not None:
            yield self.table


courseDatabase = DatabaseInfo('root', 'ilikeyou2003', '127.0.0.1', 'test1', 't2')


class WebCrawler:
    class CrawlerSetting:
        defaultCourseList = ['操作系统', '编译', '程序设计', '数据结构与算法', '计算机组成', '数据库', '软件工程',
                             '计算机网络']

        # defaultCourseList = ['操作系统']
        def __init__(self, courseList=None, maxPages=5, dbInfo=courseDatabase):
            self.courseList = self.defaultCourseList.copy() if courseList is None else courseList
            self.maxPages = maxPages
            self.dbInfo = dbInfo

        def __str__(self):
            print("\t" + "/" * 30)
            print('\tcourseList:' + self.courseList)
            print(f"\tmaxPages:{self.maxPages}")
            print("\t" + "/" * 30)

        def __iter__(self):
            yield self.courseList
            yield self.maxPages
            yield self.dbInfo

    def __init__(self, platform, headers, setting):
        self.platform = platform
        self.headers = headers
        self.setting = setting
        self.dataQueue = queue.Queue()

    def __str__(self):
        print('*' * 30)
        print(f"platform:{self.platform}")
        print("settings:\n" + self.setting)
        print('*' * 30)

    def crawler(self):
        threads = []
        user, password, host, db, table = self.setting.dbInfo
        conn = pymysql.connect(user=user, password=password, database=db, host=host)
        sender = threading.Thread(target=self._sendDataToSql,args=(conn,))
        sender.start()
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            for course in self.setting.courseList:
                for i in range(1, self.setting.maxPages + 1):
                    threads.append(executor.submit(self._crawlerForSingleCourseAndPage,course,i))
                    # threads.append(threading.Thread(target=self._crawlerForSingleCourseAndPage, args=(course, i)))
                    # threads[-1].start()
            concurrent.futures.wait(threads)
        self.dataQueue.put(None)
        sender.join()
        conn.close()


    def _getVideoInfos(self, addr):
        # duration,playCnt,commentCnt
        return None, None, None

    def _crawlerForSingleCourseAndPage(self, course, page):
        raise NotImplementedError('Not implemented')

    def _sendDataToSql(self, conn):
        (t1, t2, t3, t4, table) = self.setting.dbInfo
        while True:
            data = self.dataQueue.get()
            if data is None:
                return
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO {}".format(table) + Video.fixedPassTuple
                        % data.passSqlValues())
                    cur.connection.commit()
            except IntegrityError as e:
                continue

爬取计课相关课程在一些网站的信息。支持平台有(imooc,icourse163,icourse,bilibili,cnmooc等)。用法为引入crawler.py中的Crawler，使用静态方法crawler爬取。同时爬取的设置（爬取搜索的页数，爬取的课程,存放的mysql数据库，最大线程数等）在common.py中WebCrawler中__init__设置（时间所限没在Crawler里封装实现了）

# -*- coding: utf-8 -*-
from . import config
from . import define
import pixivpy3
import time
import datetime
import os
from PIL import Image
from .db import dbconnect, dbclose, dbinsert, dbifhave
from apscheduler.schedulers.background import BackgroundScheduler
from threading import Lock, Thread
from .logger import logger

lock = Lock()  # 线程锁，只执行一个下载线程
downloading = False  # 判断是否正在下载


# 登录Pixiv
def apiLogin() -> pixivpy3.ByPassSniApi:
    logger.info("尝试登录gPixiv")
    api = pixivpy3.ByPassSniApi()
    api.require_appapi_hosts()
    api.set_accept_language('en-us')
    if config.PIXIV_USERNAME != "username" and config.PIXIV_PASSWORD != "password":
        api.login(config.PIXIV_USERNAME, config.PIXIV_PASSWORD)
        logger.info("Pixiv登录成功")
    else:
        raise Exception("请在config.py文件中设置账号密码")
    return api


# 根据类型获取排行榜信息
def apiRanking(api: pixivpy3.ByPassSniApi, t: str) -> list:
    logger.info("尝试获取 " + t + " 排行榜信息")
    json_result = api.illust_ranking(mode=t)
    rt = []
    for json_item in json_result.illusts:
        if json_item.type != 'illust':
            continue
        illust = json_item.id
        title = json_item.title
        count = json_item.page_count
        if count == 1:
            url = [json_item.meta_single_page.original_image_url]
        else:
            url = [i.image_urls.original for i in json_item.meta_pages]
        tags = [i.name for i in json_item.tags]
        temp = {"illust": illust, "title": title,
                "count": count, "tags": tags, "url": url, "suffix": url[0].split('.')[-1]}
        logger.debug(temp)
        rt.append(temp)
    logger.info(t + " 排行榜信息获取完成")
    return rt


# 判断图片完整性
def isValidImage(pathfile):
    bValid = True
    try:
        Image.open(pathfile).verify()
    except:
        bValid = False
    return bValid


# 图片下载并创建缩略图
def apiDownload(api: pixivpy3.ByPassSniApi, item: dict) -> None:
    # item = {"illust": illust, "title": title,
    #         "count": count, "tags": tags, "url": url, "suffix": suffix}
    logger.info("尝试下载 " + str(item['illust']) + ':' + item['title'])
    # 检测PATH是否存在，不存在则创建
    # 当日图片根文件夹
    basePath = os.path.join(define.STATICPATH, config.IMGPATH)
    # 存放原图的文件夹，按时间分类好
    localtime = time.localtime()
    origPath = os.path.join(basePath, "orig", str(localtime.tm_year).zfill(
        4), str(localtime.tm_mon).zfill(2), str(localtime.tm_mday).zfill(2))
    # 存放缩略图的文件夹
    thumPath = os.path.join(basePath, "thum")
    if not os.path.exists(origPath):
        logger.debug("创建路径 " + origPath)
        os.makedirs(origPath)
    if not os.path.exists(thumPath):
        logger.debug("创建路径 " + thumPath)
        os.makedirs(thumPath)
    # 遍历下载
    for i in range(item['count']):
        if config.USECAT:  # 判断是否使用代理镜像站下载
            url = item['url'][i].replace("i.pximg.net", define.PIXIVCAT)
        else:
            url = item['url'][i]
        name = str(item['illust']) + "-" + str(i) + "." + item['suffix']
        logger.debug("下载orig " + name)
        origName = os.path.join(origPath, name)
        if not (os.path.exists(origName) and isValidImage(origName)):  # 若图片不完整则下载
            api.download(url, path=origPath, name=name, replace=True)  # 下载器
        # 封面创建缩略图
        thumName = os.path.join(thumPath, str(item['illust']) + '.png')
        if i == 0 and not (os.path.exists(thumName) and isValidImage(thumName)):
            logger.debug("创建thum " + str(item['illust']))
            img = Image.open(os.path.join(origPath, name))
            width = img.size[0]  # 获取宽度
            height = img.size[1]  # 获取高度
            if 1.3*width < height:
                x0 = int(0)
                y0 = int((height-1.3*width)/2)
                x1 = int(width)
                y1 = int(y0+1.3*width)
            elif 1.3*width > height:
                x0 = (width-height/1.3)/2
                y0 = int(0)
                x1 = int(x0+height/1.3)
                y1 = int(height)
            img = img.crop((x0, y0, x1, y1))
            img = img.resize((192, 250), Image.ANTIALIAS)  # 按比例缩放，高度固定为250px
            img.save(thumName)
        time.sleep(3)  # 延时3s，防止下载过快卡死
    logger.info("下载完成 " + str(item['illust']) + ':' + item['title'])


def pixiv() -> None:
    global downloading
    lock.acquire()
    downloading = True
    logger.info("Pixiv下载模块已启动")
    try:
        api = apiLogin()
    except:
        logger.error("Pixiv登录失败，请检查账号密码")
        return
    items = {}
    for t in config.CHOICEMODE:
        try:
            items[t] = apiRanking(api, t)  # 获取t类型排行榜列表
        except:
            logger.error("获取" + t + "类型排行榜失败")
            # 获取失败，尝试下一类型
            continue
        for item in items[t]:
            # 超过设定值不下载
            if config.MAXCOUNT and item['count'] > config.MAXCOUNT:
                logger.debug("count超过设定值" + str(config.MAXCOUNT) +
                             " " + str(item['illust']) + ":" + item['title'])
                continue
            try:
                conn = dbconnect()
                if not dbifhave(conn, "illustJsonMsg", item["illust"]):
                    # 下载到本地
                    apiDownload(api, item)
                    # 下载完成，写入数据库
                    dbinsert(conn, t, item["illust"], item)
                dbclose(conn)
            except:
                logger.error(
                    "下载失败 " + str(item['illust']) + ":" + item['title'])
    logger.info("Pixiv下载模块已关闭")
    downloading = False
    lock.release()


# 将pixiv()加入后台计划任务
def pixivCron() -> None:
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=pixiv, trigger='cron', **config.APSTIME)
    scheduler.start()
    dt = datetime.datetime.now()
    (h, m, s) = (dt.hour, dt.minute, dt.second)
    if datetime.time(**config.APSTIME) <= datetime.time(**{"hour": h, "minute": m, "second": s}):
        t = Thread(target=pixiv)
        t.start()


if __name__ == "__main__":
    pixivCron()
    import os
    os.system("pause>nul")

# -*- coding: utf-8 -*-
import os
from .logger import logger
from . import config
from . import define


def delete(data: dict = {}, all: bool = False):
    if not data and all:
        # 删除全部
        logger.info("尝试删除全部")
        try:
            os.removedirs(os.path.join(define.STATICPATH, config.IMGPATH))
            logger.info("删除全部 - 完成")
        except:
            logger.error("删除全部 - 失败")
    elif data:
        logger.info("尝试删除指定文件")
        basePath = os.path.join(define.STATICPATH, config.IMGPATH)
        thumPath = os.path.join(basePath, "thum")
        try:
            for key in data:
                stime = str(key)
                yea = stime[:4]
                mon = stime[4:6]
                day = stime[6:8]
                origPath = os.path.join(basePath, "orig", yea, mon, day)
                items = data[key]
                for item in items:
                    thumname = os.path.join(thumPath, str(item['illust']) + ".png")
                    if os.path.exists(thumname):
                        os.remove(thumname)
                    for i in range(item['count']):
                        filename = os.path.join(origPath, str(
                            item['illust']) + "-" + str(i) + "." + item['suffix'])
                        if os.path.exists(filename):
                            os.remove(filename)
            logger.info("删除成功")
        except:
            logger.error("删除失败 - " + str(data))

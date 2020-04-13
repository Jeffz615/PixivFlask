# -*- coding: utf-8 -*-
from src import pixiv
from src import route
from src import config

if __name__ == "__main__":
    pixiv.pixivCron()  # 启用定时下载器
    route.app.run(config.HOST, config.PORT, debug=config.DEBUG)  # 开启网页服务器

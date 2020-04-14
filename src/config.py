# -*- coding: utf-8 -*-

from . import define
from os import path, makedirs
import logging


# 服务器设置
PORT = 5555
HOST = "0.0.0.0"
DEBUG = False
ALLOW_HOSTS = ["127.0.0.1:5555", "localhost:5555"]

# 日志文件
LOGON = True
LOGFILE = path.join(define.PATHDIR, "PixivFlask.log")
LOGLEVEL = logging.WARNING

# 图片存放位置
# 与static文件夹的相对路径
# 请确保在static文件夹内，否则无法访问
IMGPATH = "img"

# 系统管理员密码
FLASK_PASSWORD = "passwd"

# pixiv账号密码
PIXIV_USERNAME = "username"
PIXIV_PASSWORD = "password"

# 是否启用代理图床站(pixiv.cat)
USECAT = True

# 排行榜每日下载时间设置
# P站排行榜刷新时间为日本的中午12:00，即北京时间上午11:00
APSTIME = {"hour": 12, "minute": 0}

# 选择下载的类型
# MODELIST = ["day", "week", "month", "day_male", "day_female",
#             "week_original", "week_rookie", "day_manga", "day_r18", "day_male_r18",
#             "day_female_r18", "week_r18", "week_r18g"]
CHOICEMODE = ["day"]

# COUNT阈值，合集中超过多少张不下载，0为无限制
MAXCOUNT = 3

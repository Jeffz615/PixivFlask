# -*- coding: utf-8 -*-
import logging
import sys
from . import config

# 日志记录器
logger = logging.getLogger('PixivFlask')
logger.setLevel(config.LOGLEVEL)
while logger.hasHandlers():
    for i in logger.handlers:
        logger.removeHandler(i)
if config.LOGON:
    formatter = logging.Formatter('[ %(levelname)s ] : %(asctime)s - %(message)s')
    fh = logging.FileHandler(config.LOGFILE, encoding='utf-8')
    fh.setLevel(config.LOGLEVEL)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
formatter = logging.Formatter('%(message)s')
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(config.LOGLEVEL)
logger.addHandler(ch)

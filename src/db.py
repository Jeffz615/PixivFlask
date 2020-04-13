# -*- coding: utf-8 -*-
import sqlite3
import time
from . import define
from .logger import logger
import os
import logging
import json


DBFILE = os.path.join(define.PATHDIR, 'db.sqlite3')


# 检测是否为合法输入
def checkTable(t: str) -> bool:
    if t in define.MODELIST or t == "illustJsonMsg":
        return True
    logger.error("checkTable检测到非法输入 " + t)
    return False


# 连接数据库
def dbconnect() -> sqlite3.Connection:
    conn = sqlite3.connect(DBFILE)
    logger.info("打开数据库成功")
    if not conn.execute("SELECT COUNT(*) FROM sqlite_master where type='table' and name='illustJsonMsg';").fetchall()[0][0]:
        logger.info("正在创建数据表")
        create_tb_cmd = '''
        CREATE TABLE IF NOT EXISTS illustJsonMsg
        (`illust` INTEGER NOT NULL PRIMARY KEY,
	     `time` INTEGER,
	     `json` JSON);
        '''
        conn.execute(create_tb_cmd)
        create_index_cmd = '''
        CREATE UNIQUE INDEX `index_illust` on `illustJsonMsg` (`illust`,`time`);
        '''
        conn.execute(create_index_cmd)
        for t in define.MODELIST:
            create_tb_cmd = '''
            CREATE TABLE IF NOT EXISTS ''' + t + '''
            (`illust` INTEGER NOT NULL PRIMARY KEY);
            '''
            conn.execute(create_tb_cmd)
        conn.commit()
        logger.info("数据表创建完成")
    return conn


# 关闭数据库
def dbclose(conn: sqlite3.Connection) -> None:
    conn.close()
    logger.info("关闭数据库成功")


# 判断表中是否存在指定illust
def dbifhave(conn: sqlite3.Connection, table: str, illust: int) -> bool:
    sql = 'select `illust` from `' + table + \
        '` where `illust`=' + str(illust) + ';'
    logger.debug(sql)
    if checkTable(table) and conn.execute(sql).fetchall():
        return True
    else:
        return False


# 插入元素(增)
def dbinsert(conn: sqlite3.Connection, mode: str, illust: int, item: dict) -> None:
    logger.info("正在写入数据库 " + str(illust))
    item.pop('url')  # 已下载到本地，不需要url
    if not dbifhave(conn, "illustJsonMsg", illust):
        tmp = time.localtime()
        timeint = tmp.tm_year*10000 + tmp.tm_mon*100 + tmp.tm_mday
        insert_dt_cmd = 'insert into `illustJsonMsg` values (' + str(
            illust) + ',' + str(timeint) + ',\'' + json.dumps(item) + '\');'
        logger.debug(insert_dt_cmd)
        conn.execute(insert_dt_cmd)
        conn.commit()
    if not dbifhave(conn, mode, illust):
        insert_dt_cmd = 'insert into `' + mode + \
            '` (`illust`) values (' + str(illust) + ');'
        logger.debug(insert_dt_cmd)
        conn.execute(insert_dt_cmd)
        conn.commit()


# 抛弃单个元素(删)
def dbdropitem(conn: sqlite3.Connection, illust: int) -> None:
    logger.info("尝试删除" + str(illust))
    drop_sql = 'update `illustJsonMsg` set `time`=-1 where `illust`="' + \
        str(illust) + '";'
    conn.execute(drop_sql)
    conn.commit()
    logger.info("删除" + str(illust) + "成功")


# 抛弃全部元素(删)
def dbdropall(conn: sqlite3.Connection) -> None:
    logger.info("尝试删除全部")
    drop_sql = 'update `illustJsonMsg` set `time`=-1 where `time`!=-1;'
    conn.execute(drop_sql)
    conn.commit()
    logger.info("删除全部成功")


# 抛弃指定类型的全部元素(删)
def dbdropmode(conn: sqlite3.Connection, typelist: list) -> None:
    logger.info("尝试删除指定类型" + str(typelist))
    for mode in typelist:
        if mode not in define.MODELIST:
            return
        drop_sql = '''
            update `illustJsonMsg` set `time`=-1 where `illust` in 
            (select `illust` from ''' + mode + ''') and `time`!=-1;
            '''
        conn.execute(drop_sql)
    conn.commit
    logger.info("删除指定类型成功" + str(typelist))


# 时间列表(查)
def dbgettimelist(conn: sqlite3.Connection) -> list:
    logger.info("查询时间列表")
    get_time_list_sql = 'select distinct `time` from `illustJsonMsg` where `time`!=-1 order by `time` desc;'
    temp = conn.execute(get_time_list_sql).fetchall()
    timelist = [temp[i][0] for i in range(len(temp))]
    logger.info(str(timelist))
    return timelist


# 指定时间和类型的元素列表(查)
def dbgetitems(conn: sqlite3.Connection,  typelist: list, time: int = 0) -> list:
    logger.info("查询元素列表")
    logger.info("时间 : " + str(time))
    logger.info("类型 : " + str(typelist))
    imgs_sql = 'select `time`,`json` from `illustJsonMsg` where `illust` in ('
    ifUnion = False
    for t in typelist:
        if t not in define.MODELIST:
            continue
        if ifUnion:
            imgs_sql += ' union '
        imgs_sql += 'select `illust` from ' + t
        ifUnion = True
    if time == 0:
        imgs_sql += ') and `time`!=-1 order by `illust` desc;'
    elif time == -1:
        time = dbgettimelist(conn)[0]
        imgs_sql += ') and `time`=' + str(time) + ' order by `illust` desc;'
    else:
        imgs_sql += ') and `time`=' + str(time) + ' order by `illust` desc;'
    rt = conn.execute(imgs_sql).fetchall()
    rtjson = {}
    for i in rt:
        if i[0] not in rtjson.keys():
            rtjson[i[0]] = []
        rtjson[i[0]].append(json.loads(i[1]))
    logger.info(str(rtjson))
    return rtjson


# 查询指定元素(查)
def dbgetillust(conn: sqlite3.Connection, illust: int) -> dict:
    logger.info("查询元素 " + str(illust))
    get_illust_sql = 'select `time`,`json` from `illustJsonMsg` where `illust`=' + \
        str(illust) + ' and `time`!=-1;'
    rt = conn.execute(get_illust_sql).fetchall()
    if rt:
        j = json.loads(rt[0][1])
    else:
        raise Exception('查询结果为空。')
    rt = {"time": rt[0][0], "detail": j}
    logger.info(str(rt))
    return rt

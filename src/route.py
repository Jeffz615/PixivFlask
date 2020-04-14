# -*- coding: utf-8 -*-
from flask import Flask, jsonify, render_template, request, Response, send_from_directory, abort
from . import define
from . import db
import os
from . import config
from . import pixiv
import json
from . import rsaUnit
from . import deleteUnit
from .logger import logger


app = Flask(__name__, static_folder=define.STATICPATH,
            template_folder=os.path.join(define.PATHDIR, 'templates'))
RSA = rsaUnit.myRSA()


@app.before_request
def checkHosts():
    if request.host not in config.ALLOW_HOSTS:
        abort(404)


# 首页
@app.route("/")
def index():
    return render_template("index.html")


# 登录页面
@app.route("/login")
def loginPage():
    return render_template("login.html")


def rtMsg(errno: int, data: any = None, wantDict: bool = False):  # API返回的格式
    switch = {  # 定义错误码
        0: "Success!",  # 正常返回
        1: "Illegal input!",  # 非法输入
        2: "Database error! Please contact the webmaster.",  # 数据库错误
        3: "Template error! Please contact the webmaster.",  # 模板错误
        4: "RSA module failure! Please contact the webmaster.",  # RSA模块失效
        5: "Password error.",  # 密码错误
        6: "Not logged in. Please Login."  # 未登录
    }
    if wantDict:
        return {"errno": errno, "msg": switch[errno], "data": data}
    return jsonify({"errno": errno, "msg": switch[errno], "data": data})


# 下载器状态
@app.route("/api/status", methods=['GET'])
def apiStatus():
    return rtMsg(0, pixiv.downloading)


# 时间列表
@app.route("/api/time", methods=['GET'])
def apiTime():
    try:
        conn = db.dbconnect()
        data = db.dbgettimelist(conn)
        db.dbclose(conn)
        return rtMsg(0, data)
    except:
        return rtMsg(2)

# 获取元素
@app.route("/api/items", methods=['GET', 'POST'])
def apiItems():
    if request.method == 'GET':
        illust = request.args.get('illust', '')
        if illust and len(illust) < 10 and illust.isnumeric():
            try:
                conn = db.dbconnect()
                data = db.dbgetillust(conn, illust)
                db.dbclose(conn)
                return rtMsg(0, data)
            except:
                return rtMsg(2)  # 数据库查询错误或不存在此元素
        return rtMsg(1)  # 未过检测，非法输入
    elif request.method == 'POST':
        j = request.get_json()
        typelist = j.get('typelist')
        time = j.get('time')
        category = str(j.get('category')).upper()
        # 无指明typelist则根据category赋值
        if not typelist and category in ['R18', 'NORMAL', 'ALL']:
            switch = {
                'R18': define.R18MODE,
                'NORMAL': define.NORMALMODE,
                'ALL': define.MODELIST
            }
            typelist = switch[category]
        elif not typelist or type(typelist) != list:
            return rtMsg(1)  # 无指明类型，或输入数据不是列表，非法输入
        if not(type(time) == int and time < 10**10 and time >= 0):  # 0代表全部，-1代表最后一天
            time = -1  # 非法输入或不输入则默认为最后一天
        for t in typelist:
            if t not in define.MODELIST:
                return rtMsg(1)  # 存在不在modelist中的类型，非法输入
        # 输入信息过滤完毕，查询数据库
        try:
            conn = db.dbconnect()
            data = db.dbgetitems(conn, typelist, time)
            db.dbclose(conn)
            return rtMsg(0, data)
        except:
            return rtMsg(2)  # 数据库查询错误


# 登录功能
@app.route("/api/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        # 分发公钥
        try:
            (keyno, publickey) = RSA.getkeys()
            return rtMsg(0, {"keyno": keyno, "key": publickey.decode('utf-8')})
        except:
            return rtMsg(4)  # RSA模块失效
    elif request.method == 'POST':
        j = request.get_json()
        keyno = j.get("keyno")
        print(type(keyno), keyno)
        password = j.get("password")
        print(type(password), password)
        if not (type(keyno) == int and keyno in [0, 1, 2]) or not (type(password) == str):
            return rtMsg(1)  # 非法输入
        (password, err) = RSA.getplain(keyno, password)
        if err and password == config.FLASK_PASSWORD:
            # 密码正确
            logger.info("密码正确，登录成功。")
            response = Response(json.dumps(
                rtMsg(0, wantDict=True)), content_type='application/json')
            # 登录成功，颁发cookies证书
            response.set_cookie("AuthCert", RSA.generateCert())
            logger.debug("AuthCert : " + RSA.AuthCert)
            return response
        else:
            logger.info("密码错误，登录失败。")
            return rtMsg(5)  # 密码错误


# 验证登录是否有效
@app.route("/api/verification", methods=['GET', 'POST'])
def verification():
    AuthCert = request.cookies.get("AuthCert")
    if RSA.Used and AuthCert == RSA.AuthCert:
        return rtMsg(0)  # 登录成功，返回正常信息
    else:
        return rtMsg(6)  # 未登录


# 注销cookies证书
@app.route("/api/logout", methods=['GET', 'POST'])
def logout():
    AuthCert = request.cookies.get("AuthCert")
    if RSA.Used and AuthCert == RSA.AuthCert:
        RSA.Used = False  # 清除登录证书
        return rtMsg(0)  # 登录成功，返回正常信息
    else:
        return rtMsg(6)  # 未登录


# 删除功能
@app.route("/api/delete", methods=['POST'])
def delete():
    AuthCert = request.cookies.get("AuthCert")
    if RSA.Used and AuthCert == RSA.AuthCert:
        j = request.get_json()
        t = j.get("type")
        if t == 0:  # 删除单个元素
            illust = j.get("illust")
            if type(illust) == int and illust < 10**10 and illust > 0:
                try:
                    conn = db.dbconnect()
                    data = db.dbgetillust(conn, illust)
                    db.dbdropitem(conn, illust)  # 先删数据库
                    db.dbclose(conn)
                    deleteUnit.delete({data['time']: [data['detail']]})  # 再删文件
                except:
                    return rtMsg(2)  # 数据库错误
            else:
                return rtMsg(1)  # 非法输入
        elif t == 1:  # 删除指定类型元素
            typelist = j.get("typelist")
            category = str(j.get('category')).upper()
            if not typelist and category in ['R18', 'NORMAL', 'ALL']:
                switch = {
                    'R18': define.R18MODE,
                    'NORMAL': define.NORMALMODE,
                    'ALL': define.MODELIST
                }
                typelist = switch[category]
            elif not typelist or type(typelist) != list:
                return rtMsg(1)  # 无指明类型，或输入数据不是列表，非法输入
            for t in typelist:
                if t not in define.MODELIST:
                    return rtMsg(1)  # 存在不在modelist中的类型，非法输入
            try:
                conn = db.dbconnect()
                data = db.dbgetitems(conn, typelist)
                db.dbdropmode(conn, typelist)
                db.dbclose(conn)
                deleteUnit.delete(data)
            except:
                return rtMsg(2)  # 数据库错误
        elif t == 2 and not pixiv.downloading:  # 删除全部元素，下载时不能删除全部文件
            try:
                conn = db.dbconnect()
                db.dbdropall(conn)
                db.dbclose(conn)
                deleteUnit.delete(all=True)
            except:
                return rtMsg(2)  # 数据库错误
        else:
            return rtMsg(1)  # 非法输入
        return rtMsg(0)  # 登录成功，返回正常信息
    else:
        return rtMsg(6)  # 未登录

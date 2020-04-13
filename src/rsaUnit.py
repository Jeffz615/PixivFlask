# -*- coding: utf-8 -*-
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5
from Crypto import Random
import base64
from threading import Lock
from .logger import logger
import random
import time


# 生成一个指定长度的随机字符串
def generate_random_str(randomlength=64):
    random_str = ''
    base_str = 'ABCDEFGHIGKLMNOPQRSTUVWXYZabcdefghigklmnopqrstuvwxyz0123456789'
    length = len(base_str) - 1
    for _ in range(randomlength):
        random_str += base_str[random.randint(0, length)]
    return random_str


class myRSA:
    __lock = Lock()
    __keys = {}
    __count = -1
    __RANDOM_GENERATOR = Random.new().read
    AuthCert = ""
    __CertTime = 0  # 创建时间（1天有效期）
    Used = False  # 证书已创建的标记

    def __init__(self):
        self.__scheduler = BackgroundScheduler()
        # 5分钟创建一个公私钥对，10分钟内有效
        self.__scheduler.add_job(
            func=self.newkeys, trigger='interval', minutes=5)
        self.newkeys()
        self.__scheduler.start()

    def newkeys(self):
        logger.info("创建公私钥对")
        rsa = RSA.generate(1024, self.__RANDOM_GENERATOR)
        self.__PRIVATE_PEM = rsa.exportKey()
        logger.debug(str(self.__PRIVATE_PEM))
        self.__PUBLIC_PEM = rsa.publickey().exportKey()
        logger.debug(str(self.__PUBLIC_PEM))
        self.__lock.acquire()  # 线程加锁
        if (self.__count+2) % 3 in self.__keys.keys():  # 清除过期密钥
            self.__keys.pop((self.__count+2) % 3)
            logger.debug("清除过期密钥")
        self.__count = (self.__count+1) % 3
        self.__keys[self.__count] = (
            self.__PRIVATE_PEM, self.__PUBLIC_PEM)  # 将密钥加入记录
        self.__lock.release()  # 线程解锁
        if self.Used:  # 如果证书被使用，验证证书保留6h，过时重新登陆
            nowtime = time.time()
            if nowtime-self.__CertTime > 21600:
                self.Used = False
                self.AuthCert = ""
                self.__CertTime = 0

    def getkeys(self) -> (int, bytes):
        logger.info("发放公钥")
        return (self.__count, self.__PUBLIC_PEM)

    def getplain(self, keysno: int, cipher: str) -> (str, bool):
        logger.info("尝试解密")
        self.__lock.acquire()  # 阻塞线程
        if keysno not in self.__keys.keys():
            self.__lock.release()  # 解锁
            logger.error("找不到keyno")
            return ('', False)
        key = self.__keys[keysno][0]
        self.__lock.release()  # 解锁
        rsakey = RSA.importKey(key)
        cipheror = Cipher_pkcs1_v1_5.new(rsakey)
        try:
            plain = cipheror.decrypt(base64.b64decode(
                cipher), self.__RANDOM_GENERATOR)
            return (plain.decode('utf-8'), True)
        except:
            logger.error("解密失败")
            return ('', False)
        logger.info("解密成功")

    def generateCert(self) -> str:  # 生成验证证书
        self.AuthCert = generate_random_str()
        self.Used = True
        self.__CertTime = time.time()
        return self.AuthCert

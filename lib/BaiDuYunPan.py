#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: Chaobo Ren
# @Date:   2022/7/18 9:07
# @Last Modified by:   Ming
# @Last Modified time: 2022/7/18 9:07
import hashlib
import json
import logging
import sys
from pathlib import Path
from urllib.parse import urlencode

import requests

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

BASEPATH = Path(__file__).absolute()
# 百度云API
sys.path.append(str(BASEPATH))
import openapi_client
from openapi_client.api import userinfo_api
from openapi_client.api import fileupload_api


class BDYP(object):
    """
    百度网盘API的进一步封装
    """

    def __init__(self, thread=4, ssl_check=True):
        """
        初始化百度网盘对象
        """
        # 一些基本信息
        self._client_id = "EyUURtW1VbHkibk4nGGOUk4c7B9Nxnse"
        self._redirect_uri = "oob"
        self._device_id = "26708729"
        self._SecretKey = "w88HIgI8u7bR4gFNwcdjgvuBxDbKBPTL"

        # 会话信息
        configuration = openapi_client.configuration.Configuration.get_default_copy()
        if ssl_check is False:
            configuration.verify_ssl = False
        self.client = openapi_client.ApiClient(configuration=configuration, pool_threads=thread)

        # step
        self._f_token = Path.home().joinpath(".BDY.json")
        self.login()
        self.quote()

    def login(self):
        """
        登陆网盘
        """
        if self._f_token.exists():
            self._parse_token_file()
        else:
            self._authorize()
            self._code2token()

    def _authorize(self):
        """
        获取授权码
        """
        url = "http://openapi.baidu.com/oauth/2.0/authorize?"
        param = {"response_type": "code",
                 "client_id": self._client_id,
                 "redirect_uri": self._redirect_uri,
                 "scope": "basic netdisk",
                 "device_id": self._device_id}
        full_url = f"{url}{urlencode(param)}"
        logging.info(f"Open the URL: {full_url}")
        self._authorize_code = input(f"Parse the Authorization Code here within 10 minutes: ")

    def _code2token(self):
        """
        通过授权码获取Access Token
        """
        url = "https://openapi.baidu.com/oauth/2.0/token?"
        param = {"grant_type": "authorization_code",
                 "code": self._authorize_code,
                 "client_id": self._client_id,
                 "client_secret": self._SecretKey,
                 "redirect_uri": self._redirect_uri}
        res = requests.get(f"{url}{urlencode(param)}")
        logging.debug(res.text)
        self._token = json.loads(res.text)["access_token"]
        logging.info(f"Save the token info to {self._f_token}")
        with open(self._f_token, 'w') as OUT:
            print(res.text, file=OUT)

    def _parse_token_file(self):
        """
        解析储存授权信息的文件
        """
        logging.info(f"Parse the token from file: {self._f_token}")
        self._token = json.load(open(self._f_token))["access_token"]

    def quote(self):
        """
        获取用户信息
        """
        api_instance = userinfo_api.UserinfoApi(self.client)

        try:
            userinfo = api_instance.xpannasuinfo(self._token)
            logging.info(f"用户名：{userinfo['baidu_name']}")
            logging.info(f"授权状态：{userinfo['errmsg']}")
        except openapi_client.ApiException as e:
            logging.error(f"Can not get user info: {e}")
            sys.exit(-1)

    def upload(self, local, remote):
        """
        上传文件

        TODO: 1. 添加切片上传的支持

        :param local: 本地文件路径
        :param remote: 远程文件路径
        """
        local = Path(local).absolute()
        handle = open(local, 'rb')
        f_size = local.stat().st_size
        f_md5 = f"[\"{hashlib.md5(open(local, 'rb').read()).hexdigest()}\"]"
        remote = f"/apps/BDY/{remote}"
        logging.debug(f_md5)

        obj = fileupload_api.FileuploadApi(self.client)
        # 预上传
        try:
            precreate_response = obj.xpanfileprecreate(self._token, remote, 0, f_size, 1, f_md5, rtype=3)
            logging.debug(precreate_response)
        except openapi_client.ApiException as e:
            logging.error(f"Pre Create err: {e}")

        # 上传
        try:
            upload_response = obj.pcssuperfile2(self._token, '0', remote, precreate_response['uploadid'], "tmpfile",
                                                file=handle)
            logging.debug(upload_response)
        except openapi_client.ApiException as e:
            logging.error(f"Upload file err:{e}")
            exit(-1)

        # 创建
        try:
            create_response = obj.xpanfilecreate(self._token, remote, 0, f_size, precreate_response['uploadid'], f_md5,
                                                 rtype=3)
            logging.debug(create_response)
        except openapi_client.ApiException as e:
            logging.error(f"Creat file err: {e}")

    def upload_single_force(self, local, remote):
        """
        利用目前 Python API 的 Bug, 即使文件的大小超过2G，如果不考虑接口返回的状态码，依旧可以不分片成功上传(不一定什么时候就没有了)

        :param local: 本地文件路径
        :param remote: 远程文件路径
        """
        local = Path(local).absolute()
        handle = open(local, 'rb')
        f_size = local.stat().st_size
        f_md5 = f"[\"{hashlib.md5(open(local, 'rb').read()).hexdigest()}\"]"
        remote = f"/apps/BDY/{remote}"
        logging.debug(f_md5)

        obj = fileupload_api.FileuploadApi(self.client)
        # 预上传
        try:
            precreate_response = obj.xpanfileprecreate(self._token, remote, 0, f_size, 1, f_md5, rtype=3,
                                                       async_req=True).get()
            logging.debug(precreate_response)
        except BaseException as e:
            logging.error(f"预上传错误: {e}")
            exit(-1)

        # 上传
        # try:
        try:
            upload_response = obj.pcssuperfile2(self._token, '0', remote, precreate_response['uploadid'], "tmpfile",
                                                file=handle, async_req=True).get()
            logging.debug(upload_response)
        except BaseException as e:
            logging.debug("上传错误")
        # except BaseException as e:
        #     logging.error(f"Upload has err: {e}, you result may have some problem")
        # if 'string longer than 2147483647 bytes' in str(e):
        #     logging.warning(e)
        # else:
        #     logging.error(f"Upload file err:{e}")
        #     exit(-1)

        # 创建
        try:
            create_response = obj.xpanfilecreate(self._token, remote, 0, f_size, precreate_response['uploadid'], f_md5,
                                                 rtype=3, async_req=True).get()
            logging.debug(create_response)
        except BaseException as e:
            logging.error(f"创建文件错误: {e}")
            exit(-1)

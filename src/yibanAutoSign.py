from base64 import b64encode
import math
import random
import re
import time
from serverChan import ServerChan
from userData import user_data

try:
    import requests
    from requests.exceptions import RequestException
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import PKCS1_v1_5
except ModuleNotFoundError:
    print("缺少依赖! 请安装依赖！")

DEBUG = False


def get_csrf_token():
    def token():
        a = math.floor(65536 * (1 + random.random()))
        return f'{a:x}'

    csrf_token = ''
    for i in range(8):
        csrf_token += token()[1:]
    return csrf_token


def encrypt_rsa(data: str) -> str:
    """
    登录密码加密
    :param data: 待加密的密码
    :return: str
    """
    rsa_key = '''-----BEGIN PUBLIC KEY-----
    MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEA6aTDM8BhCS8O0wlx2KzA
    Ajffez4G4A/QSnn1ZDuvLRbKBHm0vVBtBhD03QUnnHXvqigsOOwr4onUeNljegIC
    XC9h5exLFidQVB58MBjItMA81YVlZKBY9zth1neHeRTWlFTCx+WasvbS0HuYpF8+
    KPl7LJPjtI4XAAOLBntQGnPwCX2Ff/LgwqkZbOrHHkN444iLmViCXxNUDUMUR9bP
    A9/I5kwfyZ/mM5m8+IPhSXZ0f2uw1WLov1P4aeKkaaKCf5eL3n7/2vgq7kw2qSmR
    AGBZzW45PsjOEvygXFOy2n7AXL9nHogDiMdbe4aY2VT70sl0ccc4uvVOvVBMinOp
    d2rEpX0/8YE0dRXxukrM7i+r6lWy1lSKbP+0tQxQHNa/Cjg5W3uU+W9YmNUFc1w/
    7QT4SZrnRBEo++Xf9D3YNaOCFZXhy63IpY4eTQCJFQcXdnRbTXEdC3CtWNd7SV/h
    mfJYekb3GEV+10xLOvpe/+tCTeCDpFDJP6UuzLXBBADL2oV3D56hYlOlscjBokNU
    AYYlWgfwA91NjDsWW9mwapm/eLs4FNyH0JcMFTWH9dnl8B7PCUra/Lg/IVv6HkFE
    uCL7hVXGMbw2BZuCIC2VG1ZQ6QD64X8g5zL+HDsusQDbEJV2ZtojalTIjpxMksbR
    ZRsH+P3+NNOZOEwUdjJUAx8CAwEAAQ==
    -----END PUBLIC KEY-----'''
    data_byte = bytes(data, 'utf-8')
    encrypt_obj = PKCS1_v1_5.new(RSA.importKey(rsa_key))
    data_encrypt = b64encode(encrypt_obj.encrypt(data_byte))
    return data_encrypt.decode('utf-8')


class YiBan:
    session = requests.session()

    def __init__(self, phone, passwd, address) -> None:
        self.__phone = phone
        self.__password = passwd
        self.CSRF = get_csrf_token()  # '64b5c616dc98779ee59733e63de00dd5'
        self.__userToken = ''
        self.address = address

    def req(self, url, method='get', cookies=None, headers=None, timeout=5, allow_redirects=True,
            **kwargs) -> requests.Response:
        if headers is None:
            headers = {}
        if cookies is None:
            cookies = {}
        data = kwargs.get('data')
        params = kwargs.get('params')
        cookies.update(self.session.cookies.get_dict())
        cookies.update({'csrf_token': self.CSRF})
        headers.update({
            "Origin": "https://c.uyiban.com",
            'AppVersion': '5.0',
            'User-Agent': 'Yiban'
        })
        if method == 'get':
            reqs = self.session.get
        elif method == 'post':
            reqs = self.session.post
        else:
            self.session.close()  # close session
            raise Exception('Requests method error.')
        back = reqs(url, data=data, params=params, headers=headers,
                    cookies=cookies, timeout=timeout, allow_redirects=allow_redirects)
        return back

    def do_login(self) -> bool:
        push_data = {
            'account': self.__phone,
            'password': self.__password
        }
        # 这个请求没有返回值
        self.req('https://www.yiban.cn/login/dologinAjax', 'post', data=push_data,
                 headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}).json()
        try:
            cookie = self.session.cookies.get_dict()
            user_token = cookie['yiban_user_token']
            self.__userToken = user_token
            return True
        except KeyError:
            server_chan.log(f'{self.__phone} 登录失败')
            return False

    def auth(self) -> dict:
        """
        用户认证
        """
        url = ('iapp',
               'iframe')
        back_raw = self.req(
            f'https://f.yiban.cn/{url[1]}/index?act=iapp7463', allow_redirects=False)
        verify = re.findall(r"verify_request=(.*?)&",
                            back_raw.headers.get("Location"))[0]
        back_json = self.req('https://api.uyiban.com/base/c/auth/yiban',
                             params={'verifyRequest': verify, 'CSRF': self.CSRF}).json()
        try:
            back_json['data']['PersonName']
        except KeyError:
            msg = f'{self.__phone} 获取授权失败, 可能未授权校本化.'
            server_chan.log(msg)
            return {'code': 1, 'msg': msg}
        return back_json

    def do_sign(self):
        """
        晚点名签到
        :return:
        """
        # 设备状态?
        self.req(
            f'https://api.uyiban.com/nightAttendance/student/index/deviceState?CSRF={self.CSRF}').json()
        # 获取区域id
        self.req(
            f'https://api.uyiban.com/nightAttendance/student/index/getPersonId?CSRF={self.CSRF}').json()
        # 获取签到区域
        back_json = self.req(
            f'https://api.uyiban.com/nightAttendance/student/index/signPosition?CSRF={self.CSRF}').json()
        time_now = time.time()
        time_range = back_json['data']['Range']
        if time_range['StartTime'] < time_now < time_range['EndTime'] or DEBUG:
            push_data = {
                "Code": "",
                "PhoneModel": "",
                "SignInfo": self.address,
                "OutState": "1"
            }
            try:
                back = self.req(
                    f'https://api.uyiban.com/nightAttendance/student/index/signIn?CSRF={self.CSRF}', 'post',
                    data=push_data).json()
            except RequestException:
                msg = f'{self.__phone} 网络或参数异常, 签到失败'
                server_chan.log(msg)
                return msg

            if back['code'] == 0 and back['data'] is True:
                msg = f'{self.__phone} 签到成功'
            else:
                msg = f'{self.__phone} 签到失败'
            server_chan.log(msg)
            return msg

        msg = f'{self.__phone} 签到失败未到签到时间'
        server_chan.log(msg)
        return msg


for user in user_data:
    server_chan = ServerChan('易班签到详情', user['SendKey'])
    yiban = YiBan(user['Phone'], user['PassWord'], user['Address'])
    if not yiban.do_login():
        server_chan.send_msg()
        continue
    if yiban.auth()['code'] != 0:
        server_chan.send_msg()
        continue
    yiban.do_sign()
    server_chan.send_msg()
    time.sleep(5)
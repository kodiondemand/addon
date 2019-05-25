# -*- coding: utf-8 -*-

from core import httptools
from core import jsontools
from core import scrapertools
from platformcode import config, logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    header = {}
    if "|" in page_url:
        page_url, referer = page_url.split("|", 1)
        header = {'Referer': referer}
    data = httptools.downloadpage(page_url, headers=header, cookies=False).data
    if 'We’re Sorry!' in data:
        data = httptools.downloadpage(page_url.replace("/embed/", "/f/"), headers=header, cookies=False).data
        if 'We’re Sorry!' in data:
            return False, config.get_localized_string(70449) % "Openload"

    return True, ""

def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info()
    itemlist = []

    header = {}
    if "|" in page_url:
        page_url, referer = page_url.split("|", 1)
        header = {'Referer': referer}

    data = httptools.downloadpage(page_url, cookies=False, headers=header).data
    subtitle = scrapertools.find_single_match(data, '<track kind="captions" src="([^"]+)" srclang="es"')

    try:
        code = scrapertools.find_single_match(data, '<p style="" id="[^"]+">(.*?)</p>' )
        if not code or code == "" or code is None:
            code = scrapertools.find_single_match(data, '<p id="[^"]+" style="">(.*?)</p>' )
        _0x59ce16 = eval(scrapertools.find_single_match(data, '_0x59ce16=([^;]+)').replace('parseInt', 'int'))
        _1x4bfb36 = eval(scrapertools.find_single_match(data, '_1x4bfb36=([^;]+)').replace('parseInt', 'int'))
        parseInt  = eval(scrapertools.find_single_match(data, '_0x30725e,(\(parseInt.*?)\),').replace('parseInt', 'int'))
        url = decode(code, parseInt, _0x59ce16, _1x4bfb36)
        url = httptools.downloadpage(url, only_headers=True, follow_redirects=False).headers.get('location')
        extension = scrapertools.find_single_match(url, '(\..{,3})\?')
        itemlist.append([extension, url, 0,subtitle])

    except Exception:
        logger.info()
        if config.get_setting('api', __file__):
            url = get_link_api(page_url)
            extension = scrapertools.find_single_match(url, '(\..{,3})\?')
            if url:
                itemlist.append([extension, url, 0,subtitle])
    logger.debug(itemlist)

    return itemlist


def decode(code, parseInt, _0x59ce16, _1x4bfb36):
    logger.info()
    import math

    _0x1bf6e5 = ''
    ke = []

    for i in range(0, len(code[0:9*8]),8):
        ke.append(int(code[i:i+8],16))

    _0x439a49 = 0
    _0x145894 = 0

    while _0x439a49 < len(code[9*8:]):
        _0x5eb93a = 64
        _0x896767 = 0
        _0x1a873b = 0
        _0x3c9d8e = 0
        while True:
            if _0x439a49 + 1 >= len(code[9*8:]):
                _0x5eb93a = 143;

            _0x3c9d8e = int(code[9*8+_0x439a49:9*8+_0x439a49+2], 16)
            _0x439a49 +=2

            if _0x1a873b < 6*5:
                _0x332549 = _0x3c9d8e & 63
                _0x896767 += _0x332549 << _0x1a873b
            else:
                _0x332549 = _0x3c9d8e & 63
                _0x896767 += int(_0x332549 * math.pow(2, _0x1a873b))

            _0x1a873b += 6
            if not _0x3c9d8e >= _0x5eb93a: break

        # _0x30725e = _0x896767 ^ ke[_0x145894 % 9] ^ _0x59ce16 ^ parseInt ^ _1x4bfb36
        _0x30725e = _0x896767 ^ ke[_0x145894 % 9] ^ parseInt ^ _1x4bfb36
        _0x2de433 = _0x5eb93a * 2 + 127

        for i in range(4):
            _0x3fa834 = chr(((_0x30725e & _0x2de433) >> (9*8/ 9)* i) - 1)
            if _0x3fa834 != '$':
                _0x1bf6e5 += _0x3fa834
            _0x2de433 = (_0x2de433 << (9*8/ 9))

        _0x145894 += 1


    url = "https://openload.co/stream/%s?mime=true" % _0x1bf6e5
    return url


def login():
    logger.info()
    data = httptools.downloadpage('https://openload.co').data
    _csrf = scrapertools.find_single_match(data, '<input type="hidden" name="_csrf" value="([^"]+)">')

    post = {
                'LoginForm[email]'      : config.get_setting('user', __file__),
                'LoginForm[password]'	: config.get_setting('passowrd', __file__),
                'LoginForm[rememberMe]' : 1,
                '_csrf'                 : _csrf
            }
    data = httptools.downloadpage('https://openload.co/login', post = post).data

    if 'Login key has already been sent.' in data:
        while True :
            if 'Invalid login key.' in data:
                platformtools.dialog_ok('openload', 'El código introducido no es válido\nrevisa tu correo e introduce el código correcto')

            code = platformtools.dialog_input(  post.get('LoginForm[loginkey]', ''),
                                                'Introduzca el código que ha sido enviado a \'%s\'' % 'r_dav'
                                              )
            if not code:
                break
            else:
                post['LoginForm[loginkey]'] = code
                data = httptools.downloadpage('https://openload.co/login', post = post).data

                if 'Welcome back,' in data: break


def get_api_keys():
    logger.info()
    api_login = config.get_setting('api_login', __file__)
    api_key = config.get_setting('api_key', __file__)
    if not api_key or not api_login:
        login()
        data = httptools.downloadpage('https://openload.co/account').data
        post = {
                    'FTPKey[password]'      : config.get_setting('password', __file__),
                    '_csrf'                 : scrapertools.find_single_match(data, '<input type="hidden" name="_csrf" value="([^"]+)">')
                }


        data = httptools.downloadpage('https://openload.co/account', post = post).data
        api_login = scrapertools.find_single_match(data, '<tr><td>ID:</td><td>([^<]+)</td></tr>')
        api_key = scrapertools.find_single_match(data, 'Your FTP Password/API Key is: ([^<]+) </div>')
        config.set_setting('api_login', api_login, __file__)
        config.set_setting('api_key', api_key, __file__)

    return api_login, api_key


def get_link_api(page_url):
    logger.info()

    api_login, api_key = get_api_keys()

    file_id = scrapertools.find_single_match(page_url, '(?:embed|f)/([0-9a-zA-Z-_]+)')

    data = httptools.downloadpage("https://api.openload.co/1/file/dlticket?file=%s&login=%s&key=%s" % (file_id, api_login, api_key)).data
    data = jsontools.load_json(data)
    # logger.info(data)
    if data["status"] == 200:
        ticket = data["result"]["ticket"]
        data = httptools.downloadpage("https://api.openload.co/1/file/dl?file=%s&ticket=%s" % (file_id, ticket)).data
        data = jsontools.load(data)

        return data['result']['url'].replace("https", "http")

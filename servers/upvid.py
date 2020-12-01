# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector UpVID By Alfa development Group
# --------------------------------------------------------
import base64
import re

from core import httptools
from core import scrapertools
from lib.aadecode import decode as aadecode
from platformcode import config
from platformcode import logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url)
    if data.code == 404:
        return False, config.get_localized_string(70449) % "upvid"
    if "<title>video is no longer available" in data.data:
        return False,  config.get_localized_string(70449) % "upvid"
    return True, ""


def get_video_url(page_url, premium = False, user = "", password = "", video_password = ""):
    logger.debug("url=" + page_url)
    video_urls = []
    headers = {'referer': page_url}
    for i in range(0, 3):
        data = httptools.downloadpage(page_url, headers=headers).data
        if 'ﾟωﾟﾉ' in data:
            break
        else:
            page_url = scrapertools.find_single_match(data, '"iframe" src="([^"]+)')
            if not page_url:
                page_url = scrapertools.find_single_match(data, '<input type="hidden" id="link" value="([^"]+)')
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    code = scrapertools.find_single_match(data, '(?s)<script>\s*ﾟωﾟ(.*?)</script>').strip()
    text_decode = aadecode(code)
    funcion, clave = re.findall("func\.innerHTML = (\w*)\('([^']*)', ", text_decode, flags=re.DOTALL)[0]
    # decodificar javascript en campos html hidden
    # --------------------------------------------
    oculto = re.findall('<input type=hidden value=([^ ]+) id=func', data, flags=re.DOTALL)[0]
    funciones = resuelve(clave, base64.b64decode(oculto))
    url, type = scrapertools.find_single_match(funciones, "setAttribute\('src', '(.*?)'\);\s.*?type', 'video/(.*?)'")
    video_urls.append(['upvid [%s]' % type ,url])
    return video_urls


def resuelve(r, o):
    a = '';
    n = 0
    e = list(range(256))
    for f in range(256):
        n = (n + e[f] + ord(r[(f % len(r))])) % 256
        t = e[f];
        e[f] = e[n];
        e[n] = t
    f = 0;
    n = 0
    for h in range(len(o)):
        f = (f + 1) % 256
        n = (n + e[f]) % 256
        t = e[f];
        e[f] = e[n];
        e[n] = t
        a += chr(ord(o[h]) ^ e[(e[f] + e[n]) % 256])
    return a

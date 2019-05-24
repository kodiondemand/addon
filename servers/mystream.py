# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector mystream By Alfa development Group
# --------------------------------------------------------

import re

from core import httptools
from core import scrapertools
from lib.aadecode import decode as aadecode
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url)
    if data.code == 404:
        return False, "[mystream] El archivo no existe o ha sido borrado"
    if "<title>video is no longer available" in data.data:
        return False, "[mystream] El archivo no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium = False, user = "", password = "", video_password = ""):
    logger.info("url=" + page_url)
    video_urls = []
    headers = {'referer': page_url}
    data = httptools.downloadpage(page_url, headers=headers).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    code = scrapertools.find_single_match(data, '(?s)<script>\s*ﾟωﾟ(.*?)</script>').strip()
    text_decode = aadecode(code)
    matches = scrapertools.find_multiple_matches(text_decode, "'src', '([^']+)'")
    for url in matches:
        video_urls.append(['mystream [mp4]',url])
    return video_urls

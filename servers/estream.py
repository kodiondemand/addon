# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Estream By Alfa development Group
# --------------------------------------------------------

import re

from core import httptools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url)

    if data.code == 404:
        return False, "[Estream] El archivo no existe o  ha sido borrado"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)

    video_urls = []
    data = httptools.downloadpage(page_url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    patron = "<source src=([^ ]+) type='video/mp4' label='.*?x(.*?)'"
    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, quality in matches:
        video_urls.append(["%sp [estream]" % quality, url])

    return video_urls

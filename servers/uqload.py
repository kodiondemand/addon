# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Uqload By Alfa development Group
# --------------------------------------------------------
import re

from core import httptools
from platformcode import config
from platformcode import logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url)

    if data.code == 404:
        return False,  config.get_localized_string(70449) % "Uqload"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)

    video_urls = []
    data = httptools.downloadpage(page_url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    patron = 'sources:.?\["([^"]+)"\]'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for url in matches:
        # url = url+'|Referer='+page_url
        video_urls.append(["[uqload]", url])

    return video_urls

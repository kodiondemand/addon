# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from platformcode import logger, config


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    global data
    data = httptools.downloadpage(page_url).data
    if "copyrightsRestricted" in data or "COPYRIGHTS_RESTRICTED" in data:
        return False, config.get_localized_string(70449) % "OKru"
    elif "notFound" in data:
        return False, config.get_localized_string(70449) % "OKru"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    video_urls = []

    # data = httptools.downloadpage(page_url).data
    global data
    data = scrapertools.decodeHtmlentities(data).replace('\\', '')
    # URL del vídeo
    for type, url in re.findall(r'\{"name":"([^"]+)","url":"([^"]+)"', data, re.DOTALL):
        url = url.replace("%3B", ";").replace("u0026", "&")
        video_urls.append([type + " [OKru]", url + '|Referrer=' + page_url])

    return video_urls

# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from platformcode import logger, config


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url).data
    if "copyrightsRestricted" in data or "COPYRIGHTS_RESTRICTED" in data:
        return False, config.getLocalizedString(70449) % "OKru"
    elif "notFound" in data:
        return False, config.getLocalizedString(70449) % "OKru"

    return True, ""


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    videoUrls = []

    data = httptools.downloadpage(page_url).data
    data = scrapertools.decodeHtmlentities(data).replace('\\', '')
    # URL del vídeo
    for type, url in re.findall(r'\{"name":"([^"]+)","url":"([^"]+)"', data, re.DOTALL):
        url = url.replace("%3B", ";").replace("u0026", "&")
        videoUrls.append({'type':type, 'url':url})

    return videoUrls

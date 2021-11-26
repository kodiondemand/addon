# -*- coding: utf-8 -*-

import base64

from core import httptools
from platformcode import config, logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url, cookies=False).data
    if 'Not found id' in data:
        return False, config.getLocalizedString(70449) % "HDLoad"

    return True, ""


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    logger.debug()
    itemlist = []

    logger.debug(page_url)
    data = httptools.downloadpage(page_url, post='').data
    logger.debug(data)
    url = base64.b64decode(data)

    itemlist.append({'type':'mp4', 'url':url})

    return itemlist

# -*- coding: utf-8 -*-
from core import httptools, support
from platformcode import logger

data = ""

def test_video_exists(page_url):
    global data
    logger.debug("(page_url='%s')" % page_url)
    response = httptools.downloadpage(page_url)

    if response.code == 404:
        return False, support.config.get_localized_string(70449) % "Vudeo"
    else:
        data = response.data
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    global data
    logger.debug("url=" + page_url)
    return support.get_jwplayer_mediaurl(data, 'Vudeo')

# -*- coding: utf-8 -*-

from core import httptools, support
from platformcode import logger, config


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    global data
    resp = httptools.downloadpage(page_url)
    data = resp.data
    if resp.code == 404:
        return False, config.get_localized_string(70449) % "Vidmoly"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    global data
    video_urls = support.get_jwplayer_mediaurl(data, 'Vidmoly')

    return video_urls

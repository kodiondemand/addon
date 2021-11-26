# -*- coding: utf-8 -*-

from core import httptools, support
from core import scrapertools
from platformcode import config, logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    global data
    data = httptools.downloadpage(page_url, cookies=False).data
    if 'File you are looking for is not found.' in data:
        return False, config.getLocalizedString(70449) % "AvaVids"

    return True, ""


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    global data
    videoUrls = support.get_jwplayer_mediaUrl(data, 'AvaVids')
    return videoUrls

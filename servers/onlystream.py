# -*- coding: utf-8 -*-

from core import httptools, support
from core import scrapertools
from platformcode import config, logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    global data
    data = httptools.downloadpage(page_url).data
    if 'File you are looking for is not found.' in data:
        return False, config.get_localized_string(70449) % "Onlystream"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    global data
    # logger.info(data)
    video_urls = support.get_jwplayer_mediaurl(data, 'Onlystream')
    return video_urls

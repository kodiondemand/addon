# -*- coding: utf-8 -*-

from core import httptools, support
from core import scrapertools
from platformcode import config, logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)

    global data
    data = httptools.downloadpage(page_url).data
    if 'File you are looking for is not found.' in data:
        return False, config.get_localized_string(70449) % "Onlystream"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    global data
    # logger.debug(data)
    block = scrapertools.find_single_match(data, 'player.updateSrc\(([^\)]+)')
    video_urls = support.get_jwplayer_mediaurl(block, 'Onlystream', dataIsBlock=True)
    return video_urls

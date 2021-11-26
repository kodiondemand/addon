# -*- coding: utf-8 -*-

from core import httptools, scrapertools, servertools, support
from platformcode import logger, config
from lib import jsunpack


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    global data
    data = httptools.downloadpage(page_url).data
    if "Can't create video code" in data:
        return False, config.getLocalizedString(70292) % 'HxFile'
    return True, ""


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    global data
    videoUrls = []
    packed = scrapertools.find_single_match(data, r'(eval\s?\(function\(p,a,c,k,e,d\).*?\n)')
    data = jsunpack.unpack(packed)
    videoUrls.extend(support.get_jwplayer_mediaUrl(data, 'HxFile'))

    return videoUrls

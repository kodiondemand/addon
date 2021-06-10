# -*- coding: utf-8 -*-

from core import httptools, scrapertools, servertools, support
from platformcode import logger, config
from lib import jsunpack


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    global data
    data = httptools.downloadpage(page_url).data
    if "Can't create video code" in data:
        return False, config.get_localized_string(70292) % 'HxFile'
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    global data
    video_urls = []
    packed = scrapertools.find_single_match(data, r'(eval\s?\(function\(p,a,c,k,e,d\).*?\n)')
    data = jsunpack.unpack(packed)
    video_urls.extend(support.get_jwplayer_mediaurl(data, 'HxFile'))

    return video_urls

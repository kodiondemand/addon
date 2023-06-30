# -*- coding: utf-8 -*-
##



from core import httptools, support
from core import scrapertools
from platformcode import logger, config


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    global data

    data = httptools.downloadpage(page_url).data

    if "File is no longer available" in data:
        return False, config.get_localized_string(70449) % "StreamHide"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    global data

    return support.get_jwplayer_mediaurl(data, 'StreamHide', hls=True)

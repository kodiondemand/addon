# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Alfa addon - KODI Plugin
# Conector para vidlox
# https://github.com/alfa-addon
# ------------------------------------------------------------
from core import httptools
from core import scrapertools
from platformcode import config
from platformcode import logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    global data
    data = httptools.downloadpage(page_url).data
    if "borrado" in data or "Deleted" in data:
        return False,  config.getLocalizedString(70449) % "vidlox"

    return True, ""


def get_videoUrl(page_url, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    videoUrls = []

    bloque = scrapertools.find_single_match(data, 'sources:.\[.*?]')
    matches = scrapertools.findMultipleMatches(bloque, '(http.*?)"')
    for videourl in matches:
        extension = videourl.split('.')[-1]
        if extension == 'm3u8':
            continue
        videoUrls.append({'type':extension, 'url':videourl})
    # videoUrls.reverse()
    return videoUrls

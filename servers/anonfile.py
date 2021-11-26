# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector anonfile By Alfa development Group
# --------------------------------------------------------

from core import httptools
from core import scrapertools
from platformcode import logger, config


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    response = httptools.downloadpage(page_url)
    if not response.success or "Not Found" in response.data or "File was deleted" in response.data or "is no longer available" in response.data:
        return False, config.getLocalizedString(70449) % "anonfile"
    return True, ""


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    videoUrls = []
    data = httptools.downloadpage(page_url).data
    patron = 'download-url.*?href="([^"]+)"'
    match = scrapertools.findMultipleMatches(data, patron)
    for media_url in match:
        media_url += "|Referer=%s" %page_url
        videoUrls.append({'type':'mp4', 'url':media_url})
    return videoUrls

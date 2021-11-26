# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector vidfast By Alfa development Group
# --------------------------------------------------------
from core import httptools
from core import scrapertools
from platformcode import config
from platformcode import logger

videoUrls = []
def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)

    subtitles = ""
    response = httptools.downloadpage(page_url)
    global data
    data = response.data
    if not response.success or "Not Found" in data or "File was deleted" in data or "is no longer available" in data:
        return False,  config.getLocalizedString(70449) % "vidfast"
    return True, ""


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    videoUrls = []
    logger.debug("Intel11 %s" %data)
    media_url = scrapertools.find_single_match(data, 'file:"([^"]+)')
    if media_url:
        ext = media_url.split('.')[-1]
        videoUrls.append({'type':ext, 'url':media_url})

    return videoUrls

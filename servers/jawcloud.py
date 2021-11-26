# -*- coding: utf-8 -*-
from core import httptools
from core import scrapertools
from platformcode import config
from platformcode import logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "The file you were looking for could not be found" in data:
        return False,  config.getLocalizedString(70449) % "jawcloud"
    return True, ""


def get_videoUrl(page_url, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    videoUrls = []
    videourl = scrapertools.find_single_match(data, 'source src="([^"]+)')
    videoUrls.append({'type':'mp4', 'url':videourl})

    return videoUrls

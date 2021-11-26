# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector tusfiles By Alfa development Group
# --------------------------------------------------------
from core import httptools
from core import scrapertools
from platformcode import config
from platformcode import logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "no longer exists" in data or "to copyright issues" in data:
        return False,  config.getLocalizedString(70449) % "tusfiles"
    return True, ""


def get_videoUrl(page_url, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    videoUrls = []
    videourl = scrapertools.find_single_match(data, 'source src="([^"]+)')
    videoUrls.append({'type':'mp4', 'url':videourl})

    return videoUrls

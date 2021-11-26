# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector mydaddy By Alfa development Group
# --------------------------------------------------------
from core import httptools
from core import scrapertools
from platformcode import config
from platformcode import logger


def test_video_exists(page_url):

    response = httptools.downloadpage(page_url)

    if not response.success or \
       "Not Found" in response.data \
       or "File was deleted" in response.data \
       or "is no longer available" in response.data:
        return False,  config.getLocalizedString(70449) % "mydaddy"
    return True, ""


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    logger.debug()
    videoUrls = []
    data = httptools.downloadpage(page_url).data
    data = scrapertools.find_single_match(data, 'var srca = \[(.*?)\]')
    matches = scrapertools.findMultipleMatches(data, 'file: "([^"]+)", label: "([^"]+)"')
    for url,quality in matches:
        if not url.startswith("http"):
            url = "http:%s" % url
        if not "Default" in quality:
            videoUrls.append({'res':quality, 'url':url})
    return videoUrls
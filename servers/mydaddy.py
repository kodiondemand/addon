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
        return False,  config.get_localized_string(70449) % "mydaddy"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug()
    video_urls = []
    data = httptools.downloadpage(page_url).data
    data = scrapertools.find_single_match(data, 'var srca = \[(.*?)\]')
    matches = scrapertools.find_multiple_matches(data, 'file: "([^"]+)", label: "([^"]+)"')
    for url,quality in matches:
        if not url.startswith("http"):
            url = "http:%s" % url
        if not "Default" in quality:
            video_urls.append(["[mydaddy] %s" % quality, url])
    return video_urls
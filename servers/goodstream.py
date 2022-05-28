# -*- coding: utf-8 -*-
from core import httptools
from core import scrapertools
from platformcode import config, logger


def test_video_exists(page_url):
    global data
    page = httptools.downloadpage(page_url)
    data = page.data
    if page.code == 404:
        return False, config.get_localized_string(70449) % "GoodStream"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    global data
    logger.debug("(page_url='%s')" % page_url)
    video_urls = []
    matches = scrapertools.find_multiple_matches(data, '<source src="([^"]+)" type="video/(\w+)')
    for media_url, ext in matches:
        video_urls.append([ext, media_url])
    return video_urls

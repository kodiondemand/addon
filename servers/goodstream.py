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
    match = scrapertools.find_single_match(data, 'file:\s+"([^"]+)')
    video_urls.append(['.mp4', match])
    return video_urls

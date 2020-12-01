# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector DoStream By Alfa development Group
# --------------------------------------------------------
from core import httptools
from core import scrapertools
from platformcode import config
from platformcode import logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url)
    if data.code == 404:
        return False,  config.get_localized_string(70449) % "Dostream"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    video_urls = []
    data = httptools.downloadpage(page_url, headers={"Referer":page_url}).data
    patron  = '"label":"([^"]+)".*?'
    patron += '"src":"(http.*?)".*?'
    matches = scrapertools.find_multiple_matches(data, patron)
    for label, url in matches:
        video_urls.append(['%s [dostream]' %label, url])
    video_urls.sort(key=lambda it: int(it[0].split("p ")[0]))
    return video_urls

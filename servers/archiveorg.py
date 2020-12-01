# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector ArchiveOrg By Alfa development Group
# --------------------------------------------------------
from core import httptools
from core import scrapertools
from platformcode import config
from platformcode import logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url)
    if data.code == 404:
        return False,  config.get_localized_string(70449) % "ArchiveOrg"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    patron = '<meta property="og:video" content="([^"]+)">'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url in matches:
        video_urls.append(['.MP4 [ArchiveOrg]', url])
    return video_urls

# -*- coding: utf-8 -*-
from core import httptools
from core import scrapertools
from platformcode import config
from platformcode import logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data

    if "File was deleted" in data:
        return False,  config.get_localized_string(70449) % "FilesCDN"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    url = scrapertools.find_single_match(data, '(?i)link:\s*"(https://.*?filescdn\.com.*?mp4)"')
    url = url.replace(':443', '')
    video_urls.append(['filescdn', url])

    return video_urls

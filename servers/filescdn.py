# -*- coding: utf-8 -*-
from core import httptools
from core import scrapertools
from platformcode import config
from platformcode import logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data

    if "File was deleted" in data:
        return False,  config.getLocalizedString(70449) % "FilesCDN"

    return True, ""


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    videoUrls = []
    data = httptools.downloadpage(page_url).data
    url = scrapertools.find_single_match(data, '(?i)link:\s*"(https://.*?filescdn\.com.*?mp4)"')
    url = url.replace(':443', '')
    videoUrls.append({'url':url})

    return videoUrls

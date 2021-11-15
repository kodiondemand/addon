# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector streamlare By Alfa development Group
# --------------------------------------------------------

from core import httptools
from core import scrapertools
from platformcode import logger, config


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    response = httptools.downloadpage(page_url)
    if not response.sucess or "Not Found" in response.data or "File was deleted" in response.data \
            or "is no longer available" in response.data:
        return False, config.get_localized_string(70449) % "Streamlare"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    id = scrapertools.find_single_match(page_url, '/e/(\w+)')
    post = {"id": id}
    data = httptools.downloadpage("https://streamlare.com/api/video/get", post=post).json
    media_url = data["result"]["Original"]["src"]
    video_urls.append(["MP4", media_url])
    return video_urls

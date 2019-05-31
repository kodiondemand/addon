# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector videobb By Alfa development Group
# --------------------------------------------------------

from core import httptools
from core import jsontools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "no longer exists" in data:
        return False, "[videobb] El video ha sido borrado"
    return True, ""


def get_video_url(page_url, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    id = scrapertools.find_single_match("v/(\w+)", page_url)
    post = "r=&d=videobb.ru"
    data = httptools.downloadpage(page_url, post=post).data
    data = jsontools.load(data)["data"]
    for url in data:
        video_urls.append([url["label"] + "p [videobb]", url["file"]])
    logger.info("Intel11 %s" %data)

    return video_urls

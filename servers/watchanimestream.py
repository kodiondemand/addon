# -*- coding: utf-8 -*-
from core import httptools
from core import scrapertools
from platformcode import logger


def get_video_url(page_url, video_password):
    logger.debug("(page_url='%s')" % page_url)
    video_urls = []
    url = page_url.replace("/v/", "/api/source/")
    post = "r=&d=watchanimestream.net"
    data = httptools.downloadpage(url, post=post).data
    matches = scrapertools.find_multiple_matches(data, '"file":"([^"]+)","label":"([^"]+)"')
    for url, quality in matches:
        url = url.replace("\/", "/")
    video_urls.append(["[watchanimestream] %s" %quality, url])
    return video_urls


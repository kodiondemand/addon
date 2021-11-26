# -*- coding: utf-8 -*-
from core import httptools
from core import scrapertools
from platformcode import logger


def get_videoUrl(page_url, video_password):
    logger.debug("(page_url='%s')" % page_url)
    videoUrls = []
    url = page_url.replace("/v/", "/api/source/")
    post = "r=&d=watchanimestream.net"
    data = httptools.downloadpage(url, post=post).data
    matches = scrapertools.findMultipleMatches(data, '"file":"([^"]+)","label":"([^"]+)"')
    for url, quality in matches:
        url = url.replace("\/", "/")
    videoUrls.append({'res':quality, 'url':url})
    return videoUrls


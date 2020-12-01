# -*- coding: utf-8 -*-
from core import httptools
from core import scrapertools
from platformcode import logger


def get_video_url(page_url, video_password):
    logger.debug("(page_url='%s')" % page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    url = scrapertools.find_single_match(data, '<source src="([^"]+)"')
    video_urls.append(["[youdbox]", url])
    return video_urls


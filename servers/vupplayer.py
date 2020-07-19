# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from platformcode import logger, config


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    page = httptools.downloadpage(page_url)
    global data
    data = page.data
    if page.code == 404:
        return False, config.get_localized_string(70449)
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    global data
    patron = r'sources:\s*\[\{src:\s*"([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url in matches:
        quality = 'm3u8'
        video_url = url
        if 'label' in url:
            url = url.split(',')
            video_url = url[0]
            quality = url[1].replace('label:','')
        video_urls.append(['VUP Player [%s]' % quality, video_url])
    return video_urls

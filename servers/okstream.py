# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from platformcode import logger, config

def test_video_exists(page_url):
    global data
    logger.debug('page url=', page_url)
    response = httptools.downloadpage(page_url)

    if response.code == 404:
        return False, config.get_localized_string(70449) % 'OkStream'
    else:
        data = response.data
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    global data
    logger.debug("URL", page_url)
    video_urls = []
    keys = scrapertools.find_single_match(data, '>var keys="([^"]+)"')
    protection = scrapertools.find_single_match(data, '>var protection="([^"]+)"')
    url =  httptools.downloadpage("https://www.okstream.cc/request/", post='&morocco={}&mycountry={}'.format(keys, protection), headers={'Referer':page_url}).data
    url = url.strip()
    video_urls.append([url.split('.')[-1] + " [OkStream]", url])

    return video_urls
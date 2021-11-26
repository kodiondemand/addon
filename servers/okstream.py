# -*- coding: utf-8 -*-

from core import httptools, support
from platformcode import logger, config

def test_video_exists(page_url):
    global data
    logger.debug('page url=', page_url)
    response = httptools.downloadpage(page_url)

    if response.code == 404 or 'File has been removed or does not exist!' in response.data:
        return False, config.getLocalizedString(70449) % 'OkStream'
    else:
        data = response.data
    return True, ""


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    global data
    logger.debug("URL", page_url)
    videoUrls = []
    keys = support.match(data, patron=r'>var keys="([^"]+)"').match
    protection = support.match(data, patron=r'>var protection="([^"]+)"').match
    url =  httptools.downloadpage("https://www.okstream.cc/request/", post='&morocco={}&mycountry={}'.format(keys, protection), headers={'Referer':page_url}).data
    url = url.strip()
    videoUrls.append({'type':url.split('.')[-1], 'url':url})

    return videoUrls
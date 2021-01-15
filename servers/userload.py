# -*- coding: utf-8 -*-
import json
from core import support, httptools
from platformcode import logger, config

def test_video_exists(page_url):
    global data
    logger.debug('page url=', page_url)
    response = httptools.downloadpage(page_url)

    if response.code == 404:
        return False, config.get_localized_string(70449) % 'Userload'
    else:
        data = response.data
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    global data
    logger.debug("URL", page_url)
    video_urls = []
    var = support.match(data, patron=r"var\|\|([^']+)").match.split('|')
    if var:
        post = 'morocco={}&mycountry={}'.format(var[7], var[17])
        url = support.match('https://userload.co/api/request/', post=post, patron=r'([^\s\r\n]+)').match
        if url:
            video_urls.append(["{} [Userload]".format(url.split('.')[-1]), url])

    return video_urls
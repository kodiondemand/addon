# -*- coding: utf-8 -*-

from core import httptools, support
from platformcode import logger, config


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    global response

    response = httptools.downloadpage(page_url, cookies=False)

    if response.json.get('error'):
        return False, config.get_localized_string(70449) % "dailymotion"
    if response.code == 404:
        return False, config.get_localized_string(70449) % "dailymotion"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    data = response.json

    url = data.get('qualities', {}).get('auto', [{}])[0].get('url','')

    urls = support.match(url, patron=r'NAME="([^"]+)"\s*,\s*PROGRESSIVE-URI="([^"]+)').matches
    for quality, uri in urls:
        video_urls.append(["mp4 [{}p] [dailymotion]".format(quality), uri])

    return video_urls
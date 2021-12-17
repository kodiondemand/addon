# -*- coding: utf-8 -*-

from core import httptools
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
    data = response.json

    url = data.get('qualities', {}).get('auto', [{}])[0].get('url','')

    return [["m3u8 [dailymotion]", url]]
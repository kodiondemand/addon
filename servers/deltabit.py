# -*- coding: utf-8 -*-

import time, sys

from core import httptools, scrapertools, support
from lib import jsunpack
from platformcode import logger, config


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    global data, real_url
    page = httptools.downloadpage(page_url)
    data = page.data.replace('"', "'")
    real_url = page.url

    if "Not Found" in data or "File Does not Exist" in data or "File doesn't exits" in data:
        return False, config.get_localized_string(70449) % "DeltaBit"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("(deltabit page_url='%s')" % page_url)
    global data, real_url
    post = {k: v for k, v in scrapertools.find_multiple_matches(data, "name='([^']+)' value='([^']*)'")}
    time.sleep(2.5)
    link = support.match(real_url, post=post, patron='sources:\s*\["([^"]+)').match.replace('https:', 'http:')
    return [[".mp4" + " [deltabit]", link]]

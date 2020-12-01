# -*- coding: utf-8 -*-

import re, time
from lib import js2py
from core import httptools, scrapertools
from platformcode import logger, config

def test_video_exists(page_url):
    global data
    logger.debug('page url=', page_url)
    response = httptools.downloadpage(page_url)

    if response.code == 404 or 'File you are looking for is not found' in response.data:
        return False, config.get_localized_string(70449) % 'DooD Stream'
    else:
        data = response.data
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    # from core.support import dbg;dbg()
    global data
    logger.debug("URL", page_url)
    # from core.support import dbg;dbg()
    video_urls = []
    host = scrapertools.find_single_match(page_url, r'http[s]?://[^/]+')

    new_url = scrapertools.find_single_match(data, r'<iframe src="([^"]+)"')
    if new_url: data = httptools.downloadpage(host + new_url).data

    label = scrapertools.find_single_match(data, r'type:\s*"video/([^"]+)"')

    base_url, token = scrapertools.find_single_match(data, r'''dsplayer\.hotkeys[^']+'([^']+).+?function\s*makePlay.+?return[^?]+([^"]+)''')
    url = '{}{}{}|Referer={}'.format(httptools.downloadpage(host + base_url, headers={"Referer": page_url}).data, token, str(int(time.time() * 1000)), page_url)
    video_urls.append([ label + ' [DooD Stream]', url])

    return video_urls
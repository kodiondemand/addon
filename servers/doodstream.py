# -*- coding: utf-8 -*-

import time, string, random
from core import httptools, support, servertools
from platformcode import logger, config


def test_video_exists(page_url):
    global data
    logger.debug('page url=', page_url)

    response = httptools.downloadpage(page_url)
    if response.code == 404 or 'dsplayer' not in response.data:
        return False, config.get_localized_string(70449) % 'DooD Stream'
    else:
        data = response.data
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    global data
    logger.debug("URL", page_url)

    video_urls = []
    host = 'https://' + servertools.get_server_host('doodstream')[0]
    headers = {'User-Agent': httptools.get_user_agent(), 'Referer': page_url}
    support.dbg()

    match = support.match(data, patron=r'''dsplayer\.hotkeys[^']+'([^']+).+?function\s*makePlay.+?return[^?]+([^"]+)''').match
    if match:
        url, token = match
        ret = httptools.downloadpage(host + url, headers=headers).data
        video_urls.append(['mp4 [DooD Stream]', '{}{}{}{}|Referer={}'.format(randomize(ret), url, token, int(time.time() * 1000), host)])


    return video_urls


def randomize(data):
    t = string.ascii_letters + string.digits
    return data + ''.join([random.choice(t) for _ in range(10)])
# -*- coding: utf-8 -*-

import time, string, random
from core import httptools, support
from platformcode import logger, config
import cloudscraper
scraper = cloudscraper.create_scraper()

def test_video_exists(page_url):
    global data
    logger.debug('page url=', page_url)

    response = scraper.get(page_url)
    # support.dbg()
    if response.status_code == 404 or 'dsplayer' not in response.text:
        return False, config.get_localized_string(70449) % 'DooD Stream'
    else:
        data = response.text
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    global data
    logger.debug("URL", page_url)

    video_urls = []
    host = 'https://dood.to'
    headers = {'User-Agent': httptools.get_user_agent(), 'Referer': page_url}

    match = support.match(data, patron=r'''dsplayer\.hotkeys[^']+'([^']+).+?function\s*makePlay.+?return[^?]+([^"]+)''').match
    if match:
        url, token = match
        ret = scraper.get(host + url, headers=headers).text
        video_urls.append(['mp4 [DooD Stream]', '{}{}{}{}|Referer={}'.format(randomize(ret), url, token, int(time.time() * 1000), host)])


    return video_urls

def randomize(data):
    t = string.ascii_letters + string.digits
    return data + ''.join([random.choice(t) for _ in range(10)])
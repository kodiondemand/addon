# -*- coding: utf-8 -*-

import re,  time
from lib import js2py
from core import httptools, scrapertools
from platformcode import logger, config

def test_video_exists(page_url):
    global data
    logger.info('page url=', page_url)
    response = httptools.downloadpage(page_url)

    if response.code == 404 or 'File you are looking for is not found' in response.data:
        return False, config.get_localized_string(70449) % 'DooD Stream'
    else:
        data = response.data
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    global data
    logger.info("URL", page_url)

    video_urls = list()
    host = "https://dood.watch"

    new_url = scrapertools.find_single_match(data, r'<iframe src="([^"]+)"')
    if new_url:
        data = httptools.downloadpage(host + new_url).data
        logger.info('DATA', data)

    label = scrapertools.find_single_match(data, r'type:\s*"video/([^"]+)"')

    js_code = scrapertools.find_single_match(data, ('(function makePlay.*?;})'))
    js_code = re.sub(r"\+Date.now\(\)", '', js_code)
    js = js2py.eval_js(js_code)
    makeplay = js() + str(int(time.time()*1000))

    base_url = scrapertools.find_single_match(data, r"\$.get\('([^']+)'")
    data = httptools.downloadpage("%s%s" % (host, base_url), headers={"referer": page_url}).data
    data = re.sub(r'\s+', '', data)

    url = data + makeplay + "|Referer=%s" % page_url
    video_urls.append([ label + ' [DooD Stream]', url])

    return video_urls
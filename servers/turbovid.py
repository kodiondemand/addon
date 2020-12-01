# -*- coding: utf-8 -*-

import time
try:
    import urllib.parse as urllib
except ImportError:
    import urllib

from core import httptools, support
from core import scrapertools
from platformcode import logger, config


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "Not Found" in data or "File Does not Exist" in data:
        return False, config.get_localized_string(70449) % "Turbovid"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password="", server='Turbovid'):

    logger.debug("(turbovid page_url='%s')" % page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    data = data.replace('"', "'")
    page_url_post = scrapertools.find_single_match(data, "<Form method='POST' action='([^']+)'>")
    imhuman = "&imhuman=" + scrapertools.find_single_match(data, "name='imhuman' value='([^']+)'").replace(" ", "+")
    post = urllib.urlencode({k: v for k, v in scrapertools.find_multiple_matches(data, "name='([^']+)' value='([^']*)'")}) + imhuman

    time.sleep(6)
    data = httptools.downloadpage(page_url_post, post=post).data
    logger.debug("(data page_url='%s')" % data)
    video_urls = support.get_jwplayer_mediaurl(data, 'Turbovid')
    return video_urls

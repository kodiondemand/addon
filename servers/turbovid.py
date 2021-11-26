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
        return False, config.getLocalizedString(70449) % "Turbovid"
    return True, ""


def get_videoUrl(page_url, premium=False, user="", password="", video_password="", server='Turbovid'):

    logger.debug("(turbovid page_url='%s')" % page_url)
    videoUrls = []
    data = httptools.downloadpage(page_url).data
    data = data.replace('"', "'")
    page_url_post = scrapertools.find_single_match(data, "<Form method='POST' action='([^']+)'>")
    imhuman = "&imhuman=" + scrapertools.find_single_match(data, "name='imhuman' value='([^']+)'").replace(" ", "+")
    post = urllib.urlencode({k: v for k, v in scrapertools.findMultipleMatches(data, "name='([^']+)' value='([^']*)'")}) + imhuman

    time.sleep(6)
    data = httptools.downloadpage(page_url_post, post=post).data
    logger.debug("(data page_url='%s')" % data)
    videoUrls = support.get_jwplayer_mediaUrl(data, 'Turbovid')
    return videoUrls

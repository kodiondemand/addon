# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector myupload By Alfa development Group
# --------------------------------------------------------
import base64

from core import httptools
from core import scrapertools
from platformcode import config
from platformcode import logger


def test_video_exists(page_url):

    response = httptools.downloadpage(page_url)

    if not response.success or \
       "Not Found" in response.data \
       or "File was deleted" in response.data \
       or "is no longer available" in response.data:
        return False,  config.getLocalizedString(70449) % "myupload"
    return True, ""


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    logger.debug()
    videoUrls = []
    data = httptools.downloadpage(page_url).data
    matches = scrapertools.findMultipleMatches(data, 'tracker: "([^"]+)"')
    for scrapedurl in matches:
        url = base64.b64decode(scrapedurl)
    videoUrls.append({'url':url})
    return videoUrls
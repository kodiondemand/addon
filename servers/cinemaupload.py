# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Cinemaupload By Alfa development Group
# --------------------------------------------------------
import re

from core import httptools
from core import scrapertools
from platformcode import config
from platformcode import logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url)
    if data.code == 404:
        return False,  config.getLocalizedString(70449) % "CinemaUpload"
    return True, ""


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    videoUrls = []
    data = httptools.downloadpage(page_url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    patron = 'file: "([^"]+)",'
    matches = scrapertools.findMultipleMatches(data, patron)
    for url in matches:
        url += "|Referer=%s" %page_url
        videoUrls.append({'type':'m3u8', 'url':url})
    return videoUrls

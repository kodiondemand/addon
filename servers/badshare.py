# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Badshare By Alfa development Group
# --------------------------------------------------------
import re

from core import httptools
from core import scrapertools
from platformcode import config
from platformcode import logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    global page
    page = httptools.downloadpage(page_url)
    if not page.success:
        return False,  config.getLocalizedString(70449) % "Badshare"
    return True, ""


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    videoUrls = []
    ext = '.mp4'

    data = page.data
    data =  re.sub(r'\n|\r|\t|\s{2,}', "", data)
    media_url, ext = scrapertools.find_single_match(data, r'file:\s*"([^"]+)",type:\s*"([^"]+)"')
    
    videoUrls.append({'type':ext, 'url':media_url})

    return videoUrls

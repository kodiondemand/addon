# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Idtbox By Alfa development Group
# --------------------------------------------------------
import re

from core import httptools
from platformcode import config
from platformcode import logger

data = ""
def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    global data
    data = httptools.downloadpage(page_url)

    if not data.success or "Not Found" in data.data or "File was deleted" in data.data or "is no longer available" in data.data:
        return False,  config.getLocalizedString(70449) % "Idtbox"
    
    data = data.data
    return True, ""


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    logger.error(data)
    videoUrls = []
    patron = 'source src="([^"]+)" type="([^"]+)" res=(\d+)'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, ext, res in matches:
        res = res+'p'
        try:
            ext = ext.split("/")[1]
        except:
            ext = ".mp4"
        videoUrls.append({'type':ext, 'res':res, 'url':url})

    return videoUrls

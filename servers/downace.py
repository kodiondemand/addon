# -*- coding: utf-8 -*-
from core import httptools
from core import scrapertools
from platformcode import config
from platformcode import logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "no longer exists" in data or "to copyright issues" in data:
        return False, "[Downace] El video ha sido borrado"
    if "please+try+again+later." in data:
        return False, "[Downace] Error de downace, no se puede generar el enlace al video"
    if "File has been removed due to inactivity" in data:
        return False,  config.get_localized_string(70449) % "Downace"
    return True, ""


def get_video_url(page_url, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    video_urls = []
    videourl = scrapertools.find_single_match(data, 'controls preload.*?src="([^"]+)')
    video_urls.append([".MP4 [downace]", videourl])

    return video_urls

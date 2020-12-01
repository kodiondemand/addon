# -*- coding: utf-8 -*-
from core import httptools
from core import scrapertools
from platformcode import config
from platformcode import logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "no longer exists" in data or "to copyright issues" in data:
        return False,  config.get_localized_string(70449) % "animeid"
    if "please+try+again+later." in data:
        return False, "[animeid] Error de animeid, no se puede generar el enlace al video"
    return True, ""


def get_video_url(page_url, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    video_urls = []
    label, videourl = scrapertools.find_single_match(data, 'label":"([^"]+)".*?file":"([^"]+)')
    if "animeid.tv" in videourl:
        videourl = httptools.downloadpage(videourl, follow_redirects=False, only_headers=True).headers.get("location", "")
    video_urls.append([".MP4 " + label + " [animeid]", videourl])
    return video_urls

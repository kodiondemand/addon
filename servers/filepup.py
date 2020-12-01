# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector filepup By Alfa development Group
# --------------------------------------------------------

from core import httptools
from core import scrapertools
from platformcode import logger, config


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    response = httptools.downloadpage(page_url)
    if "File was deleted" in response.data or "is no longer available" in response.data:
        return False, config.get_localized_string(70449) % "filepup"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    video_urls = []
    page_url = page_url.replace("https","http") + "?wmode=transparent"
    data = httptools.downloadpage(page_url).data
    media_url = scrapertools.find_single_match(data, 'src: "([^"]+)"')
    qualities = scrapertools.find_single_match(data, 'qualities: (\[.*?\])')
    qualities = scrapertools.find_multiple_matches(qualities, ' "([^"]+)')
    for calidad in qualities:
        media = media_url
        title = "%s [filepup]" % (calidad)
        if "480" not in calidad:
            med = media_url.split(".mp4")
            media = med[0] + "-%s.mp4" %calidad + med[1]
        media += "|Referer=%s" %page_url
        media += "&User-Agent=" + httptools.get_user_agent()
        video_urls.append([title, media, int(calidad.replace("p", ""))])
    video_urls.sort(key=lambda x: x[2])
    for video_url in video_urls:
        video_url[2] = 0
        logger.debug("%s - %s" % (video_url[0], video_url[1]))
    return video_urls

# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from platformcode import logger, config
headers = [['User-Agent', 'Mozilla/5.0']]
def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)

    global data
    if "|" in page_url:
        page_url, referer = page_url.split("|", 1)
        headers.append(['Referer', referer])
    if not page_url.endswith("/config"):
        page_url = scrapertools.find_single_match(page_url, ".*?video/[0-9]+")

    data = httptools.downloadpage(page_url, headers=headers).data

    if "Private Video on Vimeo" in data or "Sorry" in data:
        return False, config.getLocalizedString(70449) % 'Vimeo'
    else:
        return True, ""


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    videoUrls = []

    global data
    patron = 'mime":"([^"]+)"'
    patron += '.*?url":"([^"]+)"'
    patron += '.*?quality":"([^"]+)"'
    match = scrapertools.findMultipleMatches(data, patron)
    for mime, media_url, calidad in match:
        # title = "%s (%s) [Vimeo]" % (mime.replace("video/", "."), calidad)
        videoUrls.append({'type':mime.replace("video/", ""), 'url':media_url, 'res':calidad})

    # videoUrls.sort(key=lambda x: x[2])
    # for videoUrl in videoUrls:
    #     videoUrl[2] = 0
    #     logger.debug("%s - %s" % (videoUrl[0], videoUrl[1]))

    return videoUrls

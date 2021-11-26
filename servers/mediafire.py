# -*- coding: utf-8 -*-
from core import httptools
from core import scrapertools
from platformcode import config
from platformcode import logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "Invalid or Deleted File" in data or "Well, looks like we" in data:
        return False,  config.getLocalizedString(70449) % "Mediafire"
    if "File Removed for Violation" in data:
        return False, "[Mediafire] Archivo eliminado por infracción"
    return True, ""


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    videoUrls = []
    data = httptools.downloadpage(page_url).data
    patron = "DownloadButtonAd-startDownload gbtnSecondary.*?href='([^']+)'"
    matches = scrapertools.findMultipleMatches(data, patron)
    if len(matches) == 0:
        patron = 'Download file.*?href="([^"]+)"'
        matches = scrapertools.findMultipleMatches(data, patron)
    if len(matches) > 0:
        videoUrls.append({'type':matches[0].split('.')[-1], 'url':matches[0]})
    # for videoUrl in videoUrls:
    #     logger.debug("%s - %s" % (videoUrl[0], videoUrl[1]))
    return videoUrls

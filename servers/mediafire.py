# -*- coding: utf-8 -*-
from core import httptools
from core import scrapertools
from platformcode import config
from platformcode import logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "Invalid or Deleted File" in data or "Well, looks like we" in data:
        return False,  config.get_localized_string(70449) % "Mediafire"
    if "File Removed for Violation" in data:
        return False, "[Mediafire] Archivo eliminado por infracción"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    patron = "DownloadButtonAd-startDownload gbtnSecondary.*?href='([^']+)'"
    matches = scrapertools.find_multiple_matches(data, patron)
    if len(matches) == 0:
        patron = 'Download file.*?href="([^"]+)"'
        matches = scrapertools.find_multiple_matches(data, patron)
    if len(matches) > 0:
        video_urls.append([matches[0][-4:] + " [mediafire]", matches[0]])
    for video_url in video_urls:
        logger.debug("%s - %s" % (video_url[0], video_url[1]))
    return video_urls

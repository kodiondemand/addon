# -*- coding: utf-8 -*-
# -*- Server Voe -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

from core import httptools
from core import scrapertools
from platformcode import logger
from platformcode import config
import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int


def test_video_exists(page_url):
    global data
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data

    if "File not found" in data or "File is no longer available" in data:
        return False, config.getLocalizedString(70449) % "VOE"
    return True, ""


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    videoUrls = []
    video_srcs = scrapertools.findMultipleMatches(data, r"src: '([^']+)'")
    if not video_srcs:
        bloque = scrapertools.find_single_match(data, "sources.*?\}")
        video_srcs = scrapertools.findMultipleMatches(bloque, ': "([^"]+)')
    for url in video_srcs:
        videoUrls.append([" [Voe]", url])

    return videoUrls

# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector streamtape By Alfa development Group
# --------------------------------------------------------
from core import httptools, scrapertools
from platformcode import logger, config
import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data

    referer = {"Referer": page_url}

    data = httptools.downloadpage(page_url, headers=referer).data

    if "Video not found" in data:
        return False, config.get_localized_string(70449) % 'Streamtape'

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)

    video_urls = []
    possible_url = scrapertools.find_single_match(data, 'innerHTML = "([^"]+)')
    if not '\\' in possible_url:
        possible_url = scrapertools.find_single_match(data, "innerHTML\\'\]=\\'([^']+)")
    url = "https:" + possible_url
    url = httptools.downloadpage(url, follow_redirects=False, only_headers=True).headers.get("location", "")
    video_urls.append(['MP4 [Streamtape]', url])
    return video_urls
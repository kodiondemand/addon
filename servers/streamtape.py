# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector streamtape By Alfa development Group
# --------------------------------------------------------
from core import httptools, scrapertools
from platformcode import logger, config
from core.support import match
import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    global data

    referer = {"Referer": page_url}

    data = httptools.downloadpage(page_url, headers=referer).data

    if "Video not found" in data:
        return False, config.get_localized_string(70449) % 'Streamtape'

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)

    video_urls = []
    find_url = match(data, patron=r'''innerHTML = ["']([^"]+)["'](?:\s*\+\s*['"(]+([^"']+))?''').match
    possible_url = find_url[0]
    possible_url += find_url[1][2:]

    if not possible_url:
        possible_url = match(data, patron=r"innerHTML\\'\]=\\'([^']+)").match
    url = "https:" + possible_url
    url = httptools.downloadpage(url, follow_redirects=False, only_headers=True).headers.get("location", "")
    video_urls.append(['MP4 [Streamtape]', url])
    return video_urls

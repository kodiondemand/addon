# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector streamtape By Alfa development Group
# --------------------------------------------------------
from core import httptools
from platformcode import logger, config
from core.support import match
import sys
from lib import js2py

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
    find_url = match(data, patron=r'innerHTML = ([^;]+)').matches[-1]
    possible_url = js2py.eval_js(find_url)
    url = "https:" + possible_url
    url = httptools.downloadpage(url, follow_redirects=False, only_headers=True).headers.get("location", "")
    video_urls.append({'type':'mp4', 'url':url})
    return video_urls

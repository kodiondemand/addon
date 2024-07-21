# -*- coding: utf-8 -*-
# -*- Server Voe -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

from core import httptools, support
from core import scrapertools
from platformcode import logger
from platformcode import config
import sys
import base64

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int


def test_video_exists(page_url):
    global data
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    redirect_url = support.match(data, patron=r"}\s}\selse\s{\swindow.location.href\s=\s'(http[^']+)'").match

    if redirect_url:
        data = httptools.downloadpage(redirect_url).data

    if "File not found" in data or "File is no longer available" in data:
        return False, config.get_localized_string(70449) % "VOE"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)    
    video_urls = []
    video_srcs = support.match(data, patron=r"src: '([^']+)'")
    video_srcs = scrapertools.find_multiple_matches(data, r"src: '([^']+)'")    
    if not video_srcs:
        video_srcs = support.match(data, patronBlock=r'sources [^\{]+{([^}]+)', patron=r'''['"]([^'"]+)[^:]+: ['"]([^'"]+)['"]''').matches
    for ext, url in video_srcs:
        video_urls.append([ext + " [Voe]", base64.b64decode(url).decode()])

    return video_urls


def get_filename(page_url):
    title = httptools.downloadpage(page_url).data.split('<title>')[1].split('</title>')[0]
    prefix = 'Watch '
    if title.startswith(prefix):
        return title[len(prefix):]
    return ""

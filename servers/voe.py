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
        return False, config.get_localized_string(70449) % "VOE"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    from core import support
    # support.dbg()
    video_urls = []
    video_srcs = support.match(data, patron=r"src: '([^']+)'")
    video_srcs = scrapertools.find_multiple_matches(data, r"src: '([^']+)'")
    if not video_srcs:
        # bloque = scrapertools.find_single_match(data, "sources.*?\}")
        # video_srcs = support.match(bloque, patron=': "([^"]+)', debug=True)
        video_srcs = support.match(data, patronBlock=r'sources [^\{]+{([^}]+)', patron=r'''['"]([^'"]+)[^:]+: ['"]([^'"]+)['"]''').matches
    for ext, url in video_srcs:
        video_urls.append([ext + " [Voe]", url])

    return video_urls


def get_filename(page_url):
    title = httptools.downloadpage(page_url).data.split('<title>')[1].split('</title>')[0]
    prefix = 'Watch '
    if title.startswith(prefix):
        return title[len(prefix):]
    return ""

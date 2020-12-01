# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector GoUnlimited By Alfa development Group
# --------------------------------------------------------

import re

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger, config


def test_video_exists(page_url):
    global data
    data = httptools.downloadpage(page_url, use_requests=True, verify=False).data
    if data == "File was deleted":
        return False, config.get_localized_string(70449) % "Go Unlimited"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    video_urls = []
    global data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    # logger.debug('GOUN DATA= '+data)
    packed_data = scrapertools.find_single_match(data, "javascript'>(eval.*?)</script>")
    unpacked = jsunpack.unpack(packed_data)
    # logger.debug('GOUN DATA= '+unpacked)
    patron = r"sources..([^\]]+)"
    matches = re.compile(patron, re.DOTALL).findall(unpacked)
    if not matches:
        patron= r'src:([^,]+),'
        matches = re.compile(patron, re.DOTALL).findall(unpacked)
    for url in matches:
            if url.startswith('//'): url= 'http:' + url
            url += "|Referer=%s" %page_url
            video_urls.append(['mp4 [Go Unlimited]', url])
    return video_urls

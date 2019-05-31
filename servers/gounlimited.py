# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector GoUnlimited By Alfa development Group
# --------------------------------------------------------

import re

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger


def test_video_exists(page_url):
    data = httptools.downloadpage(page_url).data
    if data == "File was deleted":
        return False, "[gounlimited] El video ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    packed_data = scrapertools.find_single_match(data, "javascript'>(eval.*?)</script>")
    unpacked = jsunpack.unpack(packed_data)
    patron = "sources..([^\]]+)"
    matches = re.compile(patron, re.DOTALL).findall(unpacked)
    for url in matches:
        url += "|Referer=%s" %page_url
        video_urls.append(['mp4', url])
    return video_urls

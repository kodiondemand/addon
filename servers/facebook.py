# -*- coding: utf-8 -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    #from future import standard_library
    #standard_library.install_aliases()
    import urllib.parse as urllib                               # Es muy lento en PY2.  En PY3 es nativo
else:
    import urllib                                               # Usamos el nativo de PY2 que es más rápido

import re

from core import httptools
from core import scrapertools
from platformcode import logger


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    page_url = page_url.replace("amp;", "")
    data = httptools.downloadpage(page_url).data
    logger.debug("data=" + data)
    video_urls = []
    patron = "video_src.*?(http.*?)%22%2C%22video_timestamp"
    matches = re.compile(patron, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for match in matches:
        videourl = match
        videourl = videourl.replace('%5C', '')
        videourl = urllib.unquote(videourl)
        video_urls.append(["[facebook]", videourl])
    for video_url in video_urls:
        logger.debug("%s - %s" % (video_url[0], video_url[1]))
    return video_urls

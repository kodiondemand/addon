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

from core import httptools
from core import scrapertools
from platformcode import logger, config


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "File was deleted" in data or "Page Cannot Be Found" in data or "<title>Video not found" in data:
        return False,  config.get_localized_string(70449) % "vevio"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    video_urls = []
    post = {}
    post = urllib.urlencode(post)
    url = page_url
    data = httptools.downloadpage("https://vev.io/api/serve/video/" + scrapertools.find_single_match(url, "embed/([A-z0-9]+)"), post=post).data
    bloque = scrapertools.find_single_match(data, 'qualities":\{(.*?)\}')
    matches = scrapertools.find_multiple_matches(bloque, '"([^"]+)":"([^"]+)')
    for res, media_url in matches:
        video_urls.append(
            [scrapertools.get_filename_from_url(media_url)[-4:] + " (" + res + ") [vevio.me]", media_url])
    return video_urls

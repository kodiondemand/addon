# -*- coding: utf-8 -*-
import sys

from platformcode import config

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
from platformcode import logger


def test_video_exists(page_url):
    return False, "[Vidup] Servidor Deshabilitado"
    logger.debug("(page_url='%s')" % page_url)
    page = httptools.downloadpage(page_url)
    url = page.url
    if "Not Found" in page.data or "/404" in url:
        return False,  config.get_localized_string(70449) % "Vidup"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    video_urls = []
    post= {}
    post = urllib.urlencode(post)
    headers = {"Referer":page_url}
    url = httptools.downloadpage(page_url, follow_redirects=False, headers=headers, only_headers=True).headers.get("location", "")
    logger.error(url)
    data = httptools.downloadpage("https://vidup.io/api/serve/video/" + scrapertools.find_single_match(url, "embed.([A-z0-9]+)"), post=post).data
    bloque = scrapertools.find_single_match(data, 'qualities":\{(.*?)\}')
    matches = scrapertools.find_multiple_matches(bloque, '"([^"]+)":"([^"]+)')
    for res, media_url in matches:
        video_urls.append(
            [scrapertools.get_filename_from_url(media_url)[-4:] + " (" + res + ") [vidup.tv]", media_url])
    video_urls.reverse()
    return video_urls

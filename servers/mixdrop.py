# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Mixdrop By Alfa development Group
# --------------------------------------------------------

from core import httptools, servertools
from core import scrapertools
from lib import jsunpack
from platformcode import logger, config


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    global data
    data = httptools.downloadpage(page_url).data

    if 'window.location' in data:
        domain = 'https://' + servertools.get_server_host('mixdrop')[0]
        url = domain + scrapertools.find_single_match(data, "window\.location\s*=\s*[\"']([^\"']+)")
        data = httptools.downloadpage(url).data

    if "<h2>WE ARE SORRY</h2>" in data or '<title>404 Not Found</title>' in data:
        return False, config.getLocalizedString(70449) % "MixDrop"
    return True, ""


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    videoUrls = []
    ext = 'mp4'

    global data
    packed = scrapertools.find_single_match(data, r'(eval.*?)</script>')
    unpacked = jsunpack.unpack(packed)

    # mixdrop like to change var name very often, hoping that will catch every
    list_vars = scrapertools.findMultipleMatches(unpacked, r'MDCore\.\w+\s*=\s*"([^"]+)"')
    for var in list_vars:
        if '.mp4' in var:
            media_url = var
            break
    else:
        media_url = ''
    if not media_url.startswith('http'):
        media_url = 'http:' + media_url
    videoUrls.append({'type':ext, 'url': media_url})

    return videoUrls

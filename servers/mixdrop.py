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

    if "<h2>WE ARE SORRY</h2>" in data or "<h2>ALMOST THERE</h2>" in data or '<title>404 Not Found</title>' in data:
        return False, config.get_localized_string(70449) % "MixDrop"

    if 'window.location' in data:
        domain = 'https://' + servertools.get_server_host('mixdrop')[0]
        url = domain + scrapertools.find_single_match(data, "window\.location\s*=\s*[\"']([^\"']+)")
        data = httptools.downloadpage(url).data

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    video_urls = []
    ext = '.mp4'

    global data
    packed = scrapertools.find_single_match(data, r'(eval.*?)</script>')
    unpacked = jsunpack.unpack(packed)

    # mixdrop like to change var name very often, hoping that will catch every
    list_vars = scrapertools.find_multiple_matches(unpacked, r'MDCore\.\w+\s*=\s*"([^"]+)"')
    for var in list_vars:
        if '.mp4' in var:
            media_url = var
            break
    else:
        media_url = ''
    if not media_url.startswith('http'):
        media_url = 'http:%s' % media_url
    video_urls.append(["%s [Mixdrop]" % ext, media_url])

    return video_urls


def get_filename(page_url):
    title = httptools.downloadpage(page_url.replace('/e/', '/f/')).data.split('<title>')[1].split('</title>')[0]
    prefix = 'MixDrop - Watch '
    if title.startswith(prefix):
        return title[len(prefix):]
    return ""

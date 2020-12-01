# -*- coding: utf-8 -*-
# Icarus pv7
# Fix dentaku65

try:
    import urlparse
except:
    import urllib.parse as urlparse

from core import httptools
from core import scrapertools
from platformcode import logger, config


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "We're Sorry" in data:
        return False, config.get_localized_string(70292) % "Vidcloud"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)

    video_urls = []

    data = httptools.downloadpage(page_url).data

    url = scrapertools.find_single_match(data, "url: '([^']+)',")

    if url:
        headers = dict()
        headers['X-Requested-With'] = "XMLHttpRequest"

        token = scrapertools.find_single_match(data, 'set-cookie: vidcloud_session=(.*?);')
        token = token.replace("%3D", "")
        if token:
            headers['vidcloud_session'] = token

        referer = scrapertools.find_single_match(data, "pageUrl = '([^']+)'")
        if referer:
            headers['Referer'] = referer

        page_url = urlparse.urljoin(page_url, url)
        data = httptools.downloadpage(page_url, headers=headers).data
        data = data.replace('\\\\', '\\').replace('\\','')

        media_urls = scrapertools.find_multiple_matches(data, '\{"file"\s*:\s*"([^"]+)"\}')

        for media_url in media_urls:
            ext = "mp4"
            if "m3u8" in media_url:
                ext = "m3u8"
            video_urls.append(["%s [Vidcloud" % ext, media_url])

    for video_url in video_urls:
        logger.debug("%s - %s" % (video_url[0], video_url[1]))
    return video_urls


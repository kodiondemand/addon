# -*- coding: utf-8 -*-
# Icarus pv7
# Fix dentaku65

import urlparse

from core import httptools
from core import scrapertools
from platformcode import logger, config


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "Not Found" in data or "File was deleted" in data:
        return False, config.get_localized_string(70292) % "vcstream"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)

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
        data = httptools.downloadpage(page_url, headers=headers, verify=False).data
        data = data.replace('\\\\', '\\').replace('\\','')

        media_urls = scrapertools.find_multiple_matches(data, '\{"file"\s*:\s*"([^"]+)"\}')

        for media_url in media_urls:
            ext = "mp4"
            if "m3u8" in media_url:
                ext = "m3u8"
            import urllib2
            import ssl
            context = ssl._create_unverified_context()
            video_urls.append(["%s [vcstream]" % ext, media_url, urllib2.HTTPSHandler(context=context)])

    for video_url in video_urls:
        logger.info("%s - %s" % (video_url[0], video_url[1]))
    return video_urls


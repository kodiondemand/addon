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
        return False, config.getLocalizedString(70292) % "Vidcloud"

    return True, ""


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)

    videoUrls = []

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

        media_urls = scrapertools.findMultipleMatches(data, '\{"file"\s*:\s*"([^"]+)"\}')

        for media_url in media_urls:
            ext = "mp4"
            if "m3u8" in media_url:
                ext = "m3u8"
            videoUrls.append({'type':ext, 'url':media_url})

    # for videoUrl in videoUrls:
    #     logger.debug("%s - %s" % (videoUrl[0], videoUrl[1]))
    return videoUrls


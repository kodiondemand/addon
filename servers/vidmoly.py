# -*- coding: utf-8 -*-

from core import httptools, support
from platformcode import logger, config


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    global data
    resp = httptools.downloadpage(page_url)
    data = resp.data
    if resp.code == 404 or 'Video is processing now' in data:
        return False, config.getLocalizedString(70449) % "Vidmoly"
    return True, ""


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    global data
    videoUrls = support.get_jwplayer_mediaUrl(data, 'Vidmoly')
    for url in videoUrls.items:
        logger.debug(url)
        url[url] = url['url'].replace(',','').replace('.urlset','').replace('/hls','') + '|Referer=' + page_url

    return videoUrls

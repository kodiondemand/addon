# -*- coding: utf-8 -*-

from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    return True, ""


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    videoUrls = []
    data = scrapertools.httptools.downloadpage(page_url).data
    media_url = scrapertools.find_single_match(data, 'var\s+video_source\s+\=\s+"([^"]+)"')
    if "cache-1" in media_url:
        videoUrls.append({'type':scrapertools.get_filename_from_url(media_url).split('.')[-1], 'url':media_url})
        videoUrls.append({'type':scrapertools.get_filename_from_url(media_url).split('.')[-1], 'url':media_url.replace("cache-1", "cache-2")})
    elif "cache-2" in media_url:
        videoUrls.append({'type':scrapertools.get_filename_from_url(media_url).split('.')[-1], 'url':media_url.replace("cache-2", "cache-1")})
        videoUrls.append({'type':scrapertools.get_filename_from_url(media_url).split('.')[-1], 'url':media_url})
    else:
        videoUrls.append({'type':scrapertools.get_filename_from_url(media_url).split('.')[-1], 'url':media_url})
    # for videoUrl in videoUrls:
    #     logger.debug("%s - %s" % (videoUrl[0], videoUrl[1]))
    return videoUrls

# -*- coding: utf-8 -*-

from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    video_urls = []
    data = scrapertools.httptools.downloadpage(page_url).data
    media_url = scrapertools.find_single_match(data, 'var\s+video_source\s+\=\s+"([^"]+)"')
    if "cache-1" in media_url:
        video_urls.append([scrapertools.get_filename_from_url(media_url)[-4:] + " (cache1) [sendvid]", media_url])
        video_urls.append([scrapertools.get_filename_from_url(media_url)[-4:] + " (cache2) [sendvid]",
                           media_url.replace("cache-1", "cache-2")])
    elif "cache-2" in media_url:
        video_urls.append([scrapertools.get_filename_from_url(media_url)[-4:] + " (cache1) [sendvid]",
                           media_url.replace("cache-2", "cache-1")])
        video_urls.append([scrapertools.get_filename_from_url(media_url)[-4:] + " (cache2) [sendvid]", media_url])
    else:
        video_urls.append([scrapertools.get_filename_from_url(media_url)[-4:] + " [sendvid]", media_url])
    for video_url in video_urls:
        logger.debug("%s - %s" % (video_url[0], video_url[1]))
    return video_urls

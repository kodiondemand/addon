# -*- coding: utf-8 -*-

from platformcode import logger
from core import scrapertools


def test_video_exists(page_url):
    return True, ""

# Returns an array of possible video url's from the page_url
def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    videoUrls=[{'type':scrapertools.get_filename_from_url(page_url).split('.')[-1], 'url':page_url}]

    return videoUrls

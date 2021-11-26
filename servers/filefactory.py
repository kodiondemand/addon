# -*- coding: utf-8 -*-

from platformcode import logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)

    return True, ""


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    videoUrls = []
    return videoUrls

# -*- coding: utf-8 -*-

from core import httptools
from platformcode import logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if '<h2 class="error">Download error</h2>' in data:
        return False, "El enlace no es válido<br/>o ha sido borrado de gigasize"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    video_urls = []

    return video_urls

# -*- coding: utf-8 -*-
# -*- Server Fex -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-
from core import httptools
from platformcode import config
from platformcode import logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url, follow_redirects=False)

    if data.code == 404:
        return False,  config.getLocalizedString(70449) % "Fex"

    return True, ""

def get_videoUrl(page_url, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    videoUrls = []
    data = httptools.downloadpage(page_url, follow_redirects=False, only_headers=True)
    logger.debug(data.headers)
    url = data.headers['location']
    videoUrls.append({'url':url})
    return videoUrls

# -*- coding: utf-8 -*-

import re
from core import httptools
from core import jsontools
from platformcode import logger, config

def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    global data

    # page_url = re.sub('://[^/]+/', '://feurl.com/', page_url)
    page = httptools.downloadpage(page_url)
    data = page.data
    if "Sorry 404 not found" in data or "This video is unavailable" in data or "Sorry this video is unavailable:" in data:
        return False,  config.getLocalizedString(70449) % "fembed"

    page_url = page.url
    page_url = page_url.replace("/f/", "/v/")
    page_url = page_url.replace("/v/", "/api/source/")
    data = httptools.downloadpage(page_url, post={}).json
    logger.debug(data)
    if "Video not found or" in data or "We are encoding this video" in data:
        return False, config.getLocalizedString(70449) % "Fembed"
    return True, ""


def get_videoUrl(page_url, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    videoUrls = []
    for file in data['data']:
        media_url = file['file']
        label = file['label']
        extension = file['type']
        videoUrls.append({'type':extension, 'res':label, 'url':media_url})
    # videoUrls.sort(key=lambda x: int(x[0].split()[1].replace('p','')))
    return videoUrls

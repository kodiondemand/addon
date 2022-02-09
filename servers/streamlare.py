# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector streamlare By Alfa development Group
# --------------------------------------------------------
import base64

from core import httptools
from core import scrapertools
from platformcode import logger, config


def test_video_exists(page_url):
    global data
    logger.info("(page_url='%s')" % page_url)
    response = httptools.downloadpage(page_url)
    data = response.data
    if not response.success or "Not Found" in response.data or "File was deleted" in data \
            or "is no longer available" in data:
        return False, config.get_localized_string(70449) % "Streamlare"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    global data
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    id = scrapertools.find_single_match(page_url, '/e/(\w+)')
    post = {"id": id}
    token = scrapertools.find_single_match(data, '<meta name="csrf-token" content="([^"]+)')
    data = httptools.downloadpage("https://streamlare.com/api/video/get", post=post, headers={'X-CSRF-TOKEN': token, 'X-Requested-With': 'XMLHttpRequest'}).json
    src = data["result"]["Original"]["src"]
    media_url = ''.join([chr(51 ^ c) for c in base64.b64decode(src)])
    video_urls.append(["MP4", media_url])
    return video_urls


def get_filename(page_url):
    from core import jsontools
    file = jsontools.load(scrapertools.decodeHtmlentities(httptools.downloadpage(page_url).data.split(':file="')[1].split('"')[0]))
    return file['name']

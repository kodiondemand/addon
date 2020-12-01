# -*- coding: utf-8 -*-
import time

from core import httptools
from core import scrapertools
from platformcode import config
from platformcode import logger

headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Mobile Safari/537.36'}


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "Archive no Encontrado" in data:
        return False,  config.get_localized_string(70449) % "bdupload"

    return True, ""


def get_video_url(page_url, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    post = ""
    patron = '(?s)type="hidden" name="([^"]+)".*?value="([^"]*)"'
    match = scrapertools.find_multiple_matches(data, patron)
    for nombre, valor in match:
        post += nombre + "=" + valor + "&"
    time.sleep(1)
    data1 = httptools.downloadpage(page_url, post = post, headers = headers).data
    patron = "window.open\('([^']+)"
    file = scrapertools.find_single_match(data1, patron).replace(" ","%20")
    file += "|User-Agent=" + httptools.get_user_agent()
    file += "&Host=fs30.indifiles.com:182"
    video_urls = []
    videourl = file
    video_urls.append([".MP4 [bdupload]", videourl])
    return video_urls

# -*- coding: utf-8 -*-
# import re
from core import httptools
from core import scrapertools
from platformcode import logger, config
import codecs


def test_video_exists(page_url):
    global data
    data = httptools.downloadpage(page_url).data
    if 'File was deleted' in data:
        return False, config.get_localized_string(70449) % 'YouDbox'
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    global data
    video_urls = []
    list = scrapertools.find_single_match(data, 'var [a-zA-Z0-9]+ = ([^\]]+)').replace('[', '').replace('"', '').replace('\\x', '').replace(',', ' ')
    list = list.split()[::-1]
    url =""
    for elem in list:
        decoded = codecs.decode(elem, "hex")
        url += decoded.decode("utf8")
    url = scrapertools.find_single_match(url, '<source src="([^"]+)"')
    video_urls.append(["[youdbox]", url])
    return video_urls

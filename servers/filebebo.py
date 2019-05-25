# -*- coding: utf-8 -*-
# -*- Server Filebebo -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re

from core import httptools
from core import scrapertools
from platformcode import logger


def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = get_source(page_url)

    if "File was deleted" in data or "File Not Found" in data:
        return False, "[Filebebo] El video ha sido borrado"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    data = get_source(page_url)
    url = scrapertools.find_single_match(data, "<source src=(.*?) type='video/.*?'")
    video_urls.append(['Filebebo', url])

    return video_urls

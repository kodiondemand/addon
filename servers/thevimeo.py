# -*- coding: utf-8 -*-
# -*- Server Thevimeo -*-

import re

from core import httptools


def get_source(url):
    #logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def test_video_exists(page_url):
    #logger.info("(page_url='%s')" % page_url)
    data = get_source(page_url)

    if "File was deleted" in data or "File Not Found" in data:
        return False, "[Thevimeo] El video ha sido borrado"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    #logger.info("url=" + page_url)
    video_urls = []
    data = get_source(page_url)
    #logger.debug(data)
    patron = "{file:(.*?),label:(.*?),"

    matches = re.compile(patron, re.DOTALL).findall(data)
    #url = scrapertools.find_single_match(data, "sources.*?{file:(.*?),")
    for url, qual in matches:
        url = url.replace("\/", "/")
        qual = qual.replace("M\u00f3vil","360")
        video_urls.append([qual+"p [Thevimeo]", url])
    video_urls.sort(key=lambda it: int(it[0].split("p ", 1)[0]))

    return video_urls

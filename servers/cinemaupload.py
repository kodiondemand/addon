# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Cinemaupload By Alfa development Group
# --------------------------------------------------------
import re

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url)
    if data.code == 404:
        return False, "[CinemaUpload] El archivo no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    patron = "source: '([^']+)',"
    matches = scrapertools.find_multiple_matches(data, patron)
    for url in matches:
        video_urls.append(['.m3u8 [CinemaUpload]', url])
    return video_urls

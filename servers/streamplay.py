# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger

headers = [['User-Agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0']]


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    referer = re.sub(r"embed-|player-", "", page_url)[:-5]
    data = httptools.downloadpage(page_url, headers={'Referer': referer}).data
    if data == "File was deleted":
        return False, "[Streamplay] El archivo no existe o ha sido borrado"
    elif "Video is processing now" in data:
        return False, "[Streamplay] El archivo se está procesando"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info()
    itemlist = []

    referer = re.sub(r"embed-|player-", "", page_url)[:-5]

    data = httptools.downloadpage(page_url, headers={'Referer': referer}).data

    if data == "File was deleted":
        return "El archivo no existe o ha sido borrado"

    packed = scrapertools.find_single_match(data, "<script type=[\"']text/javascript[\"']>(eval.*?)</script>")
    unpacked = jsunpack.unpack(packed)

    url = scrapertools.find_single_match(unpacked, '(http[^,]+\.mp4)')

    from lib import alfaresolver
    itemlist.append([".mp4" + " [streamplay]", alfaresolver.decode_video_url(url, data)])

    itemlist.sort(key=lambda x: x[0], reverse=True)

    return itemlist

# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector playtube By Alfa development Group
# --------------------------------------------------------
from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger, config


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    data = httptools.downloadpage(page_url)
    if data.code == 404 or "File is no longer available" in data.data:
        return False, config.get_localized_string(70449) % 'PlayTube'
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    pack = scrapertools.find_single_match(data.data, 'p,a,c,k,e,d.*?</script>')
    unpacked = jsunpack.unpack(pack)
    url = scrapertools.find_single_match(unpacked, 'file:"([^"]+)') + "|Referer=%s" % page_url
    video_urls.append(['m3u8 [PlayTube]', url] )
    return video_urls
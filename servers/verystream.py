# -*- coding: utf-8 -*-
# Verystream server tool
# Developed by KOD for KOD
# KOD - Kodi on Demand Team

from core import httptools
from core import scrapertools
from platformcode import config, logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    header = {}
    if "|" in page_url:
        page_url, referer = page_url.split("|", 1)
        header = {'Referer': referer}
    data = httptools.downloadpage(page_url, headers=header, cookies=False).data
    if 'not found!' in data:
        data = httptools.downloadpage(page_url.replace("/e/", "/stream/"), headers=header, cookies=False).data
        if 'not found!' in data:
            return False, config.get_localized_string(70449) % "Verystream"

    return True, ""

def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info()
    itemlist = []

    header = {}
    if "|" in page_url:
        page_url, referer = page_url.split("|", 1)
        header = {'Referer': referer}

    data = httptools.downloadpage(page_url, cookies=False, headers=header).data
    subtitle = scrapertools.find_single_match(data, '<track kind="captions" src="([^"]+)" srclang="it"')

    try:
        code = scrapertools.find_single_match(data, '<p style="" class="" id="videolink">(.*?)</p>' )
        url = "https://verystream.com/gettoken/" + code + "?mime=true"
        url = httptools.downloadpage(url, only_headers=True, follow_redirects=False).headers.get('location')
        extension = scrapertools.find_single_match(url, '(\..{,3})\?')
        itemlist.append([extension, url, 0,subtitle])

    except Exception:
        logger.info()
        if config.get_setting('api', __file__):
            url = get_link_api(page_url)
            extension = scrapertools.find_single_match(url, '(\..{,3})\?')
            if url:
                itemlist.append([extension, url, 0,subtitle])
    logger.debug(itemlist)

    return itemlist


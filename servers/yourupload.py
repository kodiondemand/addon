# -*- coding: utf-8 -*-
from core import httptools
from core import scrapertools
from platformcode import config
from platformcode import logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    global data
    
    data = httptools.downloadpage(page_url).data
    if "File was deleted" in data or "File not found" in data or 'og:video">' in data:
        return False,  config.get_localized_string(70449) % "Yourupload"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    video_urls = []
    
    referer = {'Referer': page_url}
    url = scrapertools.find_single_match(data, '<meta property="og:video" content="([^"]+)"')
    
    if not url:
        if "download" in page_url:
            patron = 'class="btn btn-success" href="([^"]+)"'
            url = scrapertools.find_single_match(data, patron).replace('amp;', '')
        else:
            url = scrapertools.find_single_match(data, "file:\s*'([^']+)'")
    if url:
        if "vidcache" not in url:
            url = "https://www.yourupload.com%s" % url
            media_url = httptools.downloadpage(url, headers=referer, only_headers=True).url
            ext = media_url[-4:]
            media_url += "|Referer=%s" % url
        else:
            ext = url[-4:]
            media_url = url +"|Referer=%s" % page_url
        
        video_urls.append([ext + " [yourupload]", media_url])
    
    return video_urls

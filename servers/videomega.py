# -*- coding: utf-8 -*-
from core import httptools
from core import scrapertools
from platformcode import logger


def get_video_url(page_url, video_password):
    logger.debug("(page_url='%s')" % page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    m= scrapertools.find_single_match(data, '<link href="(Br74.*?==.css)"')
    url= "https://www.videomega.co/streamurl/JaV1laMGUzNzJjYzg2ZTZhYzg2NzdjNzNhYThlMTAwNTQxMTVzZWN1cmUZaoKJEa.css/"
    post="myreason=%s&saveme=/videojs/crexcode/video-js.min.css" %m
    url = httptools.downloadpage(url, post=post).data
    url = url.replace(" ", "")
    data=httptools.downloadpage(url).data
    url = scrapertools.find_single_match(data, '<source src="([^"]+)"')
    video_urls.append(["[videomega]", url])
    return video_urls


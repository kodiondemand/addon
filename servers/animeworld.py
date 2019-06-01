# -*- coding: utf-8 -*-
import urllib

from core import httptools, jsontools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    post = urllib.urlencode({'r': '', 'd': 'animeworld.biz'})
    data_json = httptools.downloadpage(page_url.replace('/v/', '/api/source/'), headers=[['x-requested-with', 'XMLHttpRequest']], post=post).data
    json = jsontools.load(data_json)
    if not json['data']:
        return False, "Video not found"

    return True, ""


def get_video_url(page_url, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    post = urllib.urlencode({'r': '', 'd': 'animeworld.biz'})
    data_json = httptools.downloadpage(page_url.replace('/v/', '/api/source/'), headers=[['x-requested-with', 'XMLHttpRequest']], post=post).data
    json = jsontools.load(data_json)
    if json['data']:
        for file in json['data']:
            media_url = file['file']
            label = file['label']
            extension = file['type']
            video_urls.append([label + " " + extension + ' [animeworld]', media_url])


    return video_urls

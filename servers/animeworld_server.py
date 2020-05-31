# -*- coding: utf-8 -*-
import sys
if sys.version_info[0] >= 3:
    import urllib.parse as urllib
else:
    import urllib

from core import httptools, jsontools
from platformcode import logger, config


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    post = urllib.urlencode({'r': '', 'd': 'animeworld.biz'})
    data_json = httptools.downloadpage(page_url.replace('/v/', '/api/source/'), headers=[['x-requested-with', 'XMLHttpRequest']], post=post).data
    global json
    json = jsontools.load(data_json)
    if not json['data']:
        return False, config.get_localized_string(70449) % "AnimeWorld"

    return True, ""


def get_video_url(page_url, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    global json
    if json['data']:
        for file in json['data']:
            media_url = file['file']
            label = file['label']
            extension = file['type']
            video_urls.append([label + " " + extension + ' [AnimeWorld]', media_url])


    return video_urls

# -*- coding: utf-8 -*-
import requests, sys
from core import httptools, support
from platformcode import config, logger

if sys.version_info[0] >= 3: from concurrent import futures
else: from concurrent_py2 import futures

headers = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14',
           'content-type': 'application/json;charset=UTF-8',
           'Referer': 'https://streamingcommunity.net'}

def test_video_exists(page_url):
    global data
    logger.debug('page url=', page_url)
    response = httptools.downloadpage(page_url, headers=headers)

    if response.code == 404:
        return False, config.get_localized_string(70449) % 'StreamingCommunity'
    else:
        data = response.data
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    video_urls = []
    url = support.match(data.replace('&quot;','"').replace('\\',''), patron=r'video_url"\s*:\s*"([^"]+)"').match
    def videourls(res):
        newurl = '{}/{}'.format(url, res)
        if requests.head(newurl, headers=headers).status_code == 200:
            video_urls.append(["m3u8 {} [StreamingCommunity]".format(res), newurl])

    with futures.ThreadPoolExecutor() as executor:
        for res in ['480p', '720p', '1080p']:
            executor.submit(videourls, res)
    if not video_urls: video_urls = [["m3u8 [StreamingCommunity]", url]]
    else: video_urls.sort(key=lambda url: int(support.match(url[0], patron=r'(\d+)p').match))
    return video_urls

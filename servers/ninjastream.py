# -*- coding: utf-8 -*-
import json
from core import support, httptools
from platformcode import logger, config

def test_video_exists(page_url):
    global data
    logger.debug('page url=', page_url)
    response = httptools.downloadpage(page_url)

    if response.code == 404:
        return False, config.get_localized_string(70449) % 'NinjaStream'
    else:
        data = response.data
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    global data
    logger.debug("URL", page_url)
    video_urls = []
    # support.dbg()

    headers = {'User-Agent': httptools.get_user_agent(),
               'Referer': page_url,
               'Origin': 'https://ninjastream.to',
               'X-Requested-With': 'XMLHttpRequest'}

    apiUrl = 'https://ninjastream.to/api/video/get'
    post = {'id':page_url.split('/')[-1]}
    data = httptools.downloadpage(apiUrl, headers=headers, post=post).json

    if data.get('result',{}).get('playlist'):
        # support.dbg()
        url = data.get('result',{}).get('playlist')

        video_urls.append([url.split('.')[-1], url + '|Referer=' + page_url])

    return video_urls

# def decode(host):
#     Host = ''
#     for n in range(len(host)):
#         Host += chr(ord(host[n]) ^ ord('2'))
#     return Host
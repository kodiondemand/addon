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

    h = json.loads(support.match(data, patron='stream="([^"]+)"').match.replace('&quot;','"'))
    baseurl = decode(h['host']) + h['hash']
    matches = support.match(baseurl + '/index.m3u8', patron=r'RESOLUTION=\d+x(\d+)\s*([^\s]+)').matches

    for quality, url in matches:
        video_urls.append(["{} {}p [NinjaStream]".format(url.split('.')[-1], quality), '{}/{}'.format(baseurl, url)])

    return video_urls

def decode(host):
    Host = ''
    for n in range(len(host)):
        Host += chr(ord(host[n]) ^ ord('2'))
    return Host
# -*- coding: utf-8 -*-

from core import httptools, support, jsontools
from platformcode import config, logger


def test_video_exists(page_url):
    global data
    logger.debug('page url=', page_url)
    response = httptools.downloadpage(page_url)

    if response.code == 404:
        return False, config.get_localized_string(70449) % 'Paramount'
    else:
        data = response.data
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    # from core.support import dbg;dbg()
    qualities = []
    video_urls = []
    mgid = support.match(data, patron=r'uri":"([^"]+)"').match
    url = 'https://media.mtvnservices.com/pmt/e1/access/index.html?uri=' + mgid + '&configtype=edge&ref=' + page_url
    ID, rootUrl = support.match(url, patron=[r'"id":"([^"]+)",',r'brightcove_mediagenRootURL":"([^"]+)"']).matches
    url = jsontools.load(support.match(rootUrl.replace('&device={device}','').format(uri = ID)).data)['package']['video']['item'][0]['rendition'][0]['src']
    urls = support.match(url, patron=r'RESOLUTION=(\d+x\d+).*?(http[^ ]+)').matches
    for quality, url in urls:
        quality = quality.split('x')[0]
        if quality not in qualities:
            qualities.append(quality)
            video_urls.append(["hls {}p [Paramount]".format(quality), url])
    video_urls.sort(key=lambda url: int(support.match(url[0], patron=r'(\d+)p').match))
    return video_urls

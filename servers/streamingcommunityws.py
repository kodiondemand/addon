# -*- coding: utf-8 -*-
from wsgiref import headers
from core import httptools, support, filetools
from platformcode import logger, config
UA = httptools.random_useragent()


def test_video_exists(page_url):
    global scws_id
    logger.debug('page url=', page_url)

    if page_url.isdigit():
        scws_id = page_url
    else:
        scws_id = support.match(page_url, patron=r'scws_id[^:]+:(\d+)').match

    if not scws_id:
        return False, config.get_localized_string(70449) % 'StreamingCommunityWS'
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    from time import time
    from base64 import b64encode
    from hashlib import md5

    global scws_id
    video_urls = list()

    # clientIp = httptools.downloadpage(f'https://scws.work/videos/{scws_id}').json.get('client_ip')
    clientIp = httptools.downloadpage('http://ip-api.com/json/').json.get('query')
    if clientIp:
        expires = int(time() + 172800)
        token = b64encode(md5('{}{} Yc8U6r8KjAKAepEA'.format(expires, clientIp).encode('utf-8')).digest()).decode('utf-8').replace('=', '').replace('+', '-').replace('/', '_')
        url = 'https://scws.work/master/{}?token={}&expires={}&n=1'.format(scws_id, token, expires)
        if page_url.isdigit():
            video_urls.append(['m3u8', '{}|User-Agent={}'.format(url, UA)])
        else:
            video_urls = compose(url)

    return video_urls

def compose(url):
    subs = []
    video_urls = []
    info = support.match(url, patron=r'LANGUAGE="([^"]+)",\s*URI="([^"]+)|RESOLUTION=\d+x(\d+).*?(http[^"\s]+)', headers={'User-Agent':UA}).matches
    if info:
        for lang, sub, res, url in info:
            if sub and not logger.testMode: # ai test non piace questa parte
                if lang == 'auto': lang = 'ita-forced'
                s = config.get_temp_file(lang +'.srt')
                subs.append(s)
                filetools.write(s, support.vttToSrt(httptools.downloadpage(support.match(sub, patron=r'(http[^\s\n]+)').match).data))
            elif url:
                video_urls.append(['m3u8 [{}]'.format(res), '{}|User-Agent={}'.format(url, UA), 0, subs])
    return video_urls
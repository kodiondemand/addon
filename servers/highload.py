# -*- coding: utf-8 -*-
try:
    from urllib.parse import urlparse
except:
    from urlparse import urlparse

from core import httptools, support
from platformcode import logger, config
from functools import reduce
import base64


def test_video_exists(page_url):
    logger.info('page_url="{}"'.format(page_url))
    global data
    data = httptools.downloadpage(page_url)
    if data.code == 404 or "We can't find the video" in data.data or 'sorry' in data.data:
        return False, config.get_localized_string(70449) % "HighLoad"
    data = data.data
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)

    global data
    media_url = ''
    video_urls = []

    host = 'https://' + urlparse(page_url).netloc

    first = unhunt(support.match(data, patron =r'<head>(.+?)</head>').match)

    second_url = host + support.match(data, patron=r'src="(/assets/js/(?:master|tabber).js)').match
    second = unhunt(httptools.downloadpage(second_url).data)

    v, r1, r2 = support.match(second, patron=r'var\s*res\s*=\s*([^.]+)\.replace\("([^"]+).+?replace\("([^"]+)').match
    match = support.match(first, patron=r'var\s*{}\s*=\s*"([^"]+)'.format(v)).match

    if match:
        media_url = base64.b64decode(match.replace(r1, '').replace(r2, '')).decode('utf-8')

    if media_url:
        video_urls.append([media_url.split('.')[-1] +' [HighLoad]', media_url])
    return video_urls


def unhunt(source):
    def decode(params):
        h = params[0]
        n = params[1]
        t = int(params[2])
        e = int(params[3])
        r = ""
        i = 0
        while i < len(h):
            s = ""
            while h[i] != n[e]:
                s += h[i]
                i += 1

            for j in enumerate(n):
                s = s.replace(j[1], str(j[0]))

            r += chr(int(dehunt(s, e, 10)) - t)
            i += 1

        return r

    def dehunt(d, e, f):
        g = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+/"
        h = g[0:e]
        i = g[0:f]
        d = d[::-1]
        j = reduce(lambda a, b: a + int(h[int(b[1])]) * (e ** int(b[0])) if int(h[int(b[1])]) != -1 else None, enumerate(d), 0)
        k = ""
        while j > 0:
            k = i[int(j % f)] + k
            j = (j - (j % f)) / f

        return k or "0"

    return decode(support.match(source, patron=r'\(h,\s*u,\s*n,\s*t,\s*e,\s*r\).+}\("([^"]+)",[^,]+,\s*"([^"]+)",\s*(\d+),\s*(\d+)').match)


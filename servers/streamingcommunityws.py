# -*- coding: utf-8 -*-
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True

if PY3: 
    import urllib.parse as urllib
else: 
    import urllib
    
import ast
import xbmc

from core import httptools, support, filetools
from platformcode import logger, config
from concurrent import futures

vttsupport = False if int(xbmc.getInfoLabel('System.BuildVersion').split('.')[0]) < 20 else True


def test_video_exists(page_url):
    global iframeParams
    global urlParams
    server_url = support.scrapertools.decodeHtmlentities(support.match(page_url, patron=['<iframe [^>]+src="([^"]+)', 'embed_url="([^"]+)']).match)
    iframeParams = support.match(server_url, patron=r'''"quality":(\d+),.+window\.masterPlaylist\s+=\s+{[^{]+({[^}]+}),\s+url:\s+'([^']+)''').match

    if not iframeParams or len(iframeParams) < 2:
        return 'StreamingCommunity', 'Prossimamente'

    urlParams = urllib.parse_qs(urllib.urlsplit(server_url).query)
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    video_urls = list()

    quality, params, url = iframeParams

    masterPlaylistParams = ast.literal_eval(params)
    if 'canPlayFHD' in urlParams:
        masterPlaylistParams['h'] = 1
    if 'b' in urlParams:
        masterPlaylistParams['b'] = 1
    url =  '{}?{}'.format(url,urllib.urlencode(masterPlaylistParams))

    video_urls = [['hls [{}]'.format(quality), url]]

    return video_urls

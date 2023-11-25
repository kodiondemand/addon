# -*- coding: utf-8 -*-
import urllib.parse
import ast
import xbmc

from core import httptools, support, filetools
from platformcode import logger, config
from concurrent import futures

vttsupport = False if int(xbmc.getInfoLabel('System.BuildVersion').split('.')[0]) < 20 else True


def test_video_exists(page_url):
    global server_url
    global iframeParams

    server_url = support.scrapertools.decodeHtmlentities(support.match(page_url, patron='<iframe [^>]+src="([^"]+)').match)
    if not server_url:
        server_url = support.match(page_url, patron='embed_url="([^"]+)').match
    iframeParams = support.match(server_url, patron=['window.masterPlaylist\s=\s{\s.*params:\s(.*?}),',
                                                     '''},\s*url:\s.(http[^"']+).,''']).matches
    logger.info(iframeParams)

    if not iframeParams or len(iframeParams) < 2:
        return 'StreamingCommunity', 'Prossimamente'

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    urls = list()
    subs = list()
    local_subs = list()
    video_urls = list()

    # scws_id = urlparse(server_url).path.split('/')[-1]
    masterPlaylistParams = ast.literal_eval(iframeParams[0])
    url = iframeParams[1] + '?{}&n=1'.format(urllib.parse.urlencode(masterPlaylistParams))

    # info = support.match(url, patron=r'LANGUAGE="([^"]+)",\s*URI="([^"]+)|(http.*?rendition=(\d+)[^\s]+)').matches
    #
    # if info:
    #     for lang, sub, url, res in info:
    #         if sub:
    #             if lang == 'auto': lang = 'ita-forced'
    #             subs.append([lang, sub])
    #         elif not 'token=&' in url:
    #             urls.append([res, url])
    #
    #     if subs:
    #         local_subs = subs_downloader(subs)
    #         video_urls = [['m3u8 [{}]'.format(res), url, 0, local_subs] for res, url in urls]
    #     else:
    #         video_urls = [['m3u8 [{}]'.format(res), url] for res, url in urls]
    # else:
    video_urls = [['hls', url]]

    return video_urls


def subs_downloader(subs):
    def subs_downloader_thread(n, s):
        lang, url = s
        match = support.match(url, patron=r'(http[^\s\n]+)').match
        if match:
            data = httptools.downloadpage(match).data
            if lang == 'auto': lang = 'ita-forced'
            sub = config.get_temp_file('{}.{}'.format(lang, 'vtt' if vttsupport else 'str'))
            filetools.write(sub, data if vttsupport else support.vttToSrt(data))
            return n, sub

    local_subs = list()

    with futures.ThreadPoolExecutor() as executor:
        itlist = [executor.submit(subs_downloader_thread, n, s) for n, s in enumerate(subs)]
        for res in futures.as_completed(itlist):
            if res.result():
                local_subs.append(res.result())

    return [s[1] for s in sorted(local_subs, key=lambda n: n[0])]

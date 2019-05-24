# -*- coding: utf-8 -*-

import urllib

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    data = scrapertools.downloadpage(page_url)

    # if '<meta property="og:title" content=""/>' in data:
    # return False,"The video has been cancelled from Backin.net"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("page_url=" + page_url)

    video_urls = []

    headers = [["User-Agent", "Mozilla/5.0 (Windows NT 6.1; rv:54.0) Gecko/20100101 Firefox/54.0"]]



    # First access
    httptools.downloadpage("http://backin.net/s/streams.php?s=%s" % page_url, headers=headers)

    # xbmc.sleep(10000)
    headers.append(["Referer", "http://backin.net/%s" % page_url])
    #xbmc.sleep(10000)
    data = httptools.downloadpage("http://backin.net/stream-%s-500x400.html" % page_url, headers=headers).data
    
    data_pack = scrapertools.find_single_match(data, r"(eval.function.p,a,c,k,e,.*?)\s*</script>")
    if data_pack:
        from lib import jsunpack
        data = jsunpack.unpack(data_pack)
    logger.info("page_url=" + data)

    # URL
    url = scrapertools.find_single_match(data, r'"src"value="([^"]+)"')
    if not url:
        url = scrapertools.find_single_match(data, r'file\s*:\s*"([^"]+)"')
    logger.info("URL=" + str(url))

    # URL del vídeo
    video_urls.append([".mp4" + " [backin]", url + '|' + urllib.urlencode(dict(headers))])

    for video_url in video_urls:
        logger.info("%s - %s" % (video_url[0], video_url[1]))

    return video_urls

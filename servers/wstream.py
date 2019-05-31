# -*- coding: utf-8 -*-
# Kodi on Demand - Kodi Addon - Kodi Addon
# by DrZ3r0 - Fix Alhaziel

import re
import urllib

from core import httptools, scrapertools
from platformcode import logger

headers = [['User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0']]

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "Not Found" in data or "File was deleted" in data:
        return False, "[wstream.py] El fichero no existe o ha sido borrado"
    return True, ""

# Returns an array of possible video url's from the page_url
def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    # import web_pdb; web_pdb.set_trace()
    logger.info("[wstream.py] url=" + page_url)
    video_urls = []

    data = httptools.downloadpage(page_url, headers=headers).data.replace('https', 'http')
    # logger.info("[wstream.py] data=" + data)
    vid = scrapertools.find_multiple_matches(data, 'download_video.*?>.*?<.*?<td>([^\,,\s]+)')

    headers.append(['Referer', page_url])
    post_data = scrapertools.find_single_match(data,
                                               "</div>\s*<script type='text/javascript'>(eval.function.p,a,c,k,e,.*?)\s*</script>")
    if post_data != "":
        from lib import jsunpack
        data = jsunpack.unpack(post_data)

    media_url = scrapertools.find_multiple_matches(data, '(http.*?\.mp4)')
    _headers = urllib.urlencode(dict(headers))
    i = 0

    for media_url in media_url:
        video_urls.append([vid[i] + " mp4 [wstream] ", media_url + '|' + _headers])
        i = i + 1

    for video_url in video_urls:
        logger.info("[wstream.py] %s - %s" % (video_url[0], video_url[1]))

    return video_urls


def find_videos(data):
    encontrados = set()
    devuelve = []

    patronvideos = r"wstream.video/(?:embed-)?([a-z0-9A-Z]+)"
    logger.info("[wstream.py] find_videos #" + patronvideos + "#")
    matches = re.compile(patronvideos, re.DOTALL).findall(data)

    for match in matches:
        titulo = "[wstream]"
        url = 'http://wstream.video/%s' % match

        if url not in encontrados:
            logger.info("  url=" + url)
            devuelve.append([titulo, url, 'wstream'])
            encontrados.add(url)
        else:
            logger.info("  url duplicada=" + url)

    return devuelve

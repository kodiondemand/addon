# -*- coding: utf-8 -*-

try:
    import urllib.parse as urllib
except ImportError:
    import urllib

from core import httptools
from core import scrapertools
from platformcode import logger, config

headers = [['User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0']]

def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "Not Found" in data or "File was deleted" in data or "The file is being converted" in data or "Please try again later" in data:
        return False, config.get_localized_string(70293) % "NowVideo"
    elif "no longer exists" in data:
        return False, config.get_localized_string(70292) % "NowVideo"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    host = 'http://nowvideo.club'
    logger.debug("(nowvideo page_url='%s')" % page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    page_url_post = scrapertools.find_single_match(data, '<Form id="[^"]+" method="POST" action="([^"]+)">')
    page_url_post = page_url_post.replace('..', '')
    imhuman = '&imhuman=' + scrapertools.find_single_match(data, 'name="imhuman" value="([^"]+)"').replace(" ", "+")
    post = urllib.urlencode({k: v for k, v in scrapertools.find_multiple_matches(data, 'name="([^"]+)" value="([^"]*)"')}) + imhuman
    data = httptools.downloadpage(host + page_url_post, post=post).data
    logger.debug("nowvideo data page_url2 ='%s'" % data)

    headers.append(['Referer', page_url])
    post_data = scrapertools.find_single_match(data,"</div>\s*<script>(eval.function.p,a,c,k,e,.*?)\s*</script>")
    if post_data != "":
        from lib import jsunpack
        data = jsunpack.unpack(post_data)

    block = scrapertools.find_single_match(data, 'sources:\s*\[[^\]]+\]')
    if block: data = block

    media_urls = scrapertools.find_multiple_matches(data, '(http.*?\.mp4)')
    _headers = urllib.urlencode(dict(headers))

    for media_url in media_urls:
        #logger.debug("nowvideo data page_url2 ='%s'" % media_url)
        video_urls.append([" mp4 [nowvideo] ", media_url + '|' + _headers])

    for video_url in media_urls:
        logger.debug("[nowvideo.py] %s - %s" % (video_url[0], video_url[1]))
    
    return video_urls


def find_videos(data):
    encontrados = set()
    devuelve = []

    patronvideos = r"nowvideo.club/(?:play|videos)?([a-z0-9A-Z]+)"
    logger.debug("[nowvideo.py] find_videos #" + patronvideos + "#")
    matches = re.compile(patronvideos, re.DOTALL).findall(data)

    for match in matches:
        titulo = "[nowvideo]"
        url = 'http://nowvideo.club/%s' % match

        if url not in encontrados:
            logger.debug("  url=" + url)
            devuelve.append([titulo, url, 'nowvideo'])
            encontrados.add(url)
        else:
            logger.debug("  url duplicada=" + url)

    return devuelve

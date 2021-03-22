# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from platformcode import logger, config
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)

    if 'fastid' in page_url:  # fastid
        page_url = httptools.downloadpage(page_url, follow_redirects=False, only_headers=True).headers['location']
        page_url = "http://backin.net/stream-%s-500x400.html" % scrapertools.find_single_match(page_url, 'backin.net/([a-zA-Z0-9]+)')
    global data
    data = httptools.downloadpage(page_url).data

    if 'File Not Found' in data:
        return False, config.get_localized_string(70449) % "backin"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("page_url=" + page_url)

    video_urls = []

    headers = [["User-Agent", "Mozilla/5.0 (Windows NT 6.1; rv:54.0) Gecko/20100101 Firefox/54.0"]]

    global data
    
    data_pack = scrapertools.find_single_match(data, r"(eval.function.p,a,c,k,e,.*?)\s*</script>")
    if data_pack:
        from lib import jsunpack
        data = jsunpack.unpack(data_pack)
    logger.debug("page_url=" + data)

    # URL
    url = scrapertools.find_single_match(data, r'"src"value="([^"]+)"')
    if not url:
        url = scrapertools.find_single_match(data, r'file\s*:\s*"([^"]+)"')
    logger.debug("URL=" + str(url))

    # URL del vídeo
    video_urls.append([".mp4" + " [backin]", url])

    for video_url in video_urls:
        logger.debug("%s - %s" % (video_url[0],  httptools.get_url_headers(video_url[1])))

    return video_urls

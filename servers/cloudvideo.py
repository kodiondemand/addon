# Conector Cloudvideo By Alfa development Group
# --------------------------------------------------------

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url)
    if data.code == 404:
        return False, "[Cloud] El archivo no existe o  ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    enc_data = scrapertools.find_single_match(data, "type='text/javascript'>(.*?)</script>")
    dec_data = jsunpack.unpack(enc_data)
    sources = scrapertools.find_single_match(data, "<source(.*?)</source")
    patron = 'src="([^"]+)'
    matches = scrapertools.find_multiple_matches(sources, patron)
    for url in matches:
        quality = 'm3u8'
        video_url = url
        if 'label' in url:
            url = url.split(',')
            video_url = url[0]
            quality = url[1].replace('label:','')
        video_urls.append(['cloudvideo [%s]' % quality, video_url])
    return video_urls

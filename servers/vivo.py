# Conector Vivo By Alfa development Group
# --------------------------------------------------------
import base64

from core import httptools
from core import scrapertools
from platformcode import config
from platformcode import logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url)
    if data.code == 404:
        return False,  config.get_localized_string(70449) % "Vivo"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    enc_data = scrapertools.find_single_match(data, 'data-stream="([^"]+)')
    dec_data = base64.b64decode(enc_data)
    video_urls.append(['vivo', dec_data])
    return video_urls

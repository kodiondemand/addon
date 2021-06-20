from core import httptools
from core import scrapertools, support
from lib import jsunpack
from platformcode import logger, config


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    global data
    data = httptools.downloadpage(page_url).data

    if "File Not Found" in data or "File was deleted" in data:
        return False, config.get_localized_string(70449) % "MaxStream"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    global data
    packed = scrapertools.find_single_match(data, r'(eval.*?)</script>')
    unpacked = jsunpack.unpack(packed)
    return support.get_jwplayer_mediaurl(unpacked, 'MaxStream')

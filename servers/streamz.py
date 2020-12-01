# -*- coding: utf-8 -*-
import re
from core import httptools
from core import scrapertools
from platformcode import logger, config
from lib import jsunpack


def test_video_exists(page_url):
    global data
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data

    if "<font color=\"red\"><b>File not found, sorry!" in data:
        return False, config.get_localized_string(70449) % "streamZ"
    return True, ""


def get_video_url(page_url, video_password):
    logger.debug("(page_url='%s')" % page_url)
    video_urls = []
    from core.support import match
    matches = match(data, patron=r'(eval\(function\(p,a,c,k,e,d\).*?)\s+</script>').matches
    unpacked = ''
    for packed in matches:
        unpacked += jsunpack.unpack(packed) + '\n'

    urls = match(unpacked, patron=r"videojs\d+[^;]+[^']+'[^']+'[^']+'(https://streamz.*?/get.*?.dll)").matches

    for url in urls:
        url = url + "|User-Agent=%s" % httptools.get_user_agent()
        if not video_urls or url not in video_urls[-1]:
            video_urls.append(["[streamZ]", url])

    return video_urls
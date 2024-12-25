# -*- coding: utf-8 -*-

from six.moves import urllib

from core import httptools, support
from core import scrapertools
from platformcode import logger, config
from lib import jsunpack
import re

def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    global data
    data = httptools.downloadpage(page_url).data

    if "File Not Found" in data:
        return False, config.get_localized_string(70449) % "Dropload"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug(" url=" + page_url)

    global data

    data_pack = scrapertools.find_single_match(data, "</div>\n\s*<script[^>]+>(eval.function.p,a,c,k,e,.*?)\s*</script>")
    if data_pack != "":
        data = jsunpack.unpack(data_pack)
        data = re.sub(r'\b([a-zA-Z]+):("[^"]+"[,\n}])', r'"\1":\2', data)

    _headers = urllib.parse.urlencode(httptools.default_headers)
    video_urls = support.get_jwplayer_mediaurl(data, 'dropload')

    return video_urls

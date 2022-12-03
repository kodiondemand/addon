# -*- coding: utf-8 -*-

try:
    import urllib.parse as urllib
except ImportError:
    import urllib

from core import httptools, support
from core import scrapertools
from platformcode import logger, config


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
    # vres = scrapertools.find_multiple_matches(data, 'nowrap[^>]+>([^,]+)')
    # if not vres: vres = scrapertools.find_multiple_matches(data, '<td>(\d+x\d+)')

    data_pack = scrapertools.find_single_match(data, "</div>\n\s*<script[^>]+>(eval.function.p,a,c,k,e,.*?)\s*</script>")
    if data_pack != "":
        from lib import jsunpack
        data = jsunpack.unpack(data_pack)

    _headers = urllib.urlencode(httptools.default_headers)
    video_urls = support.get_jwplayer_mediaurl(data, 'dropload')

    return video_urls

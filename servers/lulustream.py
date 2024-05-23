# -*- coding: utf-8 -*-

from core import httptools, scrapertools, support
from platformcode import logger, config


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    page = httptools.downloadpage(page_url)
    global matches
    data = page.data

    matches = support.get_jwplayer_mediaurl(data, 'LuluStream', hls=True)
    if not matches:
        data = scrapertools.find_single_match(data,
                                              r"<script type=\"text/javascript\">(eval\(function\(p,a,c,k,e,d\).*?)\s*</script>")
        if data:
            from lib import jsunpack
            data = jsunpack.unpack(data)
            matches = support.get_jwplayer_mediaurl(data, 'LuluStream', hls=True)

    if not matches:  # if not exists, the site just return a page with <video> but not url
        return False, config.get_localized_string(70449) % "LuluStream"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    global matches

    return matches

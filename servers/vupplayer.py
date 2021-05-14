# -*- coding: utf-8 -*-

from core import httptools, scrapertools, support
from platformcode import logger, config


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    page = httptools.downloadpage(page_url)
    global data
    data = page.data
    if page.code == 404 or 'File is no longer available' in data or "We're sorry!" in data:
        return False, config.get_localized_string(70449) % "VUP Player"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    global data

    matches = support.get_jwplayer_mediaurl(data, 'VUP')
    if not matches:
        data = scrapertools.find_single_match(data, r"<script type='text/javascript'>(eval.function.p,a,c,k,e,.*?)\s*</script>")
        if data:
            from lib import jsunpack
            data = jsunpack.unpack(data)
            matches = support.get_jwplayer_mediaurl(data, 'VUP')

    return matches

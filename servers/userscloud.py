# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger, config


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)

    response = httptools.downloadpage(page_url)

    if not response.success or "Not Found" in response.data or "File was deleted" in response.data or "is no longer available" in response.data:
        return False, config.getLocalizedString(70449) % "Userscloud"

    return True, ""


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    videoUrls = []
    unpacked = ""
    data = httptools.downloadpage(page_url).data
    packed = scrapertools.find_single_match(data, "function\(p,a,c,k.*?</script>")
    if packed:
        unpacked = jsunpack.unpack(packed)
    media_url = scrapertools.find_single_match(unpacked, 'url = "([^"]+)')
    if not media_url:
        id_ = page_url.rsplit("/", 1)[1]
        rand = scrapertools.find_single_match(data, 'name="rand" value="([^"]+)"')
        post = "op=download2&id=%s&rand=%s&referer=%s&method_free=&method_premium=" % (id_, rand, page_url)
        data = httptools.downloadpage(page_url, post=post).data
        media_url = scrapertools.find_single_match(data, 'name="down_script".*?<a href="([^"]+)"')

    ext = scrapertools.get_filename_from_url(media_url).split('.')[-1]
    videoUrls.append({'type':ext, 'url':media_url})

    # for videoUrl in videoUrls:
    #     logger.debug("%s - %s" % (videoUrl[0], videoUrl[1]))

    return videoUrls

# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger, config


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    global data
    data = httptools.downloadpage(page_url).data
    if "Not Found" in data or "File was deleted" in data:
        return False, config.getLocalizedString(70449) % "Watchvideo"
    return True, ""


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    videoUrls = []
    media_urls = scrapertools.findMultipleMatches(data, 'file:"([^"]+)"')
    if not media_urls:
        packed = scrapertools.find_single_match(data, "text/javascript'>(.*?)\s*</script>")
        unpacked = jsunpack.unpack(packed)
        media_urls = scrapertools.findMultipleMatches(unpacked, 'file:\s*"([^"]+)"')

    for media_url in media_urls:
        media_url += "|Referer=%s" %page_url
        if ".png" in media_url:
            continue
        ext = "mp4"
        if "m3u8" in media_url:
            ext = "m3u8"
        videoUrls.append({'type':ext, 'url':media_url})
    # videoUrls.reverse()
    # for videoUrl in videoUrls:
    #     logger.debug("%s - %s" % (videoUrl[0], videoUrl[1]))
    return videoUrls

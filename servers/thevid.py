# -*- coding: utf-8 -*-


from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger, config


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "Video not found..." in data or "Video removed due to copyright" in data:
        return False, config.get_localized_string(70292) % "Thevid"
    if "Video removed for inactivity..." in data:
        return False,  config.get_localized_string(70449) % "Thevid"
    return True, ""


def get_video_url(page_url, user="", password="", video_password=""):
    logger.error("(page_url='%s')" % page_url)
    videos = []
    data = httptools.downloadpage(page_url).data
    packed = scrapertools.find_single_match(data, "</script>\s*<script>\s*(eval.*?)\s*</script>")
    unpacked = jsunpack.unpack(packed)
    logger.error(unpacked)
    videos = scrapertools.find_multiple_matches(unpacked, 'vldAb="([^"]+)')
    video_urls = []
    for video in videos:
        if not video.startswith("//"):
            continue
        video = "https:" + video
        video_urls.append(["mp4 [Thevid]", video])
    logger.debug("Url: %s" % videos)
    return video_urls

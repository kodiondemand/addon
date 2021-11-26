# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger

id_server = "vidtodo"
response = ""
def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    global response
    response = httptools.downloadpage(page_url)
    if not response.success or "Not Found" in response.data:
        return False, "[%s] El fichero no existe o ha sido borrado" %id_server
    if not response.success or "Video is processing now." in response.data:
        return False, "[%s] El video se está procesando." %id_server
    return True, ""


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    videoUrls = []
    data = response.data
    packed_data = scrapertools.find_single_match(data, "javascript'>(eval.*?)</script>")
    unpacked = jsunpack.unpack(packed_data)
    matches = scrapertools.findMultipleMatches(unpacked, 'src:"([^"]+)",type:"video/(.*?)",res:(.*?),')
    for media_url, type, res in matches:
        if media_url.endswith(".mp4"):
            videoUrls.append(["[%s][%s]" % (type, res), media_url])
        if media_url.endswith(".m3u8"):
            videoUrls.append(["M3U8 [%s][%s]" % (type, res), media_url])
        if media_url.endswith(".smil"):
            smil_data = httptools.downloadpage(media_url).data
            rtmp = scrapertools.find_single_match(smil_data, 'base="([^"]+)"')
            playpaths = scrapertools.find_single_match(smil_data, 'src="([^"]+)" height="(\d+)"')
            mp4 = "http:" + scrapertools.find_single_match(rtmp, '(//[^:]+):') + "/%s/" + \
                  scrapertools.find_single_match(data, '"Watch video ([^"]+")').replace(' ', '.') + ".mp4"
            for playpath, inf in playpaths:
                h = scrapertools.find_single_match(playpath, 'h=([a-z0-9]+)')
                videoUrls.append({'type':'mp4', 'res':inf, 'url':mp4 % h})
                videoUrls.append({'type':'rtmp', 'res':inf, 'url':"%s playpath=%s" % (rtmp, playpath)})
    # for videoUrl in videoUrls:
    #     logger.debug("videoUrl: %s - %s" % (videoUrl[0], videoUrl[1]))
    return videoUrls

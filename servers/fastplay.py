# -*- coding: utf-8 -*-
from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import config
from platformcode import logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url)

    if "Object not found" in data.data or "longer exists on our servers" in data.data:
        return False,  config.getLocalizedString(70449) % "Fastplay"
    if data.code == 500:
        return False, "[Fastplay] Error interno del servidor"
    return True, ""


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url).data
    if "p,a,c,k,e,d" in data:
        data = jsunpack.unpack(data).replace("\\", "")
    videoUrls = []
    videos = scrapertools.findMultipleMatches(data, 'file\s*:\s*"([^"]+)",label:"(.*?)"')
    # Detección de subtítulos
    subtitulo = scrapertools.find_single_match(data, 'tracks:\s*\[{file:"(.*?)"')
    if "http" not in subtitulo:
        subtitulo = "http://fastplay.cc" + subtitulo
    for videoUrl, video_calidad in videos:
        extension = scrapertools.get_filename_from_url(videoUrl)[-4:]
        if extension not in [".vtt", ".srt"]:
            videoUrls.append({'type':extension, 'res':video_calidad, 'url':videoUrl, 'sub':subtitulo})
    try:
        videoUrls.sort(key=lambda it: int(it[0].split("p ", 1)[0].rsplit(" ")[1]))
    except:
        pass
    for videoUrl in videoUrls:
        logger.debug(" %s - %s" % (videoUrl[0], videoUrl[1]))

    return videoUrls

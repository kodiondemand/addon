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
        return False,  config.get_localized_string(70449) % "Fastplay"
    if data.code == 500:
        return False, "[Fastplay] Error interno del servidor"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url).data
    if "p,a,c,k,e,d" in data:
        data = jsunpack.unpack(data).replace("\\", "")
    video_urls = []
    videos = scrapertools.find_multiple_matches(data, 'file\s*:\s*"([^"]+)",label:"(.*?)"')
    # Detección de subtítulos
    subtitulo = scrapertools.find_single_match(data, 'tracks:\s*\[{file:"(.*?)"')
    if "http" not in subtitulo:
        subtitulo = "http://fastplay.cc" + subtitulo
    for video_url, video_calidad in videos:
        extension = scrapertools.get_filename_from_url(video_url)[-4:]
        if extension not in [".vtt", ".srt"]:
            video_urls.append(["%s %s [fastplay]" % (extension, video_calidad), video_url, 0, subtitulo])
    try:
        video_urls.sort(key=lambda it: int(it[0].split("p ", 1)[0].rsplit(" ")[1]))
    except:
        pass
    for video_url in video_urls:
        logger.debug(" %s - %s" % (video_url[0], video_url[1]))

    return video_urls

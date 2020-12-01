# -*- coding: utf-8 -*-

from core import httptools
from core import jsontools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    page_url = page_url.replace("embed/", "").replace(".html", ".json")
    data = httptools.downloadpage(page_url).data
    if '"error":"video_not_found"' in data or '"error":"Can\'t find VideoInstance"' in data:
        return False, "[Mail.ru] El archivo no existe o ha sido borrado"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % (page_url))

    video_urls = []
    # Carga la página para coger las cookies
    data = httptools.downloadpage(page_url).data

    # Nueva url
    url = page_url.replace("embed/", "").replace(".html", ".json")
    # Carga los datos y los headers
    response = httptools.downloadpage(url)
    data = jsontools.load(response.data)

    # La cookie video_key necesaria para poder visonar el video
    cookie_video_key = scrapertools.find_single_match(response.headers["set-cookie"], '(video_key=[a-f0-9]+)')

    # Formar url del video + cookie video_key
    for videos in data['videos']:
        media_url = videos['url'] + "|Referer=https://my1.imgsmail.ru/r/video2/uvpv3.swf?75&Cookie=" + cookie_video_key
        if not media_url.startswith("http"):
            media_url = "http:" + media_url
        quality = " %s" % videos['key']
        video_urls.append([scrapertools.get_filename_from_url(media_url)[-4:] + quality + " [mail.ru]", media_url])
    try:
        video_urls.sort(key=lambda video_urls: int(video_urls[0].rsplit(" ", 2)[1][:-1]))
    except:
        pass

    for video_url in video_urls:
        logger.debug("%s - %s" % (video_url[0], video_url[1]))

    return video_urls

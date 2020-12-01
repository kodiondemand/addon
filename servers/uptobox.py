# -*- coding: utf-8 -*-
import sys

from platformcode import config

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    #from future import standard_library
    #standard_library.install_aliases()
    import urllib.parse as urllib                               # Es muy lento en PY2.  En PY3 es nativo
else:
    import urllib                                               # Usamos el nativo de PY2 que es más rápido

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url).data

    if "Streaming link:" in data:
        return True, ""
    elif "Unfortunately, the file you want is not available." in data or "Unfortunately, the video you want to see is not available" in data or "This stream doesn" in data\
         or "Page not found" in data:
        return False,  config.get_localized_string(70449) % "Uptobox"
    wait = scrapertools.find_single_match(data, "You have to wait ([0-9]+) (minute|second)")
    if len(wait) > 0:
        tiempo = wait[1].replace("minute", "minuto/s").replace("second", "segundos")
        return False, "[Uptobox] Alcanzado límite de descarga.<br/>Tiempo de espera: " + wait[0] + " " + tiempo

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    # Si el enlace es directo de upstream
    if "uptobox" not in page_url:
        data = httptools.downloadpage(page_url).data
        if "Video not found" in data:
            page_url = page_url.replace("uptostream.com/iframe/", "uptobox.com/")
            data = httptools.downloadpage(page_url).data
            video_urls = uptobox(page_url, data)
        else:
            video_urls = uptostream(data)
    else:
        data = httptools.downloadpage(page_url).data
        # Si el archivo tiene enlace de streaming se redirige a upstream
        if "Streaming link:" in data:
            page_url = "http://uptostream.com/iframe/" + scrapertools.find_single_match(page_url,
                                                                                      'uptobox.com/([a-z0-9]+)')
            data = httptools.downloadpage(page_url).data
            video_urls = uptostream(data)
        else:
            # Si no lo tiene se utiliza la descarga normal
            video_urls = uptobox(page_url, data)

    for video_url in video_urls:
        logger.debug("%s - %s" % (video_url[0], video_url[1]))
    return video_urls


def uptostream(data):
    subtitle = scrapertools.find_single_match(data, "kind='subtitles' src='//([^']+)'")
    if subtitle:
        subtitle = "http://" + subtitle
    video_urls = []
    videos1 = []
    data = data.replace("\\","")
    patron  = 'src":"([^"]+).*?'
    patron += 'type":"([^"]+).*?'
    patron += 'res":"([^"]+).*?'
    patron += 'lang":"([^"]+)'
    media = scrapertools.find_multiple_matches(data, patron)
    for media_url, tipo, res, lang in media:
        videos1.append([media_url, tipo, res, lang])
    videos1.sort(key=lambda videos1: int(videos1[2]))
    for x in videos1:
        media_url = x[0]
        tipo = x[1]
        res = x[2]
        lang = x[3]
        tipo = tipo.replace("video/","")
        extension = ".%s (%s)" % (tipo, res)
        if lang:
            extension = extension.replace(")", "/%s)" % lang[:3])
        video_urls.append([extension + " [uptostream]", media_url, 0, subtitle])
    return video_urls


def uptobox(url, data):
    video_urls = []
    post = ""
    matches = scrapertools.find_multiple_matches(data, '<input type="hidden".*?name="([^"]+)".*?value="([^"]*)">')
    for inputname, inputvalue in matches:
        post += inputname + "=" + inputvalue + "&"

    data = httptools.downloadpage(url, post=post[:-1]).data
    media = scrapertools.find_single_match(data, '<a href="([^"]+)">\s*<span class="button_upload green">')
    # Solo es necesario codificar la ultima parte de la url
    url_strip = urllib.quote(media.rsplit('/', 1)[1])
    media_url = media.rsplit('/', 1)[0] + "/" + url_strip
    video_urls.append([media_url[-4:] + " [uptobox]", media_url])

    return video_urls

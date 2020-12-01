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
    if 'googleusercontent' in page_url:
        return True, "" # desactivada verificación pq se encalla!

    response = httptools.downloadpage(page_url, headers={"Referer": page_url})
    global page
    page = response

    if "no+existe" in response.data or 'no existe.</p>' in response.data:
        return False,  config.get_localized_string(70449) % "gvideo"
    if "Se+ha+excedido+el" in response.data:
        return False, "[gvideo] Se ha excedido el número de reproducciones permitidas"
    if "No+tienes+permiso" in response.data:
        return False, "[gvideo] No tienes permiso para acceder a este video"
    if "Se ha producido un error" in response.data:
        return False, "[gvideo] Se ha producido un error en el reproductor de google"
    if "No+se+puede+procesar+este" in response.data:
        return False, "[gvideo] No se puede procesar este video"
    if response.code == 429:
        return False, "[gvideo] Demasiadas conexiones al servidor, inténtelo después"
    return True, ""


def get_video_url(page_url, user="", password="", video_password=""):
    logger.debug()
    video_urls = []
    urls = []
    streams =[]
    logger.debug('page_url: %s'%page_url)
    
    if 'googleusercontent' in page_url:

        url = page_url
        headers_string = httptools.get_url_headers(page_url, forced=True)

        quality = scrapertools.find_single_match (url, '.itag=(\d+).')
        if not quality:
            quality = '59'
        streams.append((quality, url))

    else:

        data = page.data
        bloque= scrapertools.find_single_match(data, 'url_encoded_fmt_stream_map(.*)')
        
        if bloque:
            data = bloque
        
        data = data.decode('unicode-escape', errors='replace')
        data = urllib.unquote_plus(urllib.unquote_plus(data))

        headers_string = httptools.get_url_headers(page_url, forced=True)
        streams = scrapertools.find_multiple_matches(data,
                                                     'itag=(\d+)&url=(.*?)(?:;.*?quality=.*?(?:,|&)|&quality=.*?(?:,|&))')

    itags = {'18': '360p', '22': '720p', '34': '360p', '35': '480p', '37': '1080p', '43': '360p', '59': '480p'}
    for itag, video_url in streams:
        if not video_url in urls:
            video_url += headers_string
            video_urls.append([itags.get(itag, ''), video_url])
            urls.append(video_url)
        video_urls.sort(key=lambda video_urls: int(video_urls[0].replace("p", "")))

    return video_urls

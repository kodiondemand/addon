# -*- coding: utf-8 -*-

import base64
import hashlib

import urlparse

from core import httptools
from core import scrapertools
from platformcode import logger

host = "https://www.nuvid.com"


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(
        item.clone(action="lista", title="Nuevos Vídeos", url="https://www.nuvid.com/search/videos/_empty_/"))
    itemlist.append(
        item.clone(action="lista", title="Mejor Valorados", url="https://www.nuvid.com/search/videos/_empty_/",
                   extra="rt"))
    itemlist.append(
        item.clone(action="lista", title="Solo HD", url="https://www.nuvid.com/search/videos/hd", calidad="1"))
    itemlist.append(item.clone(action="categorias", title="Categorías", url=host))
    itemlist.append(item.clone(title="Buscar...", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    item.url = "https://www.nuvid.com/search/videos/" + texto.replace(" ", "%20")
    item.extra = "buscar"
    return lista(item)


def lista(item):
    logger.info()
    itemlist = []

    if not item.calidad:
        item.calidad = "0"
    filter = 'ch=178.1.2.3.4.191.7.8.5.9.10.169.11.12.13.14.15.16.17.18.28.190.20.21.22.27.23.24.25.26.189.30.31.32.181' \
             '.35.36.37.180.176.38.33.34.39.40.41.42.177.44.43.45.47.48.46.49.50.51.52.53.54.55.56.57.58.179.59.60.61.' \
             '62.63.64.65.66.69.68.71.67.70.72.73.74.75.182.183.77.76.78.79.80.81.82.84.85.88.86.188.87.91.90.92.93.94' \
             '&hq=%s&rate=&dur=&added=&sort=%s' % (item.calidad, item.extra)
    header = {'X-Requested-With': 'XMLHttpRequest'}
    if item.extra != "buscar":
        header['Cookie'] = 'area=EU; lang=en; search_filter_new=%s' % filter
    # Descarga la pagina 
    data = httptools.downloadpage(item.url, headers=header, cookies=False).data

    # Extrae las entradas
    patron = '<div class="box-tumb related_vid">.*?href="([^"]+)" title="([^"]+)".*?src="([^"]+)"(.*?)<i class="time">([^<]+)<'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle, scrapedthumbnail, quality, duration in matches:
        scrapedurl = urlparse.urljoin(host, scrapedurl)
        if duration:
            scrapedtitle = "%s - %s" % (duration, scrapedtitle)
        if item.calidad == "0" and 'class="hd"' in quality:
            scrapedtitle += "  [COLOR red][HD][/COLOR]"
        itemlist.append(
            item.clone(action="play", title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail, folder=False))

        # Extrae la marca de siguiente página
    next_page = scrapertools.find_single_match(data, '<li class="next1">.*?href="([^"]+)"')
    if next_page:
        next_page = urlparse.urljoin(host, next_page)
        itemlist.append(item.clone(action="lista", title=">> Página Siguiente", url=next_page))

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []

    # Descarga la pagina    
    data = httptools.downloadpage("https://www.nuvid.com/categories").data

    # Extrae las entradas (carpetas)
    bloques = scrapertools.find_multiple_matches(data, '<h2 class="c-mt-output title2">.*?>([^<]+)</h2>(.*?)</div>')
    for cat, b in bloques:
        cat = cat.replace("Straight", "Hetero")
        itemlist.append(item.clone(action="", title=cat, text_color="gold"))
        matches = scrapertools.find_multiple_matches(b, '<li.*?href="([^"]+)">(.*?)</span>')
        for scrapedurl, scrapedtitle in matches:
            scrapedtitle = "   " + scrapedtitle.replace("<span>", "")
            scrapedurl = urlparse.urljoin(host, scrapedurl)
            itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl))

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url, cookies=False).data
    h = scrapertools.find_single_match(data, "params\s*\+=\s*'h=([^']+)'")
    t = scrapertools.find_single_match(data, "params\s*\+=\s*'%26t=([^']+)'")
    vkey = scrapertools.find_single_match(data, "params\s*\+=\s*'%26vkey='.*?'([^']+)'")
    pkey = hashlib.md5(vkey + base64.b64decode("aHlyMTRUaTFBYVB0OHhS")).hexdigest()

    url = 'https://www.nuvid.com/player_config/?h=%s&check_speed=1&t=%s&vkey=%s&pkey=%s&aid=&domain_id=' % (
    h, t, vkey, pkey)
    data = httptools.downloadpage(url, cookies=False).data
    videourl = scrapertools.find_single_match(data, '<video_file>.*?(http.*?)\]')
    if videourl:
        itemlist.append(['.mp4 [directo]', videourl])
    videourl = scrapertools.find_single_match(data, '<hq_video_file>.*?(http.*?)\]')
    if videourl:
        itemlist.append(['.mp4 HD [directo]', videourl])

    return itemlist

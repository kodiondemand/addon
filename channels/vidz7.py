# -*- coding: utf-8 -*-

import re

import urlparse

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import logger

host = 'http://www.vidz7.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, action="lista", title="Útimos videos", url=host))
    itemlist.append(
        Item(channel=item.channel, action="categorias", title="Categorias", url=host + "/category/"))
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar", url="http://www.vidz7.com"))
    return itemlist


def search(item, texto):
    logger.info()

    texto = texto.replace(" ", "+")
    item.url = host + "/?s=%s" % texto
    try:
        return lista(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}", "", data)
    patron = '<li><a href="([^"]+)">(.*?)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for url, actriz in matches:
        itemlist.append(Item(channel=item.channel, action="lista", title=actriz, url=url))

    return itemlist


def lista(item):
    logger.info()
    # Descarga la página
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}", "", data)
    patron = "<a href='.*?.' class='thumb' style='background-image:url\(\"([^\"]+)\"\).*?"
    patron += "<div class=\"hd\">(.*?)</div>.*?"
    patron += "<div class=\"duration\">(.*?)</div>.*?"
    patron += "<h6><a class='hp' href='([^']+)'>(.*?)</a></h6>"
    matches = re.compile(patron, re.DOTALL).findall(data)
    itemlist = []
    for scrapedthumbnail, scrapedhd, duration, scrapedurl, scrapedtitle in matches:
        thumbnail = urlparse.urljoin(item.url, scrapedthumbnail)
        url = urlparse.urljoin(item.url, scrapedurl)
        scrapedtitle = scrapedtitle.strip()
        title = "[COLOR yellow]" + duration + "[/COLOR] " + "[COLOR red]" +scrapedhd+ "[/COLOR]  "+scrapedtitle
        # Añade al listado
        itemlist.append(Item(channel=item.channel, action="play", title=title, thumbnail=thumbnail, fanart=thumbnail,
                             fulltitle=title, url=url,
                             viewmode="movie", folder=True))
    paginacion = scrapertools.find_single_match(data,'<a class="active".*?.>\d+</a><a class="inactive" href ="([^"]+)">')
    if paginacion:
        itemlist.append(Item(channel=item.channel, action="lista", title=">> Página Siguiente", url=paginacion))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    # Descarga la página
    data = httptools.downloadpage(item.url).data
    data = scrapertools.unescape(data)
    itemlist.extend(servertools.find_video_items(data=data))
    for videoitem in itemlist:
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
        videoitem.action = "play"
        videoitem.folder = False
        videoitem.title = item.title
    return itemlist


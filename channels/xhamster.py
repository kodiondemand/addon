# -*- coding: utf-8 -*-

import re

import urlparse

from core import scrapertools, httptools
from core.item import Item
from platformcode import logger

HOST = "http://es.xhamster.com/"


def mainlist(item):
    logger.info()

    itemlist = []
    itemlist.append(Item(channel=item.channel, action="videos", title="Útimos videos", url=HOST, viewmode="movie"))
    itemlist.append(Item(channel=item.channel, action="categorias", title="Categorías", url=HOST))
    itemlist.append(Item(channel=item.channel, action="votados", title="Lo mejor"))
    itemlist.append(Item(channel=item.channel, action="vistos", title="Los mas vistos"))
    itemlist.append(Item(channel=item.channel, action="videos", title="Recomendados",
                         url=urlparse.urljoin(HOST, "/videos/recommended")))
    itemlist.append(
        Item(channel=item.channel, action="search", title="Buscar", url=urlparse.urljoin(HOST, "/search?q=%s")))

    return itemlist


# REALMENTE PASA LA DIRECCION DE BUSQUEDA


def search(item, texto):
    logger.info()
    tecleado = texto.replace(" ", "+")
    item.url = item.url % tecleado
    item.extra = "buscar"
    try:
        return videos(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


# SECCION ENCARGADA DE BUSCAR


def videos(item):
    logger.info()
    data = httptools.downloadpage(item.url).data
    itemlist = []

    data = scrapertools.find_single_match(data, '<article.+?>(.*?)</article>')

    # Patron
    patron = '(?s)<div class="thumb-list__item.*?href="([^"]+)".*?src="([^"]+)".*?alt="([^"]+)">.*?'
    patron += '<div class="thumb-image-container__duration">(.+?)</div>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, duration in matches:
        # logger.debug("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        fullTitle = scrapedtitle.strip() + " [" + duration + "]"
        itemlist.append(
            Item(channel=item.channel, action="play", title=fullTitle, url=scrapedurl, thumbnail=scrapedthumbnail,
                 folder=True))

    # Paginador
    patron = '(?s)<div class="pager-container".*?<li class="next">.*?href="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    if len(matches) > 0:
        itemlist.append(
            Item(channel=item.channel, action="videos", title="Página Siguiente", url=matches[0], thumbnail="",
                 folder=True, viewmode="movie"))

    return itemlist


# SECCION ENCARGADA DE VOLCAR EL LISTADO DE CATEGORIAS CON EL LINK CORRESPONDIENTE A CADA PAGINA


def categorias(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    data = scrapertools.find_single_match(data, '(?s)<div class="all-categories">(.*?)</aside>')

    patron = '(?s)<li>.*?<a href="([^"]+)".*?>([^<]+).*?</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle in matches:
        fullTitle = scrapedtitle.strip()
        itemlist.append(Item(channel=item.channel, action="videos", title=fullTitle, url=scrapedurl))

    return itemlist


def votados(item):
    logger.info()
    itemlist = []

    itemlist.append(Item(channel=item.channel, action="videos", title="Día", url=urlparse.urljoin(HOST, "/best/daily"),
                         viewmode="movie"))
    itemlist.append(
        Item(channel=item.channel, action="videos", title="Semana", url=urlparse.urljoin(HOST, "/best/weekly"),
             viewmode="movie"))
    itemlist.append(
        Item(channel=item.channel, action="videos", title="Mes", url=urlparse.urljoin(HOST, "/best/monthly"),
             viewmode="movie"))
    itemlist.append(
        Item(channel=item.channel, action="videos", title="De siempre", url=urlparse.urljoin(HOST, "/best/"),
             viewmode="movie"))
    return itemlist


def vistos(item):
    logger.info()
    itemlist = []

    itemlist.append(
        Item(channel=item.channel, action="videos", title="Día", url=urlparse.urljoin(HOST, "/most-viewed/daily"),
             viewmode="movie"))
    itemlist.append(
        Item(channel=item.channel, action="videos", title="Semana", url=urlparse.urljoin(HOST, "/most-viewed/weekly"),
             viewmode="movie"))
    itemlist.append(
        Item(channel=item.channel, action="videos", title="Mes", url=urlparse.urljoin(HOST, "/most-viewed/monthly"),
             viewmode="movie"))
    itemlist.append(
        Item(channel=item.channel, action="videos", title="De siempre", url=urlparse.urljoin(HOST, "/most-viewed/"),
             viewmode="movie"))

    return itemlist


# OBTIENE LOS ENLACES SEGUN LOS PATRONES DEL VIDEO Y LOS UNE CON EL SERVIDOR
def play(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    logger.debug(data)

    patron = '"([0-9]+p)":"([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for res, url in matches:
        url = url.replace("\\", "")
        logger.debug("url=" + url)
        itemlist.append(["%s %s [directo]" % (res, scrapertools.get_filename_from_url(url)[-4:]), url])

    return itemlist

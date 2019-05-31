# -*- coding: utf-8 -*-

import re

import urlparse

from core import scrapertools
from core.item import Item
from platformcode import logger


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Novedades", action="novedades", url="http://tubehentai.com/"))
    itemlist.append(
        Item(channel=item.channel, title="Buscar", action="search", url="http://tubehentai.com/search/%s/page1.html"))

    return itemlist


def search(item, texto):
    logger.info()

    texto = texto.replace(" ", "%20")

    item.url = item.url % texto
    try:
        return novedades(item)
    # Se captura la excepciÛn, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def novedades(item):
    logger.info()

    # Descarga la página
    data = httptools.downloadpage(item.url).data
    # <a href="http://tubehentai.com/videos/slave_market_¨c_ep1-595.html"><img class="img" width="145" src="http://tubehentai.com/media/thumbs/5/9/5/./f/595/595.flv-3.jpg" alt="Slave_Market_&Acirc;&uml;C_Ep1" id="4f4fbf26f36
    patron = '<a href="(http://tubehentai.com/videos/[^"]+)"><img.*?src="(http://tubehentai.com/media/thumbs/[^"]+)" alt="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    itemlist = []
    for match in matches:
        # Titulo
        scrapedtitle = match[2]
        scrapedurl = match[0]
        scrapedthumbnail = match[1].replace(" ", "%20")
        scrapedplot = scrapertools.htmlclean(match[2].strip())
        logger.debug("title=[" + scrapedtitle + "], url=[" + scrapedurl + "], thumbnail=[" + scrapedthumbnail + "]")

        # Añade al listado de XBMC
        itemlist.append(
            Item(channel=item.channel, action="play", title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail,
                 plot=scrapedplot, folder=False))

    # ------------------------------------------------------
    # Extrae el paginador
    # ------------------------------------------------------
    # <a href="page2.html" class="next">Next »</a>
    patronvideos = '<a href=\'(page[^\.]+\.html)\'[^>]*?>Next[^<]*?<\/a>'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches) > 0:
        scrapedurl = urlparse.urljoin(item.url, "/" + matches[0])
        logger.info(scrapedurl)
        itemlist.append(Item(channel=item.channel, action="novedades", title=">> Página siguiente", url=scrapedurl))

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    # s1.addParam("flashvars","overlay=http://tubehentai.com/media/thumbs/5/2/3/9/c/5239cf74632cbTHLaBlueGirlep3%20%20Segment2000855.000001355.000.mp4
    # http://tubehentai.com/media/thumbs/5/2/3/9/c/5239cf74632cbTHLaBlueGirlep3%20%20Segment2000855.000001355.000.mp4
    # http://tubehentai.com/media/videos/5/2/3/9/c/5239cf74632cbTHLaBlueGirlep3%20%20Segment2000855.000001355.000.mp4?start=0
    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(data, 's1.addParam\("flashvars","bufferlength=1&autostart=true&overlay=(.*?\.mp4)')
    url = url.replace("/thumbs", "/videos")
    # url = url+"?start=0"
    logger.info("url=" + url)
    server = "Directo"
    itemlist.append(Item(channel=item.channel, title="", url=url, server=server, folder=False))

    return itemlist

# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale hdblog
# ------------------------------------------------------------
import re
import urlparse

from core import httptools, scrapertools
from core.item import Item
from platformcode import logger

host = "https://www.hdblog.it"


def mainlist(item):
    logger.info("kod.hdblog mainlist")
    itemlist = [Item(channel=item.channel,
                     title="[COLOR azure]Video recensioni tecnologiche[/COLOR]",
                     action="peliculas",
                     url=host + "/video/",
                     thumbnail="http://www.crat-arct.org/uploads/images/tic%201.jpg"),
                Item(channel=item.channel,
                     title="[COLOR azure]Categorie[/COLOR]",
                     action="categorias",
                     url=host + "/video/",
                     thumbnail="http://www.crat-arct.org/uploads/images/tic%201.jpg")]

    return itemlist


def categorias(item):
    logger.info("kod.hdblog categorias")
    itemlist = []

    data = httptools.downloadpage(item.url).data
    logger.info(data)

    # Narrow search by selecting only the combo
    start = data.find('<section class="left_toolbar" style="float: left;width: 125px;margin-right: 18px;">')
    end = data.find('</section>', start)
    bloque = data[start:end]

    # The categories are the options for the combo  
    patron = '<a href="([^"]+)"[^>]+><span>(.*?)</span>'
    matches = re.compile(patron, re.DOTALL).findall(bloque)
    scrapertools.printMatches(matches)

    for scrapedurl, scrapedtitle in matches:
        scrapedthumbnail = ""
        scrapedplot = ""
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl + "video/",
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot))

    return itemlist


def peliculas(item):
    logger.info("kod.hdblog peliculas")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data

    # Estrae i contenuti 
    patron = '<a class="thumb_new_image" href="([^"]+)">\s*<img[^s]+src="([^"]+)"[^>]+>\s*</a>\s*[^>]+>\s*(.*?)\s*<'
    matches = re.compile(patron, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        scrapedplot = ""
        itemlist.append(Item(channel=item.channel, action="findvideos", fulltitle=scrapedtitle, show=scrapedtitle,
                             title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot,
                             folder=True))

    # Paginazione 
    patronvideos = '<span class="attiva">[^>]+>[^=]+="next" href="(.*?)" class="inattiva">'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches) > 0:
        scrapedurl = urlparse.urljoin(item.url, matches[0])
        itemlist.append(
            Item(channel=item.channel, action="peliculas", title="[COLOR orange]Avanti >>[/COLOR]", url=scrapedurl,
                 folder=True))

    return itemlist

# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale ricettevideo
# ------------------------------------------------------------
import re
import urlparse

from core import httptools, scrapertools
from core.item import Item
from platformcode import logger

host = "http://ricettevideo.net"


def mainlist(item):
    logger.info("kod.ricettevideo mainlist")
    itemlist = [Item(channel=item.channel, title="[COLOR azure]Videoricette[/COLOR]", action="peliculas",
                     url=host,
                     thumbnail="http://www.brinkmanscountrycorner.com/images/Recipies.png")]

    return itemlist


def peliculas(item):
    logger.info("kod.ricettevideo peliculas")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data

    # Estrae i contenuti 
    patron = '<div class="post-item-small">\s*<a href="([^"]+)"[^t]+title="Permanent Link: ([^"]+)"><img[^s]+src="([^"]+)"[^>]+>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        scrapedplot = ""
        itemlist.append(Item(channel=item.channel, action="findvideos", fulltitle=scrapedtitle, show=scrapedtitle,
                             title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot,
                             folder=True))

    # Paginazione 
    patronvideos = '<link rel=\'next\' href=\'([^\']+)\' />'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches) > 0:
        scrapedurl = urlparse.urljoin(item.url, matches[0])
        itemlist.append(
            Item(channel=item.channel, action="peliculas", title="[COLOR orange]Avanti >>[/COLOR]", url=scrapedurl,
                 folder=True))

    return itemlist

# test update

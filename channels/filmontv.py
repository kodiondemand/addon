# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale film in tv
# Ringraziamo Icarus crew
# ------------------------------------------------------------

import re
import urllib

from channels import support
from core import httptools, scrapertools, tmdb
from core.item import Item
from platformcode import logger

host = "https://www.comingsoon.it"

TIMEOUT_TOTAL = 60


def mainlist(item):
    logger.info(" mainlist")
    itemlist = [Item(channel=item.channel,
                     title=support.typo("IN ONDA ADESSO bold color kod"),
                     action="tvoggi",
                     url="%s/filmtv/" % host,
                     thumbnail=""),
                Item(channel=item.channel,
                     title="Mattina",
                     action="tvoggi",
                     url="%s/filmtv/oggi/mattina/" % host,
                     thumbnail=""),
                Item(channel=item.channel,
                     title="Pomeriggio",
                     action="tvoggi",
                     url="%s/filmtv/oggi/pomeriggio/" % host,
                     thumbnail=""),
                Item(channel=item.channel,
                     title="Sera",
                     action="tvoggi",
                     url="%s/filmtv/oggi/sera/" % host,
                     thumbnail=""),
                Item(channel=item.channel,
                     title="Notte",
                     action="tvoggi",
                     url="%s/filmtv/oggi/notte/" % host,
                     thumbnail="")]

    return itemlist


def tvoggi(item):
    logger.info("filmontv tvoggi")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data

    # Estrae i contenuti 
    patron = r'<div class="col-xs-5 box-immagine">[^<]+<img src="([^"]+)[^<]+<[^<]+<[^<]+<[^<]+<[^<]+<.*?titolo">(.*?)<[^<]+<[^<]+<[^<]+<[^>]+><br />(.*?)<[^<]+</div>[^<]+<[^<]+<[^<]+<[^>]+>[^<]+<[^<]+<[^<]+<[^>]+><[^<]+<[^>]+>:\s*([^<]+)[^<]+<[^<]+[^<]+<[^<]+[^<]+<[^<]+[^<]+[^>]+>:\s*([^<]+)'
    # patron = r'<div class="col-xs-5 box-immagine">[^<]+<img src="([^"]+)[^<]+<[^<]+<[^<]+<[^<]+<[^<]+<.*?titolo">(.*?)<[^<]+<[^<]+<[^<]+<[^>]+><br />(.*?)<[^<]+</div>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedtitle, scrapedtv, scrapedgender, scrapedyear in matches:
    # for scrapedthumbnail, scrapedtitle, scrapedtv in matches:
        scrapedurl = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        infoLabels = {}
        infoLabels["year"] = scrapedyear
        itemlist.append(
            Item(channel=item.channel,
                 action="do_search",
                 extra=urllib.quote_plus(scrapedtitle) + '{}' + 'movie',
                 title=scrapedtitle + "[COLOR yellow]   " + scrapedtv + "[/COLOR]",
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 contentTitle=scrapedtitle,
                 contentType='movie',
                 infoLabels=infoLabels,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def do_search(item):
    from channels import search
    return search.do_search(item)
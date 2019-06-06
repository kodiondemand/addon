# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale film in tv
# Ringraziamo Icarus crew
# ------------------------------------------------------------

import re
import urllib
from channelselector import get_thumb
from core import httptools, scrapertools, tmdb, support
from core.item import Item
from platformcode import logger, config

host = "https://www.comingsoon.it"

TIMEOUT_TOTAL = 60


def mainlist(item):
    logger.info(" mainlist")
    itemlist = [Item(channel="search", action='discover_list', title=config.get_localized_string(70309),
               search_type='list', list_type='movie/now_playing',
                         thumbnail=get_thumb("now_playing.png")),
               Item(channel="search", action='discover_list', title=config.get_localized_string(70312),
                         search_type='list', list_type='tv/on_the_air', thumbnail=get_thumb("on_the_air.png")),
               Item(channel=item.channel,
                     title="[Oggi in TV] [B]Adesso in onda[/B]",
                     action="tvoggi",
                     url="%s/filmtv/" % host,
                     thumbnail=item.thumbnail),
                Item(channel=item.channel,
                     title="[Oggi in TV] Mattina",
                     action="tvoggi",
                     url="%s/filmtv/oggi/mattina/" % host,
                     thumbnail=item.thumbnail),
                Item(channel=item.channel,
                     title="[Oggi in TV] Pomeriggio",
                     action="tvoggi",
                     url="%s/filmtv/oggi/pomeriggio/" % host,
                     thumbnail=item.thumbnail),
                Item(channel=item.channel,
                     title="[Oggi in TV] Sera",
                     action="tvoggi",
                     url="%s/filmtv/oggi/sera/" % host,
                     thumbnail=item.thumbnail),
                Item(channel=item.channel,
                     title="[Oggi in TV] Notte",
                     action="tvoggi",
                     url="%s/filmtv/oggi/notte/" % host,
                     thumbnail=item.thumbnail)]

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
    from specials import search
    return search.do_search(item)
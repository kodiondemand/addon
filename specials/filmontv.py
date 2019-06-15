# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale film in tv
# ------------------------------------------------------------

import re
import urllib
from channelselector import get_thumb
from core import httptools, scrapertools, support, tmdb
from core.item import Item
from platformcode import logger, config

host = "https://www.superguidatv.it"

TIMEOUT_TOTAL = 60


def mainlist(item):
    logger.info(" mainlist")
    itemlist = [#Item(channel="search", action='discover_list', title=config.get_localized_string(70309),
               #search_type='list', list_type='movie/now_playing',
               #          thumbnail=get_thumb("now_playing.png")),
               #Item(channel="search", action='discover_list', title=config.get_localized_string(70312),
               #          search_type='list', list_type='tv/on_the_air', thumbnail=get_thumb("on_the_air.png")),
            Item(channel=item.channel,
                     title="DT Film",
                     action="now_on_tv",
                     url="%s/film-in-tv/" % host,
                     thumbnail=item.thumbnail),
            Item(channel=item.channel,
                     title="P Film",
                     action="now_on_tv",
                     url="%s/film-in-tv/oggi/premium/" % host,
                     thumbnail=item.thumbnail),
            Item(channel=item.channel,
                     title="S Intrattenimento Film",
                     action="now_on_tv",
                     url="%s/film-in-tv/oggi/sky-intrattenimento/" % host,
                     thumbnail=item.thumbnail),
            Item(channel=item.channel,
                     title="S Cinema Film",
                     action="now_on_tv",
                     url="%s/film-in-tv/oggi/sky-cinema/" % host,
                     thumbnail=item.thumbnail),
            Item(channel=item.channel,
                     title="S Documentari Film",
                     action="now_on_tv",
                     url="%s/film-in-tv/oggi/sky-doc-e-lifestyle/" % host,
                     thumbnail=item.thumbnail),
            Item(channel=item.channel,
                     title="Primafila",
                     action="now_on_tv",
                     url="%s/film-in-tv/oggi/sky-primafila/" % host,
                     thumbnail=item.thumbnail),
            Item(channel=item.channel,
                     title="P",
                     action="now_on_misc",
                     url="%s/ora-in-onda/premium/" % host,
                     thumbnail=item.thumbnail),
            Item(channel=item.channel,
                     title="S Intrattenimento",
                     action="now_on_misc",
                     url="%s/ora-in-onda/sky-intrattenimento/" % host,
                     thumbnail=item.thumbnail),
            Item(channel=item.channel,
                     title="S Doc Lifestyle",
                     action="now_on_misc",
                     url="%s/ora-in-onda/sky-doc-e-lifestyle/" % host,
                     thumbnail=item.thumbnail),
            Item(channel=item.channel,
                     title="S Intrattenimento",
                     action="now_on_misc",
                     url="%s/ora-in-onda/sky-intrattenimento/" % host,
                     thumbnail=item.thumbnail)]

    return itemlist

def now_on_misc(item):
    logger.info("filmontv tvoggi")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data
    #patron = r'spanTitleMovie">([A-Za-z À-ÖØ-öø-ÿ\-\']*)[a-z \n<>\/="_\-:0-9;A-Z.]*GenresMovie">([\-\'A-Za-z À-ÖØ-öø-ÿ\/]*)[a-z \n<>\/="_\-:0-9;A-Z.%]*src="([a-zA-Z:\/\.0-9?]*)[a-z \n<>\/="_\-:0-9;A-Z.%\-\']*Year">([A-Z 0-9a-z]*)'
    patron = r'table-cell[;" ]*alt="([^"]+)"[a-z \n<>\/="_\-:0-9;A-Z.?!\'\&, \(\)#]*backdrop" alt="([^"]+)"[ ]*src="([^"]+)'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedchannel, scrapedtitle, scrapedthumbnail in matches:
    # for scrapedthumbnail, scrapedtitle, scrapedtv in matches:
        scrapedurl = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        infoLabels = {}
        infoLabels["year"] = ""
        infoLabels['tvshowtitle'] = scrapedtitle
        itemlist.append(
            Item(channel=item.channel,
                 action="do_search",
                 extra=urllib.quote_plus(scrapedtitle) + '{}' + 'tvshow',
                 title="[B]" + scrapedtitle + "[/B] - " + scrapedchannel,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail.replace("?width=320", "?width=640"),
                 contentTitle=scrapedtitle,
                 contentType='tvshow',
                 infoLabels=infoLabels,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist

def now_on_tv(item):
    logger.info("filmontv tvoggi")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data
    #patron = r'spanTitleMovie">([A-Za-z À-ÖØ-öø-ÿ\-\']*)[a-z \n<>\/="_\-:0-9;A-Z.]*GenresMovie">([\-\'A-Za-z À-ÖØ-öø-ÿ\/]*)[a-z \n<>\/="_\-:0-9;A-Z.%]*src="([a-zA-Z:\/\.0-9?]*)[a-z \n<>\/="_\-:0-9;A-Z.%\-\']*Year">([A-Z 0-9a-z]*)'
    patron = r'view_logo" alt="([a-zA-Z 0-9]*)"[a-z \n<>\/="_\-:0-9;A-Z.?!\'\&]*spanTitleMovie">([A-Za-z ,0-9\.À-ÖØ-öø-ÿ\-\']*)[a-z \n<>\/="_\-:0-9;A-Z.]*GenresMovie">([\-\'A-Za-z À-ÖØ-öø-ÿ\/]*)[a-z \n<>\/="_\-:0-9;A-Z.%]*src="([a-zA-Z:\/\.0-9?]*)[a-z \n<>\/="_\-:0-9;A-Z.%\-\']*Year">([A-Z 0-9a-z]*)'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedchannel, scrapedtitle, scrapedgender, scrapedthumbnail, scrapedyear in matches:
    # for scrapedthumbnail, scrapedtitle, scrapedtv in matches:
        scrapedurl = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        infoLabels = {}
        infoLabels["year"] = scrapedyear
        itemlist.append(
            Item(channel=item.channel,
                 action="do_search",
                 extra=urllib.quote_plus(scrapedtitle) + '{}' + 'movie',
                 title="[B]" + scrapedtitle + "[/B] - " + scrapedchannel,
                 fulltitle="[B]" + scrapedtitle + "[/B] - " + scrapedchannel,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail.replace("?width=240", "?width=480"),
                 contentTitle=scrapedtitle,
                 contentType='movie',
                 infoLabels=infoLabels,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist

def primafila(item):
    logger.info("filmontv tvoggi")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data
    #patron = r'spanTitleMovie">([A-Za-z À-ÖØ-öø-ÿ]*)[a-z \n<>\/="_\-:0-9;A-Z.]*GenresMovie">([A-Za-z À-ÖØ-öø-ÿ\/]*)[a-z \n<>\/="_\-:0-9;A-Z.%]*src="([a-zA-Z:\/\.0-9?=]*)'
    patron = r'spanTitleMovie">([A-Za-z À-ÖØ-öø-ÿ\-\']*)[a-z \n<>\/="_\-:0-9;A-Z.]*GenresMovie">([\-\'A-Za-z À-ÖØ-öø-ÿ\/]*)[a-z \n<>\/="_\-:0-9;A-Z.%]*src="([a-zA-Z:\/\.0-9?]*)[a-z \n<>\/="_\-:0-9;A-Z.%\-\']*Year">([A-Z 0-9a-z]*)'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedtitle, scrapedgender, scrapedthumbnail, scrapedyear in matches:
    # for scrapedthumbnail, scrapedtitle, scrapedtv in matches:
        scrapedurl = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        infoLabels = {}
        infoLabels["year"] = scrapedyear
        itemlist.append(
            Item(channel=item.channel,
                 action="do_search",
                 extra=urllib.quote_plus(scrapedtitle) + '{}' + 'movie',
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail.replace("?width=240", "?width=480"),
                 contentTitle=scrapedtitle,
                 contentType='movie',
                 infoLabels=infoLabels,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist

def do_search(item):
    from specials import search
    return search.do_search(item)

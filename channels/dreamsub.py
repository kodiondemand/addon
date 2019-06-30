# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per dreamsub
# ------------------------------------------------------------
import re
import urlparse

from core import scrapertoolsV2, httptools, servertools, tmdb, support
from specials.autorenumber import renumber
from core.support import menu, log, scrape
from core.item import Item
from platformcode import logger, config

__channel__ = "dreamsub"
host = config.get_channel_url(__channel__)

list_servers = ['verystream', 'streamango', 'openload']
list_quality = ['default']


def mainlist(item):
    log()
    itemlist = []

    menu(itemlist, 'Anime / Cartoni', 'peliculas', host + '/anime', 'tvshow')
    menu(itemlist, 'Categorie', 'categorie', host + '/filter?genere=', 'tvshow')
    menu(itemlist, 'Ultimi Episodi', 'last', host, 'episode')
    menu(itemlist, 'Cerca...', 'search')
    support.aplay(item, itemlist, list_servers, list_quality)
    support.channel_config(item, itemlist)

    return itemlist


def search(item, texto):
    log(texto)
    item.url = host + '/search/' + texto
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    log(categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "anime":
            item.url = host
            item.action = "ultimiep"
            itemlist = ultimiep(item)

            if itemlist[-1].action == "ultimiep":
                itemlist.pop()
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def peliculas(item):
    itemlist = scrape(item, r'Lingua[^<]+<br>\s*<a href="(?:Lista episodi )?([^"]+)" title="(?:Lista episodi )?(.*?)(?: \(([0-9]+)\))?(?: Streaming)?">', ['url', 'title', 'year'], action='episodios', patron_block='<input type="submit" value="Vai!" class="blueButton">(.*?)<div class="footer">', patronNext='<li class="currentPage">[^>]+><li[^<]+<a href="([^"]+)">')
    renumber(itemlist) 
    return itemlist
    

def last(item):
    return scrape(item, r'<li><a href="([^"]+)"[^>]+>([^<]+)(\d+)<br>', ['url', 'title', 'episode'], patron_block='<ul class="last" id="recentAddedEpisodesAnimeDDM">(.*?)</ul>' )


def categorie(item):
    log()
    itemlist = []
    matches = support.match(item, r'<option value="([^"]+)">', r'<select name="genere" id="genere" class="selectInput">(.*?)</select>')[0]

    for value in matches:
        url = item.url + value
        itemlist.append(
            Item(channel=item.channel,
                 contentType=item.contentType,
                 action="peliculas",
                 title=support.typo(value, 'bold'),
                 url=url))
    return support.thumb(itemlist)


def episodios(item):
    itemlist = scrape(item, r'<li><a href="([^"]+)"[^<]+<b>(.*?)<\/b>[^>]+>([^<]+)<\/i>', ['url','title','title2'], patron_block='<div class="seasonEp">(.*?)<div class="footer">')
    renumber(itemlist, item, 'bold')
    return itemlist

def findvideos(item):
    log()
    itemlist = []
    data = httptools.downloadpage(item.url).data

    if 'keepem.online' in data:
        urls = scrapertoolsV2.find_multiple_matches(data, r'(https://keepem\.online/f/[^"]+)"')
        for url in urls:
            url = httptools.downloadpage(url).url
            itemlist += servertools.find_video_items(data=url)

    return support.server(item, data, itemlist)

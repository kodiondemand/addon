# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per altadefinizioneclick
# ----------------------------------------------------------

import re

from channels import autoplay, filtertools, support
from core import servertools
from core.item import Item
from platformcode import logger, config

host = "https://altadefinizione.center"   ### <- cambio Host da .fm a .center

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['verystream', 'openload', 'streamango', "vidoza", "thevideo", "okru", 'youtube']
list_quality = ['1080p']

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'altadefinizioneclick')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'altadefinizioneclick')

headers = [['Referer', host]]

def mainlist(item):
    support.log()    
    itemlist = []

    support.menu(itemlist, 'Film', 'peliculas', host + "/nuove-uscite/")
    support.menu(itemlist, 'Per Genere submenu', 'menu', host, args='Film')
    support.menu(itemlist, 'Per Anno submenu', 'menu', host, args='Anno')
    support.menu(itemlist, 'Sub-IIA', 'peliculas', host + "/sub-ita/")
    support.menu(itemlist, 'Cerca...', 'search', host, 'movie')    

    autoplay.init(item.channel, list_servers, list_quality)
    autoplay.show_option(item.channel, itemlist)

    return itemlist


def search(item, texto):
    support.log("search ", texto)

    item.extra = 'search'
    item.url = host + "/?s=" + texto

    try:
        return peliculas(item)

    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

def newest(categoria):
    support.log(categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "peliculas":
            item.url = host + "/nuove-uscite/"
            item.action = "peliculas"
            itemlist = peliculas(item)

            if itemlist[-1].action == "peliculas":
                itemlist.pop()

    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def menu(item):
    support.log()
    itemlist = support.scrape(item, '<li><a href="(.*?)">(.*?)</a></li>', ['url', 'title'], headers,  patron_block='<ul class="listSubCat" id="'+ str(item.args) + '">(.*?)</ul>', action='peliculas')
    return support.thumb(itemlist)

def peliculas(item):
    support.log()
    if item.extra == 'search':
        itemlist = support.scrape(item, r'<a href="([^"]+)">\s*<div[^=]+=[^=]+=[^=]+=[^=]+=[^=]+="(.*?)"[^>]+>[^<]+<[^>]+>\s*<h[^=]+="titleFilm">(.*?)<', ['url', 'thumb', 'title'], headers, patronNext='<a class="next page-numbers" href="([^"]+)">')
    else:
        itemlist = support.scrape(item, r'<img width[^s]+src="([^"]+)[^>]+>[^>]+>[^>]+>[^>]+><a href="([^"]+)">([^<]+)<\/a>[^>]+>[^>]+>[^>]+>(?:[^>]+>|)[^I]+IMDB\:\s*([^<]+)<', ['thumb', 'url', 'title', 'rating'], headers, patronNext='<a class="next page-numbers" href="([^"]+)">')
    for item in itemlist:
        item.title = re.sub(r'.\(.*?\)', '', item.title)
    return itemlist


def findvideos(item):
    support.log()

    itemlist = support.hdpass_get_servers(item)

    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)

    itemlist = filtertools.get_links(itemlist, item, list_language)

    autoplay.start(itemlist, item)
    support.videolibrary(itemlist, item ,'color kod bold')

    return itemlist

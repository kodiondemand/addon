# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per altadefinizioneclick
# ----------------------------------------------------------

import re

from core import servertools, support
from core.item import Item
from platformcode import logger, config
from specials import autoplay

#host = config.get_setting("channel_host", 'altadefinizioneclick')
__channel__ = 'altadefinizioneclick'
host = config.get_channel_url(__channel__)

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['verystream', 'openload', 'streamango', "vidoza", "thevideo", "okru", 'youtube']
list_quality = ['1080p']

checklinks = config.get_setting('checklinks', 'altadefinizioneclick')
checklinks_number = config.get_setting('checklinks_number', 'altadefinizioneclick')

headers = [['Referer', host]]

def mainlist(item):
    support.log()    
    itemlist = []

    support.menu(itemlist, 'Film', 'peliculas', host + "/nuove-uscite/")
    support.menu(itemlist, 'Per Genere submenu', 'menu', host, args='Film')
    support.menu(itemlist, 'Per Anno submenu', 'menu', host, args='Anno')
    support.menu(itemlist, 'Sub-ITA', 'peliculas', host + "/sub-ita/")
    support.menu(itemlist, 'Cerca...', 'search', host, 'movie')    
    support.aplay(item, itemlist,list_servers, list_quality)
    support.channel_config(item, itemlist)

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
    itemlist = support.scrape(item, '<li><a href="([^"]+)">([^<]+)</a></li>', ['url', 'title'], headers,  patron_block='<ul class="listSubCat" id="'+ str(item.args) + '">(.*?)</ul>', action='peliculas')
    return support.thumb(itemlist)

def peliculas(item):
    support.log()
    if item.extra == 'search':
        patron = r'<a href="([^"]+)">\s*<div class="wrapperImage">(?:<span class="hd">([^<]+)<\/span>)?<img[^s]+src="([^"]+)"[^>]+>[^>]+>[^>]+>([^<]+)<[^<]+>(?:.*?IMDB:\s([^<]+)<\/div>)?'
        elements = ['url', 'quality', 'thumb', 'title', 'rating']
        
    else:
        patron = r'<img width[^s]+src="([^"]+)[^>]+><\/a>.*?<a href="([^"]+)">([^(?:\]|<)]+)(?:\[([^\]]+)\])?<\/a>[^>]+>[^>]+>[^>]+>(?:\sIMDB\:\s([^<]+)<)?(?:.*?<span class="hd">([^<]+)<\/span>)?\s*<a'
        elements =['thumb', 'url', 'title','lang', 'rating', 'quality']
    itemlist = support.scrape(item, patron, elements, headers, patronNext='<a class="next page-numbers" href="([^"]+)">')
    return itemlist


def findvideos(item):
    support.log()

    itemlist = support.hdpass_get_servers(item)

    if checklinks:
        itemlist = servertools.check_list_links(itemlist, checklinks_number)

    # itemlist = filtertools.get_links(itemlist, item, list_language)

    autoplay.start(itemlist, item)
    support.videolibrary(itemlist, item ,'color kod bold')

    return itemlist

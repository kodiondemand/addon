# -*- coding: utf-8 -*-
# -*- Channel Altadefinizione01L Film - Serie -*-
# -*- Creato per Alfa-addon -*-
# -*- e adattato for KOD -*-
# -*- By Greko -*-
# -*- last change: 26/05/2019

import channelselector
from specials import autoplay
from core import servertools, support, jsontools
from core.item import Item
from platformcode import config, logger

__channel__ = "altadefinizione01_link"

# ======== def per utility INIZIO ============================

list_servers = ['supervideo', 'streamcherry','rapidvideo', 'streamango', 'openload']
list_quality = ['default']

#host = config.get_setting("channel_host", __channel__)
host = config.get_channel_url(__channel__)
checklinks = config.get_setting('checklinks', __channel__)
checklinks_number = config.get_setting('checklinks_number', __channel__)

headers = [['Referer', host]]
# =========== home menu ===================

def mainlist(item):
    """
    Creo il menu principale del canale
    :param item:
    :return: itemlist []
    """
    support.log()
    itemlist = []

    # Menu Principale
    support.menu(itemlist, 'Novità bold', 'peliculas', host)
    support.menu(itemlist, 'Film per Genere', 'genres', host, args='genres')
    support.menu(itemlist, 'Film per Anno submenu', 'genres', host, args='years')
    support.menu(itemlist, 'Film per Qualità submenu', 'genres', host, args='quality') 
    support.menu(itemlist, 'Al Cinema bold', 'peliculas', host+'film-del-cinema')    
    support.menu(itemlist, 'Popolari bold', 'peliculas', host+'piu-visti.html')
    support.menu(itemlist, 'Mi sento fortunato bold', 'genres', host, args='lucky')    
    support.menu(itemlist, 'Sub-ITA bold', 'peliculas', host+'film-sub-ita/')   
    support.menu(itemlist, 'Cerca film submenu', 'search', host)

    # per autoplay
    autoplay.init(item.channel, list_servers, list_quality)
    autoplay.show_option(item.channel, itemlist)

    itemlist.append(
        Item(channel='setting',
             action="channel_config",
             title=support.typo("Configurazione Canale color lime"),
             config=item.channel,
             folder=False,
             thumbnail=channelselector.get_thumb('setting_0.png'))
    )
    
    return itemlist

# ======== def in ordine di action dal menu ===========================

def peliculas(item):
    support.log
    itemlist = []

    patron = r'class="innerImage">.*?href="([^"]+)".*?src="([^"]+)"'\
             '.*?class="ml-item-title">([^<]+)</.*?class="ml-item-label"> (\d{4}) <'\
             '.*?class="ml-item-label">.*?class="ml-item-label ml-item-label-.+?"> '\
             '(.+?) </div>.*?class="ml-item-label"> (.+?) </'
    listGroups = ['url', 'thumb', 'title', 'year', 'quality', 'lang']

    patronNext =  '<span>\d</span> <a href="([^"]+)">'
    
    itemlist = support.scrape(item, patron=patron, listGroups=listGroups,
                          headers= headers, patronNext=patronNext,
                          action='findvideos')    
    
    return itemlist

# =========== def pagina categorie ======================================

def genres(item):
    support.log
    itemlist = []
    #data = httptools.downloadpage(item.url, headers=headers).data
    action = 'peliculas'
    if item.args == 'genres':
        bloque = r'<ul class="listSubCat" id="Film">(.*?)</ul>'
    elif item.args == 'years':
        bloque = r'<ul class="listSubCat" id="Anno">(.*?)</ul>'
    elif item.args == 'quality':
        bloque = r'<ul class="listSubCat" id="Qualita">(.*?)</ul>'
    elif item.args == 'lucky': # sono i titoli random nella pagina, cambiano 1 volta al dì
        bloque = r'FILM RANDOM.*?class="listSubCat">(.*?)</ul>'
        action = 'findvideos'
     
    patron = r'<li><a href="([^"]+)">(.*?)<'

    listGroups = ['url','title']
    itemlist = support.scrape(item, patron=patron, listGroups=listGroups,
                          headers= headers, patron_block = bloque,
                          action=action)    

    return itemlist

# =========== def per cercare film/serietv =============
#host+/index.php?do=search&story=avatar&subaction=search
def search(item, text):
    support.log()
    itemlist = []
    text = text.replace(" ", "+")
    item.url = host+"/index.php?do=search&story=%s&subaction=search" % (text)
    try:
        return peliculas(item)
    # Se captura la excepciÛn, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.info("%s mainlist search log: %s" % (__channel__, line))
        return []

# =========== def per le novità nel menu principale =============

def newest(categoria):
    support.log(categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "peliculas":
            item.url = host
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

def findvideos(item):
    support.log()
    
    itemlist = support.server(item, headers=headers)

    # Requerido para FilterTools
    # itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay
    autoplay.start(itemlist, item)

    support.videolibrary(itemlist, item, 'color kod')
    
    return itemlist

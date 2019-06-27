# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Eurostreaming
# by Greko
# ------------------------------------------------------------
"""
    Riscritto per poter usufruire del decoratore support.scrape
    Problemi noti:
    Alcune sezioni di anime-cartoni non vanno, alcune hanno solo la lista degli episodi, ma non hanno link
    altre cambiano la struttura
    La sezione novità non fa apparire il titolo degli episodi
"""

import channelselector
from specials import autoplay, filtertools
from core import scrapertoolsV2, httptools, servertools, tmdb, support
from core.item import Item
from platformcode import logger, config

__channel__ = "eurostreaming"
host = config.get_channel_url(__channel__)
headers = ['Referer', host]

list_servers = ['verystream', 'wstream', 'speedvideo', 'flashx', 'nowvideo', 'streamango', 'deltabit', 'openload']
list_quality = ['default']

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'eurostreaming')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'eurostreaming')

IDIOMAS = {'Italiano': 'ITA', 'Sub-ITA':'vosi'}
list_language = IDIOMAS.values()

def mainlist(item):
    #import web_pdb; web_pdb.set_trace()
    support.log()    
    itemlist = []
    
    support.menu(itemlist, 'Serie TV', 'serietv', host, contentType = 'tvshow') # mettere sempre episode per serietv, anime!!
    support.menu(itemlist, 'Serie TV Archivio submenu', 'serietv', host + "/category/serie-tv-archive/", contentType = 'tvshow')
    support.menu(itemlist, 'Ultimi Aggiornamenti submenu', 'serietv', host + '/aggiornamento-episodi/', args='True', contentType = 'tvshow')
    support.menu(itemlist, 'Anime / Cartoni', 'serietv', host + '/category/anime-cartoni-animati/', contentType = 'tvshow')
    support.menu(itemlist, 'Cerca...', 'search', host, contentType = 'tvshow')

##    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality)
    # richiesto per autoplay
    autoplay.init(item.channel, list_servers, list_quality)
    autoplay.show_option(item.channel, itemlist)

    support.channel_config(item, itemlist)
    
    return itemlist

@support.scrape
def serietv(item):
    #import web_pdb; web_pdb.set_trace()
    # lista serie tv
    support.log()
    itemlist = []
    if item.args:
        # il titolo degli episodi viene inglobato in episode ma non sono visibili in newest!!!
        patron = r'<span class="serieTitle" style="font-size:20px">(.*?).[^–]<a href="([^"]+)"\s+target="_blank">(.*?)<\/a>'
        listGroups = ['title', 'url', 'title2']
        patronNext = ''
    else:
        patron = r'<div class="post-thumb">.*?\s<img src="([^"]+)".*?><a href="([^"]+)".*?>(.*?(?:\((\d{4})\)|(\d{4}))?)<\/a><\/h2>'
        listGroups = ['thumb', 'url', 'title', 'year', 'year']
        patronNext='a class="next page-numbers" href="?([^>"]+)">Avanti &raquo;</a>'
    action='episodios'
    return locals()
##    itemlist = support.scrape(item, patron_block='', patron=patron, listGroups=listGroups,
##                          patronNext=patronNext, action='episodios')
##    return itemlist

@support.scrape
def episodios(item):
##    import web_pdb; web_pdb.set_trace()
    support.log("episodios: %s" % item)
    itemlist = []
    item.contentType = 'episode'
    # Carica la pagina
    data = httptools.downloadpage(item.url).data
    #======== 
    if 'clicca qui per aprire' in data.lower():
        item.url = scrapertoolsV2.find_single_match(data, '"go_to":"([^"]+)"')
        item.url = item.url.replace("\\","")
        # Carica la pagina
        data = httptools.downloadpage(item.url).data
    elif 'clicca qui</span>' in data.lower():
        item.url = scrapertoolsV2.find_single_match(data, '<h2 style="text-align: center;"><a href="([^"]+)">')
        # Carica la pagina        
        data = httptools.downloadpage(item.url).data
    #=========
    patron = r'(?:<\/span>\w+ STAGIONE\s\d+ (?:\()?(ITA|SUB ITA)(?:\))?<\/div>'\
             '<div class="su-spoiler-content su-clearfix" style="display:none">|'\
             '(?:\s|\Wn)?(?:<strong>)?(\d+&#.*?)(?:|–)?<a\s(.*?)<\/a><br\s\/>)'

    listGroups = ['lang', 'title', 'url']
    action = 'findvideos'

    return locals()

# ===========  def findvideos  =============

def findvideos(item):
    support.log('findvideos', item)
    itemlist =[]

    # Requerido para FilterTools
##    itemlist = filtertools.get_links(itemlist, item, list_language)

    itemlist = support.server(item, item.url)
##    support.videolibrary(itemlist, item)
    
    return itemlist

# ===========  def ricerca  =============
def search(item, texto):
    support.log()
    item.url = "%s/?s=%s" % (host, texto)
    try:
        return serietv(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

# ===========  def novità in ricerca globale  =============
def newest(categoria):
    support.log()  
    itemlist = []
    item = Item()
    item.contentType= 'episode'
    item.args= 'True'
    try:        
        item.url = "%s/aggiornamento-episodi/" % host
        item.action = "serietv"
        itemlist = serietv(item)

        if itemlist[-1].action == "serietv":
            itemlist.pop()

    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist

def paginator(item):
    pass

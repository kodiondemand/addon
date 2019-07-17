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
"""

#import channelselector
#from specials import autoplay#, filtertools
from core import scrapertoolsV2, httptools, support#, servertools, tmdb
from core.item import Item
from platformcode import logger, config

__channel__ = "eurostreaming"
host = config.get_channel_url(__channel__)
headers = ['Referer', host]

list_servers = ['verystream', 'wstream', 'speedvideo', 'flashx', 'nowvideo', 'streamango', 'deltabit', 'openload']
list_quality = ['default']

checklinks = config.get_setting('checklinks', 'cineblog01')
checklinks_number = config.get_setting('checklinks_number', 'cineblog01')

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
    # autoplay
    support.aplay(item, itemlist, list_servers, list_quality)
    # configurazione canale
    support.channel_config(item, itemlist)
        
    return itemlist

@support.scrape
def serietv(item):
##    import web_pdb; web_pdb.set_trace()
    support.log()
    itemlist = []
    if item.args:
        #patron = r'<span class="serieTitle" style="font-size:20px">(.*?).[^–]<a href="([^"]+)"\s+target="_blank">(.*?)<\/a>'
##        # DA SISTEMARE - problema: mette tutti gli episodi in sub-ita
##        patron = r'<span class="serieTitle" style="font-size:20px">(.*?).[^–]<a href="([^"]+)"'\
##                 '\s+target="_blank">(\d+x\d+) (.*?)(?:|\((.+?)\))</a>'
        patron = r'<span class="serieTitle" style="font-size:20px">(.*?).[^–]<a href="([^"]+)"'\
                 '\s+target="_blank">(\d+x\d+) (.*?)</a>'
        listGroups = ['title', 'url', 'episode', 'title2']
        patronNext = ''

        # permette di vedere episodio e titolo + titolo2 in novità
        def itemHook(item):
            item.show = item.episode + item.title
            return item
    else:
        patron = r'<div class="post-thumb">.*?\s<img src="([^"]+)".*?><a href="([^"]+)".*?>(.*?(?:\((\d{4})\)|(\d{4}))?)<\/a><\/h2>'
        listGroups = ['thumb', 'url', 'title', 'year', 'year']
        patronNext='a class="next page-numbers" href="?([^>"]+)">Avanti &raquo;</a>'
    action='episodios'
    
    return locals()

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
    return support.server(item, item.url)

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

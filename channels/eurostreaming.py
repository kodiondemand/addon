# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Eurostreaming
# adattamento di Cineblog01
# by Greko
# ------------------------------------------------------------
"""
    Riscritto per poter usufruire del modulo support.
    Problemi noti:
    Alcun regex possono migliorare
    server versystream : 'http://vcrypt.net/very/' # VeryS non decodifica il link :http://vcrypt.net/fastshield/
    server nowvideo.club da implementare nella cartella servers, altri server nei meandri del sito?!
    Alcune sezioni di anime-cartoni non vanno, alcune hanno solo la lista degli episodi, ma non hanno link
    altre cambiano la struttura
    La sezione novità non fa apparire il titolo degli episodi
"""

import re

from core import scrapertoolsV2, httptools, tmdb, support
from core.item import Item
from platformcode import logger, config
from specials import autoplay

host = "https://eurostreaming.cafe/"
headers = ['Referer', host]

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['verystream', 'wstream', 'speedvideo', 'flashx', 'nowvideo', 'streamango', 'deltabit', 'openload']
list_quality = ['default']

checklinks = config.get_setting('checklinks', 'eurostreaming')
checklinks_number = config.get_setting('checklinks_number', 'eurostreaming')

def mainlist(item):
    support.log()    
    itemlist = []
    
    support.menu(itemlist, 'Serie TV', 'serietv', host, 'episode') # mettere sempre episode per serietv, anime!!
    support.menu(itemlist, 'Serie TV Archivio submenu', 'serietv', host + "category/serie-tv-archive/", 'episode')
    support.menu(itemlist, 'Ultimi Aggiornamenti submenu', 'serietv', host + 'aggiornamento-episodi/', 'episode', args='True')
    support.menu(itemlist, 'Anime / Cartoni', 'serietv', host + 'category/anime-cartoni-animati/', 'episode')
    support.menu(itemlist, 'Cerca...', 'search', host, 'episode')

    # richiesto per autoplay
    autoplay.init(item.channel, list_servers, list_quality)
    autoplay.show_option(item.channel, itemlist)

    return itemlist


def serietv(item):    
    support.log()
    itemlist = []
    if item.args:
        # il titolo degli episodi viene inglobato in episode ma non sono visibili in newest!!!
        patron = r'<span class="serieTitle" style="font-size:20px">(.*?).[^–]<a href="([^"]+)"\s+target="_blank">(.*?)<\/a>'
        listGroups = ['title', 'url', 'episode']
        patronNext = ''
    else:
        patron = r'<div class="post-thumb">.*?\s<img src="([^"]+)".*?><a href="([^"]+)".*?>(.*?(?:\((\d{4})\)|(\d{4}))?)<\/a><\/h2>'
        listGroups = ['thumb', 'url', 'title', 'year', 'year']
        patronNext='a class="next page-numbers" href="?([^>"]+)">Avanti &raquo;</a>'

    itemlist = support.scrape(item, patron_block='', patron=patron, listGroups=listGroups,
                          patronNext=patronNext,
                          action='episodios')
    return itemlist

def episodios(item):
    support.log()
    itemlist = []
    
    # Carica la pagina
    data = httptools.downloadpage(item.url).data
    #======== 
    if 'clicca qui per aprire' in data.lower():
        item.url = scrapertoolsV2.find_single_match(data, '"go_to":"(.*?)"')
        item.url = item.url.replace("\\","")
        # Carica la pagina
        data = httptools.downloadpage(item.url).data
    elif 'clicca qui</span>' in data.lower():
        item.url = scrapertoolsV2.find_single_match(data, '<h2 style="text-align: center;"><a href="(.*?)">')
        # Carica la pagina        
        data = httptools.downloadpage(item.url).data
    #=========

    matches = scrapertoolsV2.find_multiple_matches(data,
                                                   r'<span class="su-spoiler-icon"><\/span>(.*?)</div></div>')    
    for match in matches:
        blocks = scrapertoolsV2.find_multiple_matches(match, r'(?:(\d&#215;[a-zA-Z0-9].*?))<br \/>')
        season_lang = scrapertoolsV2.find_single_match(match, r'<\/span>.*?STAGIONE\s+\d+\s\(([^<>]+)\)').strip()

        logger.info("blocks log: %s" % ( blocks ))
        for block in blocks:
            season_n, episode_n = scrapertoolsV2.find_single_match(block, r'(\d+)(?:&#215;|×)(\d+)') 
            titolo = scrapertoolsV2.find_single_match(block, r'[&#;]\d+[ ]([a-zA-Z0-9;&#.\s]+)[ ]?[^<>]')
            logger.info("block log: %s" % ( block ))
                
            titolo = re.sub(r'&#215;|×', "x", titolo).replace("&#8217;","'")
            item.infoLabels['season'] = season_n # permette di vedere il plot della stagione e...
            item.infoLabels['episode'] = episode_n # permette di vedere il plot della puntata e...
           
            itemlist.append(
                Item(channel=item.channel,
                     action="findvideos",
                     contentType=item.contentType,
                     title="[B]" + season_n + "x" + episode_n + " " + titolo + "[/B] " + season_lang,
                     fulltitle=item.title, # Titolo nel video
                     show=titolo + ":" + season_n + "x" + episode_n, # sottotitoletto nel video
                     url=block,
                     extra=item.extra,
                     thumbnail=item.thumbnail,
                     infoLabels=item.infoLabels
                     ))
                
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    
    support.videolibrary(itemlist, item)

    return itemlist


# ===========  def ricerca  =============
def search(item, texto):
    support.log()
    item.url = "%s?s=%s" % (host, texto)

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
    try:
        item.args= 'True'
        item.url = "%saggiornamento-episodi/" % host
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

def findvideos(item):
    support.log()
    itemlist =[]
    
    itemlist = support.server(item, item.url)
    
    return itemlist

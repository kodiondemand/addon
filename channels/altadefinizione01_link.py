# -*- coding: utf-8 -*-
# -*- Channel Altadefinizione01L Film - Serie -*-
# -*- By Greko -*-

##import channelselector
from specials import autoplay
from core import servertools, support, jsontools
from core.item import Item
from platformcode import config, logger

__channel__ = "altadefinizione01_link"

# ======== def per utility INIZIO ============================
host = config.get_setting("channel_host", __channel__)

list_servers = ['supervideo', 'streamcherry','rapidvideo', 'streamango', 'openload']
list_quality = ['default']

headers = [['Referer', host]]
# =========== home menu ===================
@support.menu
def mainlist(item):

    film = ''
    filmSub = [
        ('Al Cinema', ['/film-del-cinema', 'peliculas']),
        ('Generi', ['', 'genres', 'genres']),
        ('Anni', ['', 'genres', 'years']),
        ('Mi sento fortunato', ['/piu-visti.html', 'genres', 'lucky']),
        ('Popolari', ['/piu-visti.html', 'peliculas', '']),
        ('Qualità', ['/piu-visti.html', 'genres', 'quality']),
        ('Sub-ITA', ['/sub-ita/', 'peliculas'])
    ]

    return locals()

# ======== def in ordine di action dal menu ===========================

@support.scrape
def peliculas(item):
    #import web_pdb; web_pdb.set_trace()
    support.log('peliculas',item)
    itemlist = []

    patron = r'class="innerImage">.*?href="(?P<url>[^"]+)".*?src="(?P<thumb>[^"]+)"'\
             '.*?class="ml-item-title">(?P<title>[^<]+)</.*?class="ml-item-label"> '\
             '(?P<year>\d{4}) <.*?class="ml-item-label"> (?P<duration>\d+) .*?'\
             'class="ml-item-label ml-item-label-.+?"> (?P<quality>.+?) <.*?'\
             'class="ml-item-label"> (?P<lang>.+?) </'

    patronNext =  '<span>\d</span> <a href="([^"]+)">'

    return locals()   

# =========== def pagina categorie ======================================
@support.scrape
def genres(item):
    support.log

    action = 'peliculas'
    if item.args == 'genres':
        patronBlock = r'<ul class="listSubCat" id="Film">(.*?)</ul>'
    elif item.args == 'years':
        patronBlock = r'<ul class="listSubCat" id="Anno">(.*?)</ul>'
    elif item.args == 'quality':
        patronBlock = r'<ul class="listSubCat" id="Qualita">(.*?)</ul>'
    elif item.args == 'lucky': # sono i titoli random nella pagina, cambiano 1 volta al dì
        patronBlock = r'FILM RANDOM.*?class="listSubCat">(.*?)</ul>'
        action = 'findvideos'

    patron = r'<li><a href="(?P<url>[^"]+)">(?P<title>[^<]+)<'

    return locals()    

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
    return support.server(item, headers=headers)

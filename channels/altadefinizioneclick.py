# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per altadefinizioneclick
# ----------------------------------------------------------

from specials import autoplay
from core import servertools, support
from core.item import Item
from platformcode import config, logger

__channel__ = 'altadefinizioneclick'

host = config.get_channel_url(__channel__)
headers = [['Referer', host]]
list_servers = ['verystream', 'openload', 'streamango', "vidoza", "thevideo", "okru", 'youtube']
list_quality = ['1080p']

@support.menu
def mainlist(item):
    support.log()

    film = '' #'/nuove-uscite/'
    filmSub = [
        ('Novità', ['/nuove-uscite/', 'peliculas']),
        ('Al Cinema', ['/film-del-cinema', 'peliculas']),
        ('Generi', ['', 'menu', 'Film']),
        ('Anni', ['', 'menu', 'Anno']),
        ('Qualità', ['', 'menu', 'Qualita']),
        ('Sub-ITA', ['/sub-ita/', 'peliculas'])
    ]

    return locals()

@support.scrape
def menu(item):
    support.log()

    action='peliculas'
    patron = r'<li><a href="(?P<url>[^"]+)">(?P<title>[^<]+)</a></li>'
    patronBlock= r'<ul class="listSubCat" id="'+ str(item.args) + '">(.*?)</ul>'

    return locals()

@support.scrape
def peliculas(item):
    support.log()
    if item.extra == 'search':
        patron = r'<a href="(?P<url>[^"]+)">\s*<div class="wrapperImage">(?:<span class="hd">(?P<quality>[^<]+)'\
                 '<\/span>)?<img[^s]+src="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+>(?P<title>[^<]+)<[^<]+>'\
                 '(?:.*?IMDB:\s(\2[^<]+)<\/div>)?'
    else:
        patron = r'<img width[^s]+src="(?P<thumb>[^"]+)[^>]+><\/a>.*?<a href="(?P<url>[^"]+)">(?P<title>[^(?:\]|<)]+)'\
                 '(?:\[(?P<lang>[^\]]+)\])?<\/a>[^>]+>[^>]+>[^>]+>(?:\sIMDB\:\s(?P<rating>[^<]+)<)?'\
                 '(?:.*?<span class="hd">(?P<quality>[^<]+)<\/span>)?\s*<a'

        # in caso di CERCA si apre la maschera di inserimento dati
        patronNext = r'<a class="next page-numbers" href="([^"]+)">'

    return locals()

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

def findvideos(item):
    support.log('findvideos', item)
    return support.hdpass_get_servers(item)

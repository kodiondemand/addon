# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Guardaserie.click
# Thanks to Icarus crew & Alfa addon & 4l3x87
# ------------------------------------------------------------

"""
    Problemi noti:
    - nella pagina categorie appaiono i risultati di tmdb in alcune voci
"""

from core import scrapertoolsV2, httptools, support
from core.item import Item
from platformcode import logger, config
from core.support import log

__channel__ = 'guardaserieclick'

host = config.get_channel_url(__channel__)
headers = [['Referer', host]]

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['speedvideo', 'openload']
list_quality = ['default']

headers = [['Referer', host]]


# ----------------------------------------------------------------------------------------------------------------
def mainlist(item):
    log()

    itemlist = []

    support.menu(itemlist, 'Serie', 'serietv', "%s/lista-serie-tv" % host, 'tvshow', args=['news'])
    support.menu(itemlist, 'Ultimi Aggiornamenti submenu', 'serietv', "%s/lista-serie-tv" % host, 'tvshow', args= ['update'])
    support.menu(itemlist, 'Categorie', 'categorie', host, 'tvshow', args=['cat'])
    support.menu(itemlist, 'Serie inedite Sub-ITA submenu', 'serietv', "%s/lista-serie-tv" % host, 'tvshow', args=['inedite'])
    support.menu(itemlist, 'Da non perdere bold submenu', 'serietv', "%s/lista-serie-tv" % host, 'tvshow', args=['tv', 'da non perdere'])
    support.menu(itemlist, 'Classiche bold submenu', 'serietv', "%s/lista-serie-tv" % host, 'tvshow', args=['tv', 'classiche'])
    support.menu(itemlist, 'Disegni che si muovono sullo schermo per magia bold', 'tvserie', "%s/category/animazione/" % host, 'tvshow', args= ['anime'])
    support.menu(itemlist, 'Cerca', 'search', host, 'tvshow', args=['cerca'])

    # autoplay
    support.aplay(item, itemlist, list_servers, list_quality)
    # configurazione del canale
    support.channel_config(item, itemlist)

    return itemlist

@support.scrape
def serietv(item):
##    import web_pdb; web_pdb.set_trace()
    log('serietv ->\n')
##<<<<<<< HEAD
##
##    action = 'episodios'
##    listGroups = ['url', 'thumb', 'title']
##    patron = r'<a href="([^"]+)".*?> <img\s.*?src="([^"]+)" \/>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)<\/p>'
##    if 'news' in item.args:
##        patronBlock = r'<div class="container container-title-serie-new container-scheda" meta-slug="new">(.*?)</div></div><div'
##    elif 'inedite' in item.args:
##        patronBlock = r'<div class="container container-title-serie-ined container-scheda" meta-slug="ined">(.*?)</div></div><div'
##    elif 'da non perdere' in item.args:
##        patronBlock = r'<div class="container container-title-serie-danonperd container-scheda" meta-slug="danonperd">(.*?)</div></div><div'
##    elif 'classiche' in item.args:
##        patronBlock = r'<div class="container container-title-serie-classiche container-scheda" meta-slug="classiche">(.*?)</div></div><div'
##    elif 'update' in item.args:
##        listGroups = ['url', 'thumb', 'episode', 'lang', 'title']
##        patron = r'rel="nofollow" href="([^"]+)"[^>]+> <img.*?src="([^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(\d+.\d+) \((.+?)\).<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)<[^>]+>'
##        patronBlock = r'meta-slug="lastep">(.*?)</div></div><div'
##        # permette di vedere episodio + titolo + titolo2 in novità
##        def itemHook(item):
##            item.show = item.episode + item.title
##            return item
##    return locals()
##
##@support.scrape
##def tvserie(item):
##
##    action = 'episodios'
##    listGroups = ['url', 'thumb', 'title']
##    patron = r'<a\shref="([^"]+)".*?>\s<img\s.*?src="([^"]+)" />[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)</p></div>'
##    patronBlock = r'<div\sclass="col-xs-\d+ col-sm-\d+-\d+">(.*?)<div\sclass="container-fluid whitebg" style="">'
##    patronNext = r'<link\s.*?rel="next"\shref="([^"]+)"'
##
##    return locals()
##
##@support.scrape
##def episodios(item):
##    log('episodios ->\n')
##    item.contentType = 'episode'
##
##    action = 'findvideos'
##    listGroups = ['episode', 'lang', 'title2', 'plot', 'title', 'url']
##    patron = r'class="number-episodes-on-img"> (\d+.\d+)(?:|[ ]\((.*?)\))<[^>]+>'\
##             '[^>]+>[^>]+>[^>]+>[^>]+>(.*?)<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>'\
##             '(.*?)<[^>]+></div></div>.<span\s.+?meta-serie="(.*?)" meta-stag=(.*?)</span>'
##
##    return locals()
##
##=======

    action = 'episodios'
    listGroups = ['url', 'thumb', 'title']
    patron = r'<a href="([^"]+)".*?> <img\s.*?src="([^"]+)" \/>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)<\/p>'
    if 'news' in item.args:
        patron_block = r'<div class="container container-title-serie-new container-scheda" meta-slug="new">(.*?)</div></div><div'
    elif 'inedite' in item.args:
        patron_block = r'<div class="container container-title-serie-ined container-scheda" meta-slug="ined">(.*?)</div></div><div'
    elif 'da non perdere' in item.args:
        patron_block = r'<div class="container container-title-serie-danonperd container-scheda" meta-slug="danonperd">(.*?)</div></div><div'
    elif 'classiche' in item.args:
        patron_block = r'<div class="container container-title-serie-classiche container-scheda" meta-slug="classiche">(.*?)</div></div><div'
    elif 'update' in item.args:
        listGroups = ['url', 'thumb', 'episode', 'lang', 'title']
        patron = r'rel="nofollow" href="([^"]+)"[^>]+> <img.*?src="([^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(\d+.\d+) \((.+?)\).<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)<[^>]+>'
        patron_block = r'meta-slug="lastep">(.*?)</div></div><div'
        # permette di vedere episodio + titolo + titolo2 in novità
        def itemHook(item):
            item.show = item.episode + item.title
            return item
    return locals()

@support.scrape
def tvserie(item):

    action = 'episodios'
    listGroups = ['url', 'thumb', 'title']
    patron = r'<a\shref="([^"]+)".*?>\s<img\s.*?src="([^"]+)" />[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)</p></div>'
    patron_block = r'<div\sclass="col-xs-\d+ col-sm-\d+-\d+">(.*?)<div\sclass="container-fluid whitebg" style="">'
    patronNext = r'<link\s.*?rel="next"\shref="([^"]+)"'

    return locals()

@support.scrape
def episodios(item):
    log('episodios ->\n')
    item.contentType = 'episode'

    action = 'findvideos'
    listGroups = ['episode', 'lang', 'title2', 'plot', 'title', 'url']
    patron = r'class="number-episodes-on-img"> (\d+.\d+)(?:|[ ]\((.*?)\))<[^>]+>'\
             '[^>]+>[^>]+>[^>]+>[^>]+>(.*?)<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>'\
             '(.*?)<[^>]+></div></div>.<span\s.+?meta-serie="(.*?)" meta-stag=(.*?)</span>'

    return locals()

##>>>>>>> a72130e0324ae485ae5f39d3d8f1df46c365fa5b
def findvideos(item):
    log()
    return support.server(item, item.url)

@support.scrape
def categorie(item):
    log

    action = 'tvserie'
    listGroups = ['url', 'title']
    patron = r'<li>\s<a\shref="([^"]+)"[^>]+>([^<]+)</a></li>'

    patron_block = r'<ul\sclass="dropdown-menu category">(.*?)</ul>'


    return locals()

# ================================================================================================================
##
### ----------------------------------------------------------------------------------------------------------------
def newest(categoria):
    log()
    itemlist = []
    item = Item()
    item.contentType= 'episode'
    item.args = 'update'
    try:
        if categoria == "series":
            item.url = "%s/lista-serie-tv" % host
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

### ================================================================================================================
### ----------------------------------------------------------------------------------------------------------------

def search(item, texto):
    log(texto)
    item.url = host + "/?s=" + texto
    item.args = 'cerca'
    try:
        return tvserie(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

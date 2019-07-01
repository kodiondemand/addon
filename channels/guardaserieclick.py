# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Guardaserie.click
# Thanks to Icarus crew & Alfa addon & 4l3x87
# ------------------------------------------------------------

#import re

##from core import httptools, scrapertools, support
###from core import tmdb
##from core.item import Item
##from core.support import log
##from platformcode import logger, config
from core import scrapertoolsV2, httptools, support
from core.item import Item
from platformcode import logger, config
from core.support import log
#from specials import autorenumber

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
    support.menu(itemlist, 'Disegni che si muovono sullo schermo per magia bold', 'serietv', "%s/category/animazione/" % host, 'tvshow', args= ['disegni'])
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
    elif 'cat' in item.args:
        patron = r'<a\shref="([^"]+)".*?>\s<img\s.*?src="([^"]+)" />[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)</p></div>'
        patron_block = r'<div\sclass="col-xs-\d+ col-sm-\d+-\d+">(.*?)<div\sclass="container-fluid whitebg" style="">'
        patronNext = r'<link\s.*?rel="next"\shref="([^"]+)"'
    elif 'cerca' in item.args:
        patron = r'<a\shref="([^"]+)".*?>\s<img\s.*?src="([^"]+)" />[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)</p></div>'
        patron_block = r'<div\sclass="col-xs-\d+ col-sm-\d+-\d+">(.*?)<div\sclass="container-fluid whitebg" style="">'
        patronNext = r'<link\s.*?rel="next"\shref="([^"]+)"'
    elif 'disegni' in item.args:
        patron = r'<a\shref="([^"]+)".*?>\s<img\s.*?src="([^"]+)" />[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)</p></div>'
        patron_block = r'<div\sclass="col-xs-\d+ col-sm-\d+-\d+">(.*?)<div\sclass="container-fluid whitebg" style="">'
        patronNext = r'<link\s.*?rel="next"\shref="([^"]+)"'
    elif 'update' in item.args:
        listGroups = ['url', 'thumb', 'episode', 'lang', 'title']
        patron = r'rel="nofollow" href="([^"]+)"[^>]+> <img.*?src="([^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(\d+.\d+) \((.+?)\).<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)<[^>]+>'
        patron_block = r'meta-slug="lastep">(.*?)</div></div><div'   
        # permette di vedere episodio e titolo + titolo2 in novità
        def itemHook(item):
            item.show = item.episode + item.title
            return item    
    return locals()

@support.scrape
def episodios(item):
    log('episodios ->\n')
    item.contentType = 'episode'
    
    action = 'findvideos'
    listGroups = ['episode', 'lang', 'title', 'plot', 'url']
##    patron = r'(?:TITOLO ORIGINALE:</b>(.*?)</p>|'\
##             '<a rel="nofollow"\s*class="number-episodes-on-img"> (\d+.\d+).(?:|\((.*?)\))'\
##             '[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(.*?)<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(.*?)<[^>]+>[^>]+>[^>]+>.<(.*?)>)'
    patron = r'class="number-episodes-on-img"> (\d+.\d+)(?:|[ ]\((.*?)\))'\
             '<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(.*?)<[^>]+>[^>]+>[^>]+>[^>]+>'\
             '[^>]+>[^>]+>(.*?)<[^>]+></div></div>.<span\s(.*?)</span>'    
    return locals()

def findvideos(item):
    log()
    return support.server(item, item.url)

@support.scrape
def categorie(item):
    log

    action = 'serietv'
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
##
##
### ================================================================================================================
##
### ----------------------------------------------------------------------------------------------------------------

def search(item, texto):
    log(texto)
    item.url = host + "/?s=" + texto
    item.args = 'cerca'
    try:
        return serietv(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
##
##

### ----------------------------------------------------------------------------------------------------------------
##
##def nuoveserie(item):
##    log()
##    itemlist = []
##
##    patron_block = ''
##    if 'inedite' in item.args:
##        patron_block = r'<div class="container container-title-serie-ined container-scheda" meta-slug="ined">(.*?)</div></div><div'
##    elif 'da non perdere' in item.args:
##        patron_block = r'<div class="container container-title-serie-danonperd container-scheda" meta-slug="danonperd">(.*?)</div></div><div'
##    elif 'classiche' in item.args:
##        patron_block = r'<div class="container container-title-serie-classiche container-scheda" meta-slug="classiche">(.*?)</div></div><div'
##    else:
##        patron_block = r'<div class="container container-title-serie-new container-scheda" meta-slug="new">(.*?)</div></div><div'
##
##    patron = r'<a href="([^"]+)".*?><img\s.*?src="([^"]+)" \/>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)<\/p>'
##
##    matches = support.match(item, patron, patron_block, headers)[0]
##
##    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
##        scrapedtitle = cleantitle(scrapedtitle)
##
##        itemlist.append(
##            Item(channel=item.channel,
##                 action="episodios",
##                 contentType="tvshow",
##                 title=scrapedtitle,
##                 fulltitle=scrapedtitle,
##                 url=scrapedurl,
##                 show=scrapedtitle,
##                 thumbnail=scrapedthumbnail,
##                 folder=True))
##
##    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
##    return itemlist
##
##

##def categorie(item):
##    log()
##    return support.scrape(item, r'<li>\s<a\shref="([^"]+)"[^>]+>([^<]+)</a></li>', ['url', 'title'], patron_block=r'<ul\sclass="dropdown-menu category">(.*?)</ul>', headers=headers, action="lista_serie")
##
##
### ================================================================================================================
##
### ----------------------------------------------------------------------------------------------------------------
##def lista_serie(item):
##    log()
##    itemlist = []
##
##    patron_block = r'<div\sclass="col-xs-\d+ col-sm-\d+-\d+">(.*?)<div\sclass="container-fluid whitebg" style="">'
##    patron = r'<a\shref="([^"]+)".*?>\s<img\s.*?src="([^"]+)" />[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)</p></div>'
##
##    return support.scrape(item, patron, ['url', 'thumb', 'title'], patron_block=patron_block, patronNext=r"<link\s.*?rel='next'\shref='([^']*)'", action='episodios')
##
##
### ================================================================================================================
##
### ----------------------------------------------------------------------------------------------------------------
##def episodios(item):
##    log()
##    itemlist = []
##
##    patron = r'<div\sclass="[^"]+">\s([^<]+)<\/div>[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)?[^>]+>[^>]+>[^>]+>[^>]+>[^>]+><p[^>]+>([^<]+)<[^>]+>[^>]+>[^>]+>'
##    patron += r'[^"]+".*?serie="([^"]+)".*?stag="([0-9]*)".*?ep="([0-9]*)"\s'
##    patron += r'.*?embed="([^"]+)"\s.*?embed2="([^"]+)?"\s.*?embed3="([^"]+)?"?[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s?'
##    patron += r'(?:<img\sclass="[^"]+" meta-src="([^"]+)"[^>]+>|<img\sclass="[^"]+" src="" data-original="([^"]+)"[^>]+>)?'
##
##    matches = support.match(item, patron, headers=headers)[0]
##
##    for scrapedtitle, scrapedepisodetitle, scrapedplot, scrapedserie, scrapedseason, scrapedepisode, scrapedurl, scrapedurl2, scrapedurl3, scrapedthumbnail, scrapedthumbnail2 in matches:
##        scrapedtitle = cleantitle(scrapedtitle)
##        scrapedepisode = scrapedepisode.zfill(2)
##        scrapedepisodetitle = cleantitle(scrapedepisodetitle)
##        title = str("%sx%s %s" % (scrapedseason, scrapedepisode, scrapedepisodetitle)).strip()
##        if 'SUB-ITA' in scrapedtitle:
##            title += " "+support.typo("Sub-ITA", '_ [] color kod')
##
##        infoLabels = {}
##        infoLabels['season'] = scrapedseason
##        infoLabels['episode'] = scrapedepisode
##        itemlist.append(
##            Item(channel=item.channel,
##                 action="findvideos",
##                 title=support.typo(title, 'bold'),
##                 fulltitle=scrapedtitle,
##                 url=scrapedurl + "\r\n" + scrapedurl2 + "\r\n" + scrapedurl3,
##                 contentType="episode",
##                 plot=scrapedplot,
##                 contentSerieName=scrapedserie,
##                 contentLanguage='Sub-ITA' if 'Sub-ITA' in title else '',
##                 infoLabels=infoLabels,
##                 thumbnail=scrapedthumbnail2 if scrapedthumbnail2 != '' else scrapedthumbnail,
##                 folder=True))
##
##    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
##
##    support.videolibrary(itemlist, item)
##
##    return itemlist

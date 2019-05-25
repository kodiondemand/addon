# -*- coding: utf-8 -*-
# -*- Channel Altadefinizione01L Film - Serie -*-
# -*- Creato per Alfa-addon -*-
# -*- e adattato for KOD -*-
# -*- By Greko -*-
# -*- last change: 04/05/2019


from channelselector import get_thumb
from core import httptools, scrapertools, servertools, tmdb, support
from core.item import Item
from platformcode import config, logger
from specials import autoplay, filtertools

__channel__ = "altadefinizione01_link"

#host = "https://altadefinizione01.link/" #riaggiornato al 29 aprile 2019
#host = "http://altadefinizione01.art/" # aggiornato al 22 marzo 2019
#host = "https://altadefinizione01.network/" #aggiornato al 22 marzo 2019
#host = "http://altadefinizione01.date/" #aggiornato al 3 maggio 2019
host = "https://altadefinizione01.voto/" #aggiornato al 3 maggio 2019

# ======== def per utility INIZIO ============================
    
checklinks = config.get_setting('checklinks', __channel__)
checklinks_number = config.get_setting('checklinks_number', __channel__)

headers = [['User-Agent', 'Mozilla/50.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'],
           ['Referer', host]]#,['Accept-Language','it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3']]

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['openload', 'streamcherry','rapidvideo', 'streamango', 'supervideo']
list_quality = ['default']

# =========== home menu ===================

def mainlist(item):
    """
    Creo il menu principale del canale
    :param item:
    :return: itemlist []
    """
    logger.info("%s mainlist log: %s" % (__channel__, item))
    itemlist = []

    autoplay.init(item.channel, list_servers, list_quality)
    # Menu Principale
    support.menu(itemlist, 'Film Ultimi Arrivi bold', 'peliculas', host)#, args='film')
    support.menu(itemlist, 'Genere', 'categorie', host, args=['','genres'])
    support.menu(itemlist, 'Per anno submenu', 'categorie', host, args=['Film per Anno','years'])
    support.menu(itemlist, 'Per qualità submenu', 'categorie', host, args=['Film per qualità','quality']) 
    support.menu(itemlist, 'Al Cinema bold', 'peliculas', host+'film-del-cinema')    
    support.menu(itemlist, 'Popolari bold', 'categorie', host+'piu-visti.html', args=['popular',''])
    support.menu(itemlist, 'Mi sento fortunato bold', 'categorie', host, args=['fortunato','lucky'])    
    support.menu(itemlist, 'Sub-ITA bold', 'peliculas', host+'film-sub-ita/')   
    support.menu(itemlist, 'Cerca film submenu', 'search', host)

    autoplay.show_option(item.channel, itemlist)
    
    return itemlist

# ======== def in ordine di menu ===========================

def peliculas(item):
    logger.info("%s mainlist peliculas log: %s" % (__channel__, item))
    itemlist = []
    # scarico la pagina
    data = httptools.downloadpage(item.url, headers=headers).data
    # da qui fare le opportuni modifiche
    patron = 'class="innerImage">.*?href="([^"]+)".*?src="([^"]+)".*?'\
             'class="ml-item-title">([^"]+)</.*?class="ml-item-label">'\
             '(.*?)<.*?class="ml-item-label">.*?class="ml-item-label">(.*?)</'
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl, scrapedimg, scrapedtitle, scrapedyear, scrapedlang in matches:
        if 'italiano' in scrapedlang.lower():
            scrapedlang = 'ITA'
        else:
            scrapedlang = 'Sub-Ita'
        itemlist.append(Item(
            channel=item.channel,
            action="findvideos",
            contentTitle=scrapedtitle,
            fulltitle=scrapedtitle,
            url=scrapedurl,
            infoLabels={'year': scrapedyear},
            contenType="movie",
            thumbnail=scrapedimg,
            title="%s [%s]" % (scrapedtitle, scrapedlang),
            language=scrapedlang,
            context="buscar_trailer"
        ))

    # poichè il sito ha l'anno del film con TMDB la ricerca titolo-anno è esatta quindi inutile fare lo scrap delle locandine 
    # e della trama dal sito che a volte toppano
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Paginazione
    support.nextPage(itemlist,item,data,'<span>\d</span> <a href="([^"]+)">')
                    
    return itemlist

# =========== def pagina categorie ======================================

def categorie(item):
    logger.info("%s mainlist categorie log: %s" % (__channel__, item))
    itemlist = []
    # scarico la pagina
    data = httptools.downloadpage(item.url, headers=headers).data

    # da qui fare le opportuni modifiche
    if item.args[1] == 'genres':
        bloque = scrapertools.find_single_match(data, '<ul class="listSubCat" id="Film">(.*?)</ul>')
    elif item.args[1] == 'years':
        bloque = scrapertools.find_single_match(data, '<ul class="listSubCat" id="Anno">(.*?)</ul>')
    elif item.args[1] == 'quality':
        bloque = scrapertools.find_single_match(data, '<ul class="listSubCat" id="Qualita">(.*?)</ul>')
    elif item.args[1] == 'lucky': # sono i titoli random nella pagina, alcuni rimandano solo a server a pagamento
        bloque = scrapertools.find_single_match(data, 'FILM RANDOM.*?class="listSubCat">(.*?)</ul>')        
    patron = '<li><a href="/(.*?)">(.*?)<'
    matches = scrapertools.find_multiple_matches(bloque, patron)

    if item.args[1] == 'lucky':
        bloque = scrapertools.find_single_match(data, 'FILM RANDOM.*?class="listSubCat">(.*?)</ul>')    
        patron = '<li><a href="(.*?)">(.*?)<'
        matches = scrapertools.find_multiple_matches(bloque, patron)
        
    for scrapurl, scraptitle in sorted(matches):
        if item.args[1] != 'lucky':
            url = host+scrapurl
            action="peliculas"
        else:
            url = scrapurl
            action = "findvideos_film"
        itemlist.append(Item(
            channel=item.channel,
            action=action,
            title = scraptitle,
            url=url,
            thumbnail=get_thumb(scraptitle, auto = True),
            Folder = True,
        ))

    return itemlist


# =========== def pagina del film con i server per verderlo =============
# da sistemare che ne da solo 1 come risultato

def findvideos(item):
    logger.info("%s mainlist findvideos_film log: %s" % (__channel__, item))
    itemlist = []
    # scarico la pagina
    #data = scrapertools.cache_page(item.url) #non funziona più?
    data = httptools.downloadpage(item.url, headers=headers).data
    # da qui fare le opportuni modifiche
    patron = '<li.*?<a href="#" data-target="(.*?)">'
    matches = scrapertools.find_multiple_matches(data, patron)
    #logger.info("altadefinizione01_linkMATCHES: %s " % matches)
    for scrapedurl in matches:

        try:
            itemlist = servertools.find_video_items(data=data)

            for videoitem in itemlist:
                logger.info("Videoitemlist2: %s" % videoitem)
                videoitem.title = "%s [%s]" % (item.contentTitle, videoitem.title)#"[%s] %s" % (videoitem.server, item.title) #"[%s]" % (videoitem.title)
                videoitem.show = item.show
                videoitem.contentTitle = item.contentTitle
                videoitem.contentType = item.contentType
                videoitem.channel = item.channel
                videoitem.year = item.infoLabels['year']
                videoitem.infoLabels['plot'] = item.infoLabels['plot']
        except AttributeError:
            logger.error("data doesn't contain expected URL")

    # Controlla se i link sono validi
    if checklinks:
        itemlist = servertools.check_list_links(itemlist, checklinks_number)

    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    
    # Aggiunge alla videoteca
    if  item.extra != 'findvideos' and item.extra != "library" and config.get_videolibrary_support() and len(itemlist) != 0 :
       support.videolibrary(itemlist, item)

    return itemlist

# =========== def per cercare film/serietv =============
#host+/index.php?do=search&story=avatar&subaction=search
def search(item, text):
    logger.info("%s mainlist search log: %s %s" % (__channel__, item, text))
    itemlist = []
    text = text.replace(" ", "+")
    item.url = host+"/index.php?do=search&story=%s&subaction=search" % (text)
    #item.extra = "search"
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
    logger.info("%s mainlist search log: %s" % (__channel__, categoria))
    itemlist = []
    item = Item()
    #item.extra = 'film'
    try:
        if categoria == "film":
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

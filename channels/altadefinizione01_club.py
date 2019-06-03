# -*- coding: utf-8 -*-
# -*- Channel Altadefinizione01C Film -*-
# -*- Riscritto per KOD -*-
# -*- By Greko -*-
# -*- last change: 04/05/2019


from channelselector import get_thumb
from core import httptools, channeltools, scrapertools, servertools, tmdb, support
from core.item import Item
from platformcode import config, logger
from specials import autoplay, filtertools

__channel__ = "altadefinizione01_club"
host = config.get_channel_url(__channel__)

# ======== Funzionalità =============================

checklinks = config.get_setting('checklinks', __channel__)
checklinks_number = config.get_setting('checklinks_number', __channel__)

headers = [['User-Agent', 'Mozilla/50.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'],
           ['Referer', host]]

parameters = channeltools.get_channel_parameters(__channel__)
fanart_host = parameters['fanart']
thumbnail_host = parameters['thumbnail']

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['verystream','openload','rapidvideo','streamango'] # per l'autoplay
list_quality = ['default'] #'rapidvideo', 'streamango', 'openload', 'streamcherry'] # per l'autoplay


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
    support.menu(itemlist, 'Film Ultimi Arrivi bold', 'peliculas', host, args='pellicola')
    support.menu(itemlist, 'Genere', 'categorie', host, args='genres')
    support.menu(itemlist, 'Per anno submenu', 'categorie', host, args=['Film per Anno','years'])
    support.menu(itemlist, 'Per lettera', 'categorie', host+'catalog/a/', args=['Film per Lettera','orderalf'])
    support.menu(itemlist, 'Al Cinema bold', 'peliculas', host+'cinema/', args='pellicola')
    support.menu(itemlist, 'Sub-ITA bold', 'peliculas', host+'sub-ita/', args='pellicola')   
    support.menu(itemlist, 'Cerca film submenu', 'search', host)

    autoplay.show_option(item.channel, itemlist)
    
    return itemlist

# ======== def in ordine di menu ===========================
# =========== def per vedere la lista dei film =============

def peliculas(item):
    logger.info("%s mainlist peliculas log: %s" % (__channel__, item))
    itemlist = []
    # scarico la pagina
    data = httptools.downloadpage(item.url, headers=headers).data
    # da qui fare le opportuni modifiche
    if item.args != 'orderalf':
        if item.args == 'pellicola' or item.args == 'years':
            bloque = scrapertools.find_single_match(data, '<div class="cover boxcaption">(.*?)<div id="right_bar">')
        elif item.args == "search":
            bloque = scrapertools.find_single_match(data, '<div class="cover boxcaption">(.*?)</a>')
        else:
            bloque = scrapertools.find_single_match(data, '<div class="cover boxcaption">(.*?)<div class="page_nav">')
        patron = '<h2>.<a href="(.*?)".*?src="(.*?)".*?class="trdublaj">(.*?)<div class="ml-item-hiden".*?class="h4">(.*?)<.*?label">(.*?)</span'
        matches = scrapertools.find_multiple_matches(data, patron)
        for scrapedurl, scrapedimg, scrapedqualang, scrapedtitle, scrapedyear in matches:

            if 'sub ita' in scrapedqualang.lower():
                scrapedlang = 'Sub-Ita'
            else:
                scrapedlang = 'ITA'
            itemlist.append(Item(
                channel=item.channel,
                action="findvideos",
                contentTitle=scrapedtitle,
                fulltitle=scrapedtitle,
                url=scrapedurl,
                infoLabels={'year': scrapedyear},
                contenType="movie",
                thumbnail=host+scrapedimg,
                title= "%s [%s]" % (scrapedtitle, scrapedlang),
                language=scrapedlang
                ))

    # poichè  il sito ha l'anno del film con TMDB la ricerca titolo-anno è esatta quindi inutile fare lo scrap delle locandine 
    # e della trama dal sito che a volte toppano
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Paginazione
    support.nextPage(itemlist,item,data,'<span>[^<]+</span>[^<]+<a href="(.*?)">')
    
    return itemlist

# =========== def pagina categorie ======================================

def categorie(item):
    logger.info("%s mainlist categorie log: %s" % (__channel__, item))
    itemlist = []
    # scarico la pagina
    data = httptools.downloadpage(item.url, headers=headers).data

    # da qui fare le opportuni modifiche
    if item.args == 'genres':
        bloque = scrapertools.find_single_match(data, '<ul class="kategori_list">(.*?)</ul>')
        patron = '<li><a href="/(.*?)">(.*?)</a>'
    elif item.args[1] == 'years':
        bloque = scrapertools.find_single_match(data, '<ul class="anno_list">(.*?)</ul>')
        patron = '<li><a href="/(.*?)">(.*?)</a>'
    elif item.args[1] == 'orderalf':
        bloque = scrapertools.find_single_match(data, '<div class="movies-letter">(.*)<div class="clearfix">')
        patron = '<a title=.*?href="(.*?)"><span>(.*?)</span>'

    matches = scrapertools.find_multiple_matches(bloque, patron)

    for scrapurl, scraptitle in sorted(matches):

        if "01" in scraptitle:
          continue
        else:
          scrapurl = host+scrapurl

        if item.args[1] != 'orderalf': action = "peliculas"
        else: action = 'orderalf'
        itemlist.append(Item(
            channel=item.channel,
            action= action,
            title = scraptitle,
            url= scrapurl,
            thumbnail = get_thumb(scraptitle, auto = True),
            extra = item.extra,
        ))

    return itemlist

# =========== def pagina lista alfabetica ===============================

def orderalf(item):
    logger.info("%s mainlist orderalf log: %s" % (__channel__, item))
    itemlist = []
    # scarico la pagina
    data = httptools.downloadpage(item.url, headers=headers).data
    # da qui fare le opportuni modifiche
    patron = '<td class="mlnh-thumb"><a href="(.*?)".title="(.*?)".*?src="(.*?)".*?mlnh-3">(.*?)<.*?"mlnh-5">.<(.*?)<td' #scrapertools.find_single_match(data, '<td class="mlnh-thumb"><a href="(.*?)".title="(.*?)".*?src="(.*?)".*?mlnh-3">(.*?)<.*?"mlnh-5">.<(.*?)<td')
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle, scrapedimg, scrapedyear, scrapedqualang in matches:

            if 'sub ita' in scrapedqualang.lower():
                scrapedlang = 'Sub-ita'
            else:
                scrapedlang = 'ITA'
            itemlist.append(Item(
                channel=item.channel,
                action="findvideos_film",
                contentTitle=scrapedtitle,
                fulltitle=scrapedtitle,
                url=scrapedurl,
                infoLabels={'year': scrapedyear},
                contenType="movie",
                thumbnail=host+scrapedimg,
                title = "%s [%s]" % (scrapedtitle, scrapedlang),
                language=scrapedlang,
                context="buscar_trailer"
            ))

    # se il sito permette l'estrazione dell'anno del film aggiungere la riga seguente
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Paginazione
    support.nextPage(itemlist,item,data,'<span>[^<]+</span>[^<]+<a href="(.*?)">')

    return itemlist

# =========== def pagina del film con i server per verderlo =============

def findvideos(item):
    logger.info("%s mainlist findvideos_film log: %s" % (__channel__, item))
    itemlist = []

    # scarico la pagina
    data = httptools.downloadpage(item.url, headers=headers).data
    # da qui fare le opportuni modifiche
    patron = '<a href="#" data-link="(.*?)">'
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl in matches:
        logger.info("altadefinizione01_club scrapedurl log: %s" % scrapedurl)
        try:
            itemlist = servertools.find_video_items(data=data)

            for videoitem in itemlist:
                logger.info("Videoitemlist2: %s" % videoitem)
                videoitem.title = "%s [%s]" % (item.contentTitle, videoitem.title)
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
#http://altadefinizione01.link/index.php?do=search&story=avatar&subaction=search
def search(item, text):
    logger.info("%s mainlist search log: %s %s" % (__channel__, item, text))
    itemlist = []
    text = text.replace(" ", "+")
    item.url = host+"index.php?do=search&story=%s&subaction=search" % (text)
    #item.extra = "search"
    try:
        return peliculas(item)
    # Cattura la eccezione così non interrompe la ricerca globle se il canale si rompe!
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s Sono qua: %s" % (__channel__, line))
        return []

# =========== def per le novità nel menu principale =============

def newest(categoria):
    logger.info("%s mainlist newest log: %s %s %s" % (__channel__, categoria))
    itemlist = []
    item = Item()
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

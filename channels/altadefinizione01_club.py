# -*- coding: utf-8 -*-
# -*- Channel Altadefinizione01C Film -*-
# -*- Created for IcarusbyGreko -*-
# -*- By Greko -*-
# -*- last change: 3/05/2019

from channelselector import get_thumb
from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from core import channeltools
from core import tmdb
from platformcode import config, logger

__channel__ = "altadefinizione01_club"

#host = "https://www.altadefinizione01.club/" # host da cambiare
#host = "https://www.altadefinizione01.team/" #aggiornato al 22 marzo 2019
host = "https://www.altadefinizione01.vision/" #aggiornato al 30-04-209
# ======== def per utility INIZIO =============================
try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
    __perfil__ = int(config.get_setting('perfil', __channel__))
except:
    __modo_grafico__ = True
    __perfil__ = 0

# Fijar perfil de color
perfil = [['0xFFFFE6CC', '0xFFFFCE9C', '0xFF994D00', '0xFFFE2E2E', '0xFFFFD700'],
          ['0xFFA5F6AF', '0xFF5FDA6D', '0xFF11811E', '0xFFFE2E2E', '0xFFFFD700'],
          ['0xFF58D3F7', '0xFF2E9AFE', '0xFF2E64FE', '0xFFFE2E2E', '0xFFFFD700']]

if __perfil__ < 3:
    color1, color2, color3, color4, color5 = perfil[__perfil__]
else:
    color1 = color2 = color3 = color4 = color5 = ""

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', __channel__)
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', __channel__)

headers = [['User-Agent', 'Mozilla/50.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'],
           ['Referer', host]]

#parameters = channeltools.get_channel_parameters(__channel__)
#fanart_host = parameters['fanart']
#thumbnail_host = parameters['thumbnail']

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
    title = ''

    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist = [
        # new upload
        Item(channel=__channel__, title="Ultimi Arrivi", action="peliculas",
             url="%s" % host, text_color=color4, extra="film",
             infoLabels={'plot': item.category},
             thumbnail=get_thumb(title, auto = True)
             ),
        # x to Cinema
        Item(channel=__channel__, title="Al Cinema", action="peliculas",
             url="%scinema/" % host, text_color=color4, extra="film",
             infoLabels={'plot': item.category},
             thumbnail = get_thumb(title, auto = True)
             ),
        # x Sub-ita
        Item(channel=__channel__, title="Sottotitolati", action="peliculas",
             url="%ssub-ita/" % host, text_color=color4, extra="film",
             infoLabels={'plot': item.category},
             thumbnail = get_thumb(title, auto = True)
             ),
        # x Category
        Item(channel=__channel__, title="Generi", action="categorie",
             url="%s" % host, text_color=color4, extra="genres",
             viewcontent='movies',
             infoLabels={'plot': item.category},
             thumbnail = get_thumb(title, auto = True)
             ),
        # x year
        Item(channel=__channel__, title="Anno", action="categorie",
             url="%s" % host, text_color=color4, extra="year",
             infoLabels={'plot': item.category},
             thumbnail = get_thumb(title, auto = True)
             ),
       # x lettera
       Item(channel=__channel__, title="Lettera", action="categorie",
            url="%scatalog/a/" % host, text_color=color4, extra="orderalf",
             infoLabels={'plot': item.category},
             thumbnail = get_thumb(title, auto = True)
            ),
        # Search
        Item(channel=__channel__, title="Cerca Film...", action="search",
             text_color=color4, extra="",
             infoLabels={'plot': item.category},
             thumbnail = get_thumb(title, auto = True)
             ),
                ]

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
    if item.extra != 'orderalf':
        if item.extra == 'film' or item.extra == 'year':
            bloque = scrapertools.find_single_match(data, '<div class="cover boxcaption">(.*?)<div id="right_bar">')
        elif item.extra == "search":
            bloque = scrapertools.find_single_match(data, '<div class="cover boxcaption">(.*?)</a>')
        else: #item.extra == 'cat':
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
                action="findvideos_film",
                contentTitle=scrapedtitle,
                fulltitle=scrapedtitle,
                url=scrapedurl,
                infoLabels={'year': scrapedyear},
                contenType="movie",
                thumbnail=host+scrapedimg,
                title= "%s [%s]" % (scrapedtitle, scrapedlang),
                text_color=color5,
                language=scrapedlang
                ))

    # se il sito permette l'estrazione dell'anno del film aggiungere la riga seguente
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Paginazione
    next_page = scrapertools.find_single_match(data, "<link rel='next' href='(.*?)' />")
    if not next_page:
        next_page = scrapertools.find_single_match(data, '<span>\d</span> <a href="([^"]+)">')

    if next_page != "":
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title=config.get_localized_string(30992),
                 url=next_page,
                 extra=item.extra,
                 text_color=color4,
                 #thumbnail="http://icons.iconarchive.com/icons/ahmadhania/spherical/128/forward-icon.png"
                 thumbnail= get_thumb('nextpage', auto = True)
                 ))

    return itemlist

# =========== def pagina categorie ======================================

def categorie(item):
    logger.info("%s mainlist categorie log: %s" % (__channel__, item))
    itemlist = []
    # scarico la pagina
    data = httptools.downloadpage(item.url, headers=headers).data

    # da qui fare le opportuni modifiche
    if item.extra == 'genres':
        bloque = scrapertools.find_single_match(data, '<ul class="kategori_list">(.*?)</ul>')
        patron = '<li><a href="/(.*?)">(.*?)</a>'
    elif item.extra == 'year':
        bloque = scrapertools.find_single_match(data, '<ul class="anno_list">(.*?)</ul>')
        patron = '<li><a href="/(.*?)">(.*?)</a>'
    elif item.extra == 'orderalf':
        bloque = scrapertools.find_single_match(data, '<div class="movies-letter">(.*)<div class="clearfix">')
        patron = '<a title=.*?href="(.*?)"><span>(.*?)</span>'

    matches = scrapertools.find_multiple_matches(bloque, patron)

    for scrapurl, scraptitle in sorted(matches):

        if "01" in scraptitle:
          continue
        else:
          scrapurl = host+scrapurl

        if item.extra != 'orderalf':
            action = "peliculas"
        else:
            action = 'orderalf'
        itemlist.append(Item(
            channel=item.channel,
            action= action,
            title = scraptitle,
            url= scrapurl,
            text_color=color4,
            thumbnail = get_thumb(scraptitle, auto = True),
            extra = item.extra,
            #Folder = True,
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
                #title=scrapedtitle + ' %s' % scrapedlang,
                title = "%s [%s]" % (scrapedtitle, scrapedlang),
                text_color=color5,
                language=scrapedlang,
                context="buscar_trailer"
            ))

    # se il sito permette l'estrazione dell'anno del film aggiungere la riga seguente
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Paginazione
    next_page = scrapertools.find_single_match(data, "<link rel='next' href='(.*?)' />")
    if not next_page:
        next_page = scrapertools.find_single_match(data, '<div class=\'wp-pagenavi\'>.*?href="(.*?)">')

    if next_page != "":
        itemlist.append(
            Item(channel=item.channel,
                 action="orderalf",
                 title=config.get_localized_string(30992),
                 url=next_page,
                 extra=item.extra,
                 text_color=color4,
                 thumbnail= get_thumb('nextpage', auto = True)
                 ))

    return itemlist

# =========== def pagina del film con i server per verderlo =============

def findvideos_film(item):
    logger.info("%s mainlist findvideos_film log: %s" % (__channel__, item))
    itemlist = []

    # scarico la pagina
    #data = scrapertools.cache_page(item.url)
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
                videoitem.title = "%s [%s]" % (item.contentTitle, videoitem.title)#"[%s] %s" % (videoitem.server, item.title) #"[%s]" % (videoitem.title)
                videoitem.show = item.show
                videoitem.contentTitle = item.contentTitle
                videoitem.contentType = item.contentType
                videoitem.channel = item.channel
                videoitem.text_color = color5
                videoitem.year = item.infoLabels['year']
                videoitem.infoLabels['plot'] = item.infoLabels['plot']
        except AttributeError:
            logger.error("data doesn't contain expected URL")

    # Controlla se i link sono validi
    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)

    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    
    # Opción "Añadir esta película a la biblioteca de KODI"
    if item.extra != "library":

        itemlist.append(Item(channel=__channel__, title="Aggiungi alla Videoteca", text_color="green",
                             action="add_pelicula_to_library", url=item.url,
                             thumbnail= get_thumb('videolibrary', auto = True),
                             contentTitle=item.contentTitle, infoLabels = item.infoLabels
                             ))
    
    return itemlist

# =========== def per cercare film/serietv =============
#http://altadefinizione01.link/index.php?do=search&story=avatar&subaction=search
def search(item, text):
    logger.info("%s mainlist search log: %s %s" % (__channel__, item, text))
    itemlist = []
    text = text.replace(" ", "+")
    item.url = host+"index.php?do=search&story=%s&subaction=search" % (text)
    item.extra = "search"
    try:
        return peliculas(item)
    # Se captura la excepciÛn, para no interrumpir al buscador global si un canal falla
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

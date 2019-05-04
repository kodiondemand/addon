# -*- coding: utf-8 -*-
# -*- Created or modificated for Alfa-Addon -*-
# -*- adpted for KOD -*-
# -*- By Greko -*-

#import base64
import re
import urlparse
# gli import sopra sono da includere all'occorrenza
# per url con ad.fly
from lib import unshortenit

from channelselector import get_thumb
from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertoolsV2
from core import servertools
from core.item import Item
from core import channeltools
from core import tmdb
from platformcode import config, logger

__channel__ = "eurostreaming" #stesso di id nel file json

#host = "https://eurostreaming.zone/"
#host = "https://eurostreaming.black/" 
host = "https://eurostreaming.cafe/" #aggiornato al 30-04-2019

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
           ['Referer', host]]#,['Accept-Language','it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3']]

parameters = channeltools.get_channel_parameters(__channel__)
fanart_host = parameters['fanart']
thumbnail_host = parameters['thumbnail']

IDIOMAS = {'Italiano': 'IT', 'VOSI':'SUB ITA'}
list_language = IDIOMAS.values()
# per l'autoplay
list_servers = ['openload', 'speedvideo', 'wstream', 'streamango' 'flashx', 'nowvideo']
list_quality = ['default'] 

# =========== home menu ===================

def mainlist(item):
    logger.info("icarus.eurostreaming mainlist")
    itemlist = []
    title = ''

    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist = [
        Item(channel=__channel__, title="Serie TV",
            contentTitle = __channel__, action="serietv",
            #extra="tvshow",
            text_color=color4,
            url="%s/category/serie-tv-archive/" % host,
            infoLabels={'plot': item.category},
            thumbnail = get_thumb(title, auto = True)
            ),
        Item(channel=__channel__, title="Ultimi Aggiornamenti",
             contentTitle = __channel__, action="elenco_aggiornamenti_serietv",
             text_color=color4, url="%saggiornamento-episodi/" % host,
             #category = __channel__,
             extra="tvshow",
             infoLabels={'plot': item.category},
             thumbnail = get_thumb(title, auto = True)
             ),        
        Item(channel=__channel__,
            title="Anime / Cartoni",
            action="serietv",
            extra="tvshow",
            text_color=color4,
            url="%s/category/anime-cartoni-animati/" % host,
            thumbnail= get_thumb(title, auto = True)
            ),
        Item(channel=__channel__,
            title="[COLOR yellow]Cerca...[/COLOR]",
            action="search",
            extra="tvshow",
            text_color=color4,
            thumbnail= get_thumb(title, auto = True)
            ),
    ]
    
    autoplay.show_option(item.channel, itemlist)
    
    return itemlist

# ======== def in ordine di menu ===========================

def serietv(item):
    
    logger.info("%s serietv log: %s" % (__channel__, item))
    itemlist = []
    # Carica la pagina
    data = httptools.downloadpage(item.url).data

    # Estrae i contenuti
    patron = '<div class="post-thumb">\s*<a href="([^"]+)" title="([^"]+)">\s*<img src="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        #scrapedplot = ""
        scrapedtitle = scrapertoolsV2.decodeHtmlentities(scrapedtitle)#.replace("Streaming", ""))
        if scrapedtitle.startswith("Link to "):
            scrapedtitle = scrapedtitle[8:]
        num = scrapertoolsV2.find_single_match(scrapedurl, '(-\d+/)')
        if num:
            scrapedurl = scrapedurl.replace(num, "-episodi/")
        itemlist.append(
            Item(channel=item.channel,
                 action="episodios",
                 #contentType="tvshow",
                 contentSerieName = scrapedtitle,
                 title=scrapedtitle,
                 #text_color="azure",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 #plot=scrapedplot,
                 show=item.show,
                 extra=item.extra,
                 folder=True
                 ))

    # locandine e trama e altro da tmdb se presente l'anno migliora la ricerca
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True, idioma_busqueda='it')

    # Paginazione
    patronvideos = '<a class="next page-numbers" href="?([^>"]+)">Avanti &raquo;</a>'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)

    if len(matches) > 0:
        scrapedurl = urlparse.urljoin(item.url, matches[0])
        itemlist.append(
            Item(
                channel=item.channel,
                action="serietv",
                title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                url=scrapedurl,
                thumbnail=
                "http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                extra=item.extra,
                folder=True))

    return itemlist

def episodios(item):
    #logger.info("%s episodios log: %s" % (__channel__, item))
    itemlist = []

    if not(item.lang):
        lang_season = {'ITA':0, 'SUB ITA' :0}
        # Download pagina
        data = httptools.downloadpage(item.url).data
        #======== 
        if 'clicca qui per aprire' in data.lower():
            logger.info("%s CLICCA QUI PER APRIRE GLI EPISODI log: %s" % (__channel__, item))
            item.url = scrapertoolsV2.find_single_match(data, '"go_to":"(.*?)"')
            item.url = item.url.replace("\\","")
            # Carica la pagina
            data = httptools.downloadpage(item.url).data
            #logger.info("%s FINE CLICCA QUI PER APRIRE GLI EPISODI log: %s" % (__channel__, item))
        elif 'clicca qui</span>' in data.lower():
            logger.info("%s inizio CLICCA QUI</span> log: %s" % (__channel__, item))
            item.url = scrapertoolsV2.find_single_match(data, '<h2 style="text-align: center;"><a href="(.*?)">')
            data = httptools.downloadpage(item.url).data
            #logger.info("%s fine CLICCA QUI</span> log: %s" % (__channel__, item))
        #=========
        data = scrapertoolsV2.decodeHtmlentities(data)
        bloque = scrapertoolsV2.find_single_match(data, '<div class="su-accordion">(.*?)<div class="clear"></div>')
        patron = '<span class="su-spoiler-icon"></span>(.*?)</div>' 
        matches = scrapertoolsV2.find_multiple_matches(bloque, patron)
        for scrapedseason in matches:
            #logger.info("%s scrapedseason log: %s" % (__channel__, scrapedseason))
            if "(SUB ITA)" in scrapedseason.upper():
                lang = "SUB ITA"
                lang_season['SUB ITA'] +=1
            else:
                lang = "ITA"
                lang_season['ITA'] +=1
            #logger.info("%s lang_dict log: %s" % (__channel__, lang_season))
        
        for lang in sorted(lang_season):
            if lang_season[lang] > 0:
                itemlist.append(
                    Item(channel = item.channel,
                         action = "episodios",
                         #contentType = "episode",
                         contentSerieName = item.title, 
                         title = '%s (%s)' % (item.title, lang),
                         url = item.url,
                         fulltitle = item.title,
                         data = data,
                         lang = lang,
                         show = item.show,
                         folder = True,
                         ))
                
        # locandine e trama e altro da tmdb se presente l'anno migliora la ricerca
        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True, idioma_busqueda='it')
        
        return itemlist

    else:
        # qui ci vanno le puntate delle stagioni
        html = item.data
        logger.info("%s else log: [%s]" % (__channel__, item))

        if item.lang == 'SUB ITA':
            item.lang = '\(SUB ITA\)'
            logger.info("%s item.lang log: %s" % (__channel__, item.lang))
        bloque = scrapertoolsV2.find_single_match(html, '<div class="su-accordion">(.*?)<div class="clear"></div>')
        patron = '<span class="su-spoiler-icon"></span>.*?'+item.lang+'</div>(.*?)</div>' # leggo tutte le stagioni
        #logger.info("%s patronpatron log: %s" % (__channel__, patron))
        matches = scrapertoolsV2.find_multiple_matches(bloque, patron)
        for scrapedseason in matches:
            #logger.info("%s scrapedseasonscrapedseason log: %s" % (__channel__, scrapedseason))
            scrapedseason = scrapedseason.replace('<strong>','').replace('</strong>','')
            patron = '(\d+)×(\d+)(.*?)<(.*?)<br />' # stagione - puntanta - titolo - gruppo link
            matches = scrapertoolsV2.find_multiple_matches(scrapedseason, patron)
            for scrapedseason, scrapedpuntata, scrapedtitolo, scrapedgroupurl in matches:
                #logger.info("%s finale log: %s" % (__channel__, patron))
                scrapedtitolo = scrapedtitolo.replace('–','')
                itemlist.append(Item(channel = item.channel,
                    action = "findvideos",
                    contentType = "episode",
                    #contentSerieName = item.contentSerieName,
                    contentTitle = scrapedtitolo,
                    title = '%sx%s %s' % (scrapedseason, scrapedpuntata, scrapedtitolo),
                    url = scrapedgroupurl,
                    fulltitle = item.fulltitle,
                    #show = item.show,
                    #folder = True,
                    ))
                    
        logger.info("%s itemlistitemlist log: %s" % (__channel__, itemlist))

        # Opción "Añadir esta película a la biblioteca de KODI"
        if item.extra != "library":
            if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
                itemlist.append(Item(channel=item.channel, title="%s" % config.get_localized_string(30161),
                                     text_color="green", extra="episodios",
                                     action="add_serie_to_library", url=item.url,
                                     thumbnail= get_thumb('videolibrary', auto = True),
                                     contentTitle=item.contentSerieName, lang = item.lang,
                                     show=item.show, data = html
                                     #, infoLabels = item.infoLabels
                                     ))

        return itemlist 

# ===========  def ricerca  =============
def search(item, texto):
    #logger.info("[eurostreaming.py] " + item.url + " search " + texto)
    logger.info("%s search log: %s" % (__channel__, item))
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
    logger.info("%s newest log: %s" % (__channel__, categoria))
    itemlist = []
    item = Item()
    try:
    
        item.url = "%saggiornamento-episodi/" % host
        item.action = "elenco_aggiornamenti_serietv"
        itemlist = elenco_aggiornamenti_serietv(item)

        if itemlist[-1].action == "elenco_aggiornamenti_serietv":
            itemlist.pop()

    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist

# ===========  def pagina aggiornamenti  =============

# ======== Ultimi Aggiornamenti ===========================
def elenco_aggiornamenti_serietv(item):
    """
    def per la lista degli aggiornamenti
    """
    logger.info("%s elenco_aggiornamenti_serietv log: %s" % (__channel__, item))
    itemlist = []

    # Carica la pagina
    data = httptools.downloadpage(item.url).data

    # Estrae i contenuti
    #bloque = scrapertoolsV2.get_match(data, '<div class="entry">(.*?)<div class="clear"></div>')
    bloque = scrapertoolsV2.find_single_match(data, '<div class="entry">(.*?)<div class="clear"></div>')
    patron = '<span class="serieTitle".*?>(.*?)<.*?href="(.*?)".*?>(.*?)<'
    matches = scrapertoolsV2.find_multiple_matches(bloque, patron)

    for scrapedtitle, scrapedurl, scrapedepisodies in matches:
        if "(SUB ITA)" in scrapedepisodies.upper():
            lang = "SUB ITA"
            scrapedepisodies = scrapedepisodies.replace('(SUB ITA)','')
        else:
            lang = "ITA"
            scrapedepisodies = scrapedepisodies.replace(lang,'')
        #num = scrapertoolsV2.find_single_match(scrapedepisodies, '(-\d+/)')
        #if num:
        #    scrapedurl = scrapedurl.replace(num, "-episodi/")
        scrapedtitle = scrapedtitle.replace("–", "").replace('\xe2\x80\x93 ','').strip()
        scrapedepisodies = scrapedepisodies.replace('\xe2\x80\x93 ','').strip()
        itemlist.append(
            Item(
                 channel=item.channel,
                 action="episodios",
                 contentType="tvshow",
                 title = "%s" % scrapedtitle, # %s" % (scrapedtitle, scrapedepisodies),
                 fulltitle = "%s %s" % (scrapedtitle, scrapedepisodies),
                 text_color = color5,
                 url = scrapedurl,
                 #show = "%s %s" % (scrapedtitle, scrapedepisodies),
                 extra=item.extra,
                 #lang = lang,
                 #data = data,
                 folder=True))

    # locandine e trama e altro da tmdb se presente l'anno migliora la ricerca
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True, idioma_busqueda='it')

    return itemlist

# ===========  def per trovare i video  =============

def findvideos(item):
    logger.info("%s findvideos log: %s" % (__channel__, item))
    itemlist = []

    # Carica la pagina 
    data = item.url

    matches = re.findall(r'a href="([^"]+)"[^>]*>[^<]+</a>', data, re.DOTALL)

    data = []
    for url in matches:
        url, c = unshortenit.unshorten(url)
        data.append(url)

    try:
        itemlist = servertools.find_video_items(data=str(data))

        for videoitem in itemlist:
            logger.info("Videoitemlist2: %s" % videoitem)
            videoitem.title = "%s [%s]" % (item.contentTitle, videoitem.title)#"[%s] %s" % (videoitem.server, item.title) #"[%s]" % (videoitem.title)
            videoitem.show = item.show
            videoitem.contentTitle = item.contentTitle
            videoitem.contentType = item.contentType
            videoitem.channel = item.channel
            videoitem.text_color = color5
            #videoitem.language = item.language
            videoitem.year = item.infoLabels['year']
            videoitem.infoLabels['plot'] = item.infoLabels['plot']
    except AttributeError:
        logger.error("data doesn't contain expected URL")

    # Controlla se i link sono validi
    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)

    # Requerido para FilterTools
    # itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay
    autoplay.start(itemlist, item)


    return itemlist

# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per animeworld
# ----------------------------------------------------------
import re, urlparse

from core import httptools, scrapertoolsV2, servertools, tmdb, tvdb, support
from core.item import Item
from platformcode import logger, config
from specials import autoplay, filtertools, autorenumber
from channelselector import thumb



host = "https://www.animeworld.it"

headers = [['Referer', host]]

IDIOMAS = {'Italiano': 'Italiano'}
list_language = IDIOMAS.values()
list_servers = ['diretto']
list_quality = []

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'animeworld')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'animeworld')


def mainlist(item):
    logger.info("[animeworld.py] mainlist")
    
    itemlist =[]
    
    support.menu(itemlist, 'Anime ITA submenu bold', 'build_menu', host+'/filter?language[]=1')
    support.menu(itemlist, 'Anime SUB submenu bold', 'build_menu', host+'/filter?language[]=0')
    support.menu(itemlist, 'Anime A-Z sub', 'alfabetico', host+'/az-list')
    support.menu(itemlist, 'Anime - Ultimi Aggiunti', 'alfabetico', host+'/newest')
    support.menu(itemlist, 'Anime - Ultimi Episodi', 'alfabetico', host+'/newest')
    support.menu(itemlist, 'Cerca...', 'search')

    
    autoplay.init(item.channel, list_servers, list_quality)
    autoplay.show_option(item.channel, itemlist)

    return itemlist


# Crea Menu Filtro ======================================================

def build_menu(item):
    itemlist = []
    itemlist.append(Item(
                    channel=item.channel,
                    action="video",
                    title="[B]Tutti[/B]",
                    url=item.url))

    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\t','',data)
    data = re.sub(r'>\s*<','><',data)
 
    block = scrapertoolsV2.find_single_match(data, r'<form class="filters.*?>(.*?)<\/form>')
    
    matches = re.compile(r'<button class="btn btn-sm btn-default dropdown-toggle" data-toggle="dropdown"> (.*?) <span.*?>(.*?)<\/ul>', re.DOTALL).findall(block)

    for title, html in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action='build_sub_menu',
                 contentType="tvshow",
                 title='[B] > ' + title + '[/B]',
                 fulltitle=title,
                 show=title,
                 url=item.url,
                 html=html,
                 thumbnail=item.thumbnail,
                 fanart=item.fanart))

    # Elimina FLingua dal Menu
    itemlist.pop(6)
    itemlist.pop(6)

    itemlist = thumb(itemlist)

    return itemlist

# Crea SottoMenu Filtro ======================================================

def build_sub_menu(item):
    itemlist = []
    matches = re.compile(r'<input.*?name="(.*?)" value="(.*?)".*?><label.*?>(.*?)<\/label>', re.DOTALL).findall(item.html)
    for name, value, title in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action='video',
                 contentType="tvshow",
                 title='[B]' + title + ' >[/B]',
                 fulltitle=title,
                 show=title,
                 url=item.url + '&' + name + '=' + value,
                 plot=""))
    itemlist = thumb(itemlist)
    return itemlist

# Novità ======================================================

def newest(categoria):
    logger.info("[animeworld.py] newest")
    itemlist = []
    item = Item()
    try:
        if categoria == "anime":
            item.url = host + '/newest'
            item.action = "video"
            itemlist = video(item)

            if itemlist[-1].action == "video":
                itemlist.pop()
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


# Cerca ===========================================================

def search(item, texto):
    logger.info(texto)
    item.url = host + '/search?keyword=' + texto
    try:
        return video(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []




# Lista A-Z ====================================================

def alfabetico(item):
    logger.info("[animeworld.py] alfabetico")
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\t','',data)
    data = re.sub(r'>\s*<','><',data)

    block = scrapertoolsV2.find_single_match(data, r'<span>.*?A alla Z.<\/span>.*?<ul>(.*?)<\/ul>')

    matches = re.compile('<a href="([^"]+)" title="([^"]+)">', re.DOTALL).findall(block)
    scrapertoolsV2.printMatches(matches)

    for url, title in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action='lista_anime',
                 contentType="tvshow",
                 title=title,
                 fulltitle=title,
                 show=title,
                 url=url,
                 plot=""))

    return itemlist

def lista_anime(item):
    logger.info("[animeworld.py] lista_anime")

    itemlist = []

    # Carica la pagina
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\t','',data)
    data = re.sub(r'>\s*<','><',data)

    # Estrae i contenuti
    patron = r'<div class="item"><a href="([^"]+)".*?src="([^"]+)".*?data-jtitle="([^"]+)".*?>([^<]+)<\/a><p>(.*?)<\/p>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumb, scrapedoriginal, scrapedtitle, scrapedplot in matches:
        
        if scrapedoriginal == scrapedtitle:
            scrapedoriginal=''
        else:
            scrapedoriginal = ' - [ ' + scrapedoriginal + ' ]'

        year = ''
        lang = ''
        if '(' in scrapedtitle:
            year = scrapertoolsV2.find_single_match(scrapedtitle, r'(\([0-9]+\))')
            lang = scrapertoolsV2.find_single_match(scrapedtitle, r'(\([a-zA-Z]+\))')
        
        title = scrapedtitle.replace(year,'').replace(lang,'')
        original = scrapedoriginal.replace(year,'').replace(lang,'')
        title = '[B]' + title + '[/B]' + year + lang + original
        itemlist.append(
                Item(channel=item.channel,
                     extra=item.extra,
                     contentType="tvshow",
                     action="episodios",
                     text_color="azure",
                     title=title,
                     url=scrapedurl,
                     thumbnail=scrapedthumb,
                     fulltitle=title,
                     show=title,
                     plot=scrapedplot,
                     folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)    
    autorenumber.renumber(itemlist)

    # Next page
    next_page = scrapertoolsV2.find_single_match(data, '<a class="page-link" href="([^"]+)" rel="next"')

    if next_page != '':
        itemlist.append(
            Item(channel=item.channel,
                 action='lista_anime',
                 title='[B]' + config.get_localized_string(30992) + ' >[/B]',
                 url=next_page,
                 contentType=item.contentType,
                 thumbnail=thumb()))


    return itemlist


def video(item):
    logger.info("[animeworld.py] video")
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\t','',data)
    data = re.sub(r'>\s*<','><',data)

    patron = r'<a href="([^"]+)" class="poster.*?><img src="([^"]+)"(.*?)data-jtitle="([^"]+)" .*?>(.*?)<\/a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumb ,scrapedinfo, scrapedoriginal, scrapedtitle in matches:
        # Cerca Info come anno o lingua nel Titolo
        year = ''
        lang = ''
        if '(' in scrapedtitle:
            year = scrapertoolsV2.find_single_match(scrapedtitle, r'( \([0-9]+\))')
            lang = scrapertoolsV2.find_single_match(scrapedtitle, r'( \([a-zA-Z]+\))')
        
        # Rimuove Anno e Lingua nel Titolo
        title = scrapedtitle.replace(year,'').replace(lang,'')
        original = scrapedoriginal.replace(year,'').replace(lang,'')
        
        # Compara Il Titolo con quello originale
        if original == title:
            original=''
        else:
            original = ' - [ ' + scrapedoriginal + ' ]'

        # cerca info supplementari
        ep = ''
        ep = scrapertoolsV2.find_single_match(scrapedinfo, '<div class="ep">(.*?)<')
        if  ep != '':
            ep = ' - ' + ep

        ova = ''
        ova = scrapertoolsV2.find_single_match(scrapedinfo, '<div class="ova">(.*?)<')
        if  ova != '':
            ova = ' - (' + ova + ')'
        
        ona = ''
        ona = scrapertoolsV2.find_single_match(scrapedinfo, '<div class="ona">(.*?)<')
        if  ona != '':
            ona = ' - (' + ona + ')'

        movie = ''
        movie = scrapertoolsV2.find_single_match(scrapedinfo, '<div class="movie">(.*?)<')
        if  movie != '':
            movie = ' - (' + movie + ')'

        special = ''
        special = scrapertoolsV2.find_single_match(scrapedinfo, '<div class="special">(.*?)<')
        if  special != '':
            special = ' - (' + special + ')'


        # Concatena le informazioni
        info = ep + lang + year + ova + ona + movie + special

        # Crea il title da visualizzare
        long_title = '[B]' + title + '[/B]' + info + original

        # Controlla se sono Episodi o Film
        if movie == '':
            contentType = 'tvshow'
            action = 'episodios'
        else:
            contentType = 'movie'
            action = 'findvideos'
        
        itemlist.append(
                Item(channel=item.channel,
                     contentType=contentType,
                     action=action,
                     title=long_title,
                     url=scrapedurl,
                     fulltitle=title,
                     show=title,
                     thumbnail=scrapedthumb,
                     context = autoplay.context))
    
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    autorenumber.renumber(itemlist)

    # Next page
    next_page = scrapertoolsV2.find_single_match(data, '<a class="page-link" href=".*?page=([^"]+)" rel="next"')

    if next_page != '':
        itemlist.append(
            Item(channel=item.channel,
                 action='video',
                 title='[B]' + config.get_localized_string(30992) + ' >[/B]',
                 url=re.sub('&page=([^"]+)', '', item.url) + '&page=' + next_page,
                 contentType=item.contentType,
                 thumbnail=thumb()))

    return itemlist


def episodios(item):
    logger.info("[animeworld.py] episodios")
    itemlist = [] 

    data = httptools.downloadpage(item.url).data.replace('\n', '')
    data = re.sub(r'>\s*<', '><', data)
    block = scrapertoolsV2.find_single_match(data, r'<div class="widget servers".*?>(.*?)<div id="download"')
    block = scrapertoolsV2.find_single_match(block,r'<div class="server.*?>(.*?)<div class="server.*?>')
   
    patron = r'<li><a.*?href="([^"]+)".*?>(.*?)<\/a>'
    matches = re.compile(patron, re.DOTALL).findall(block)
    
    for scrapedurl, scrapedtitle in matches:
        scrapedtitle = '[B] Episodio ' + scrapedtitle + '[/B]'
        itemlist.append(
            Item(
                channel=item.channel,
                action="findvideos",
                contentType="episode",
                title=scrapedtitle,
                url=urlparse.urljoin(host, scrapedurl),
                fulltitle=scrapedtitle,
                show=scrapedtitle,
                plot=item.plot,
                fanart=item.thumbnail,
                thumbnail=item.thumbnail))
    
    autorenumber.renumber(itemlist, item,'bold')
    
    
    # Aggiungi a Libreria
    if config.get_videolibrary_support() and len(itemlist) != 0:
        itemlist.append(
            Item(
                channel=item.channel,
                title="[COLOR lightblue]%s[/COLOR]" % config.get_localized_string(30161),
                url=item.url,
                action="add_serie_to_library",
                extra="episodios",
                show=item.show))

    return itemlist


def findvideos(item):
    logger.info("[animeworld.py] findvideos")

    itemlist = []
   
    anime_id = scrapertoolsV2.find_single_match(item.url, r'.*\..*?\/(.*)')
    data = httptools.downloadpage(host + "/ajax/episode/serverPlayer?id=" + anime_id).data
    patron = '<source src="([^"]+)"'

    matches = re.compile(patron, re.DOTALL).findall(data)
    for video in matches:
        itemlist.append(
            Item(
                channel=item.channel,
                action="play",
                title=item.title + " [[COLOR orange]Diretto[/COLOR]]",
                url=video,
                server='directo',
                contentType=item.contentType,
                folder=False))

    # Requerido para Filtrar enlaces

    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)

    # Requerido para FilterTools

    # itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist



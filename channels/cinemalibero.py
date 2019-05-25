# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per CinemaLibero - First Version
# ------------------------------------------------------------
import re

from core import scrapertools, servertools, httptools, support
from core import tmdb
from core.item import Item
from lib import unshortenit
from platformcode import config
from platformcode import logger
from specials import autoplay

# Necessario per Autoplay
IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['akstream', 'wstream', 'openload', 'streamango']
list_quality = ['default']

# Necessario per Verifica Link
__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'cinemalibero')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'cinemalibero')

host = 'https://www.cinemalibero.icu'

headers = [['Referer', host]]



def mainlist(item):
    logger.info('[cinemalibero.py] mainlist')
    
    autoplay.init(item.channel, list_servers, list_quality) # Necessario per Autoplay

    # Menu Principale
    itemlist = []
    support.menu(itemlist, 'Film bold', 'video', host+'/category/film/')
    support.menu(itemlist, 'Generi submenu', 'genres', host)
    support.menu(itemlist, 'Cerca film submenu', 'search', host)
    support.menu(itemlist, 'Serie TV bold', 'video', host+'/category/serie-tv/', contentType='episode')
    support.menu(itemlist, 'Anime submenu', 'video', host+'/category/anime-giapponesi/', contentType='episode')
    support.menu(itemlist, 'Cerca serie submenu', 'search', host, contentType='episode')
    support.menu(itemlist, 'Sport bold', 'video', host+'/category/sport/')

    autoplay.show_option(item.channel, itemlist) # Necessario per Autoplay (Menu Configurazione)
    
    return itemlist


def search(item, texto):
    logger.info("[cinemalibero.py] " + item.url + " search " + texto)
    item.url = host + "/?s=" + texto
    try:
        return video(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
    return []


def genres(item):
    return support.scrape(item, patron_block=r'<div id="bordobar" class="dropdown-menu(.*?)</li>', patron=r'<a class="dropdown-item" href="([^"]+)" title="([A-z]+)"', listGroups=['url', 'title'], action='video')


def video(item):
    logger.info('[cinemalibero.py] video')
    itemlist = []

    if host not in item.url:
        item.url = host + item.url

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data.replace('\n','').replace('\t','')
    block = scrapertools.find_single_match(data, '<div class="container">.*?class="col-md-12[^"]*?">(.*?)<div class=(?:"container"|"bg-dark ")>')

    # Estrae i contenuti 
    matches = re.compile(r'<div class="col-lg-3">(.*?)<\/a><\/div>', re.DOTALL).findall(block)

    for match in matches:
        url = scrapertools.find_single_match(match, r'href="([^"]+)"')
        long_title = scrapertools.find_single_match(match, r'<div class="titolo">([^<]+)<\/div>')
        thumb = scrapertools.find_single_match(match, r'url=\((.*?)\)')
        quality = scrapertools.find_single_match(match, r'<div class="voto">([^<]+)<\/div>')
        genere = scrapertools.find_single_match(match, r'<div class="genere">([^<]+)<\/div>')

        year = scrapertools.find_single_match(long_title, r'\(([0-9)]+)') or scrapertools.find_single_match(long_title, r'\) ([0-9)]+)')
        lang = scrapertools.find_single_match(long_title, r'\(([a-zA-Z)]+)')
        
        title = re.sub(r'\(.*','',long_title)
        title = re.sub(r'(?:\(|\))','',title)
        if genere:
            genere = ' - [' + genere + ']'
        if year:
            long_title = title + ' - ('+ year + ')' + genere
        if lang:
            long_title = '[B]' + title + '[/B]' + ' - ('+ lang + ')' + genere
        else:
            long_title = '[B]' + title + '[/B]'
       
        # Seleziona fra Serie TV e Film
        if item.contentType == 'movie':
            tipologia = 'movie'
            action = 'findvideos'
        elif item.contentType == 'episode':
            tipologia = 'tv'
            action = 'episodios'
        else:
            tipologia = 'movie'
            action = 'select'

        itemlist.append(
            Item(channel=item.channel,
                 action=action,
                 contentType=item.contentType,
                 title=long_title,
                 fulltitle=title,
                 quality=quality,
                 url=url,
                 thumbnail=thumb,
                 infoLabels={'year': year},
                 show=title))

    # Next page
    next_page = scrapertools.find_single_match(data, '<a class="next page-numbers".*?href="([^"]+)">')

    if next_page != '':
        itemlist.append(
            Item(channel=item.channel,
                 action='video',
                 title='[B]' + config.get_localized_string(30992) + ' &raquo;[/B]',
                 url=next_page,
                 contentType=item.contentType,
                 thumbnail='http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png'))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def select(item):
    data = httptools.downloadpage(item.url, headers=headers).data
    block = scrapertools.find_single_match(data, r'<div class="col-md-8 bg-white rounded-left p-5"><div>(.*?)<\/div>')
    if re.findall('rel="category tag">serie', data, re.IGNORECASE):
        logger.info('select = ### è una serie ###')
        return episodios(Item(channel=item.channel,
                              title=item.title,
                              fulltitle=item.fulltitle,
                              url=item.url,
                              extra='serie',
                              contentType='episode'))
    elif re.findall('rel="category tag">anime', data, re.IGNORECASE):
        if re.findall('episodio', block, re.IGNORECASE):
            logger.info('select = ### è un anime ###')
            return episodios(Item(channel=item.channel,
                                title=item.title,
                                fulltitle=item.fulltitle,
                                url=item.url,
                                extra='anime',
                                contentType='episode'))
        else:
            logger.info('select = ### è un film ###')
            return findvideos(Item(channel=item.channel,
                                    title=item.title,
                                    fulltitle=item.fulltitle,
                                    url=item.url,
                                    contentType='movie'))
    else:
        logger.info('select = ### è un film ###')
        return findvideos(Item(channel=item.channel,
                              title=item.title,
                              fulltitle=item.fulltitle,
                              url=item.url,
                              contentType='movie'))


def findvideos(item): # Questa def. deve sempre essere nominata findvideos
    logger.info('[cinemalibero.py] findvideos')
    itemlist = []

    if item.args == 'direct':
        return servertools.find_video_items(item)

    if item.contentType == 'episode':
        data = item.url.lower()
        block = scrapertools.find_single_match(data,r'>streaming.*?<\/strong>*?<\/h2>(.*?)<\/div>')
        urls = re.findall('<a.*?href="([^"]+)"', block, re.DOTALL)
    else:
        data = httptools.downloadpage(item.url, headers=headers).data
        data = re.sub(r'\n|\t','',data).lower()
        block = scrapertools.find_single_match(data,r'>streaming.*?<\/strong>(.*?)<strong>')
        urls = re.findall('<a href="([^"]+)".*?class="external"', block, re.DOTALL)
    
    logger.info('URLS'+ str(urls))
    if urls:
        data =''
        for url in urls:
            url, c = unshortenit.unshorten(url)
            data += url + '\n'
                
    logger.info('DATA'+ data)
    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.fulltitle + ' - [COLOR limegreen][[/COLOR]'+videoitem.title+' [COLOR limegreen]][/COLOR]'
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.show = item.show
        videoitem.plot = item.plot
        videoitem.channel = item.channel
        videoitem.contentType = item.contentType

    # Link Aggiungi alla Libreria
    if item.contentType != 'episode':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findservers':
            itemlist.append(
                Item(channel=item.channel, title='[COLOR lightblue][B]Aggiungi alla videoteca[/B][/COLOR]', url=item.url,
                     action='add_pelicula_to_library', extra='findservers', contentTitle=item.contentTitle))

    # Necessario per filtrare i Link
    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)

    # Necessario per  FilterTools
    # itemlist = filtertools.get_links(itemlist, item, list_language)

    # Necessario per  AutoPlay
    autoplay.start(itemlist, item)
    
    
    return itemlist


def episodios(item): # Questa def. deve sempre essere nominata episodios
    logger.info('[cinemalibero.py] episodios')
    itemlist = []
    extra = ''

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data
    block = scrapertools.find_single_match(data, r'<div class="col-md-8 bg-white rounded-left p-5"><div>(.*?)at-below-post')
    if re.findall('rel="category tag">serie', data, re.IGNORECASE):
        # logger.info('select = ### è una serie ###')
        extra='serie'
    elif re.findall('rel="category tag">anime', data, re.IGNORECASE):
        if re.findall('episodi', block, re.IGNORECASE):
            # logger.info('select = ### è un anime ###')
            extra='anime'

    block = re.sub(r'<h2>.*?<\/h2>','',block)    
    block = block.replace('<p>','').replace('<p style="text-align: left;">','').replace('–<','<').replace('-<','<').replace('&#8211;<','<').replace('&#8211; <','<').replace('<strong>','<stop><start><strong>')+'<stop>'
    block = re.sub(r'stagione completa.*?<\/p>','',block,flags=re.IGNORECASE)
    

    if extra == 'serie':
        block = block.replace('<br /> <a','<a')
        matches = re.compile(r'<start>.*?(?:stagione|Stagione)(.*?)<\/(?:strong|span)><\/p>(.*?)<stop>', re.DOTALL).findall(block)

        if not matches:
            matches = scrapertools.find_multiple_matches(block, r'<a href="([^"]+)"[^>]+>(Episodio [0-9]+)</a>')
            for scrapedurl, scrapedtitle in matches:
                scrapedtitle = re.sub(r'Episodio ([0-9]+)', r'Episodio 1x\1', scrapedtitle)
                itemlist.append(
                    Item(channel=item.channel,
                         action="findvideos",
                         contentType='episode',
                         title=scrapedtitle,
                         fulltitle=scrapedtitle,
                         show=item.fulltitle,
                         url=scrapedurl,
                         args='direct'))
        else:
            for lang, html in matches:
                lang = re.sub('<.*?>','',lang)
                html = html.replace('<br />','\n').replace('</p>', '\n')

                matches = re.compile(r'([^<]+)([^\n]+)\n', re.DOTALL).findall(html)
                for scrapedtitle, html in matches:
                    itemlist.append(
                        Item(channel=item.channel,
                            action="findvideos",
                            contentType='episode',
                            title=scrapedtitle + ' - (' + lang + ')',
                            fulltitle=scrapedtitle,
                            show=item.fulltitle,
                            url=html))

    elif extra == 'anime':
        block = re.sub(r'<start.*?(?:download:|Download:).*?<stop>','',block)
        block = re.sub(r'(?:mirror|Mirror)[^<]+<','',block)
        block = block.replace('<br />','\n').replace('/a></p>','\n')
        block = re.sub(r'<start.*?(?:download|Download).*?\n','',block)
        matches = re.compile('<a(.*?)\n', re.DOTALL).findall(block)
        for html in matches:
            scrapedtitle = scrapertools.find_single_match(html, r'>(.*?)<\/a>')
            itemlist.append(
                Item(channel=item.channel,
                    action="findvideos",
                    contentType='episode',
                    title=scrapedtitle,
                    fulltitle=scrapedtitle,
                    show=item.fulltitle,
                    url=html))

    else:
        logger.info('select = ### è un film ###')
        return findvideos(Item(channel=item.channel,
                               title=item.title,
                               fulltitle=item.fulltitle,
                               url=item.url,
                               show=item.fulltitle,
                               contentType='movie'))
    
    if config.get_videolibrary_support() and len(itemlist) != 0:
        itemlist.append(
            Item(channel=item.channel,
                 title="[COLOR lightblue]%s[/COLOR]" % config.get_localized_string(30161),
                 url=item.url,
                 action="add_serie_to_library",
                 extra="episodios",
                 show=item.show))
   
    return itemlist

# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per filmpertutti.co
# ------------------------------------------------------------
import re

from channelselector import thumb
from core import scrapertoolsV2, servertools, httptools, tmdb, support
from core.item import Item
from platformcode import config, logger
from specials import autoplay

host = "https://www.filmpertutti.club"
headers = [['Referer', host]]
list_servers = ['verystream', 'openload', 'streamango', 'wstream', 'akvideo']
list_quality = ['HD', 'SD']


def mainlist(item):
    logger.info()

    itemlist =[]

    support.menu(itemlist, '[B]Film[/B]', 'peliculas', host + '/category/film/', 'movie')
    support.menu(itemlist, '[B] > Film per Genere[/B]', 'genre', host, 'tvshow')
    support.menu(itemlist, '[COLOR blue]Cerca Film...[/COLOR]', 'search', '')
    support.menu(itemlist, '[B]Serie TV[/B]', 'peliculas', host + '/category/serie-tv/', 'tvshow')
    support.menu(itemlist, '[B] > Serie TV in ordine alfabetico[/B]', 'az', host + '/category/serie-tv/', 'tvshow')
    support.menu(itemlist, '[COLOR blue]Cerca Serie TV...[/COLOR]', 'search', '', 'tvshow')


    autoplay.init(item.channel, list_servers, list_quality)
    autoplay.show_option(item.channel, itemlist)

    for item in itemlist:
        logger.info('MENU=' + str(item) )

    return itemlist


def newest(categoria):
    logger.info("filmpertutti newest" + categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "film":
            item.url = host + "/category/film/"
            item.action = "peliculas"
            item.extra = "movie"
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


def search(item, texto):
    logger.info("filmpertutti " + item.url + " search " + texto)
    item.url = host + "/?s=" + texto
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def genre(item):
    logger.info(item.channel + 'genre')
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    block = scrapertoolsV2.find_single_match(data, r'<ul class="table-list">(.*?)<\/ul>')
    matches = scrapertoolsV2.find_multiple_matches(block, r'<a href="([^"]+)">.*?<\/span>(.*?)<\/a>')
    for url, title in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action='peliculas',
                 title=title,
                 url=host+url)
        )
    itemlist = thumb(itemlist)
    return itemlist


def az(item):
    logger.info(item.channel + 'genre')
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    block = scrapertoolsV2.find_single_match(data, r'<select class="cats">(.*?)<\/select>')
    matches = scrapertoolsV2.find_multiple_matches(block, r'<option data-src="([^"]+)">(.*?)<\/option>')
    for url, title in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action='peliculas',
                 title=title,
                 url=url)
        )
    itemlist = thumb(itemlist)
    return itemlist


def peliculas(item):
    logger.info(item.channel + 'peliculas')
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    block = scrapertoolsV2.find_single_match(data, r'<ul class="posts">(.*)<\/ul>')

    patron = r'<li><a href="([^"]+)" data-thumbnail="([^"]+)">.*?<div class="title">([^<]+)<\/div>'    
    matches = scrapertoolsV2.find_multiple_matches(block, patron)

    for scrapedurl, scrapedthumb, scrapedtitle in matches:
        title = re.sub(r'.\(.*?\)|.\[.*?\]', '', scrapedtitle)
        quality = scrapertoolsV2.find_single_match(scrapedtitle, r'\[(.*?)\]')
        if not quality:
            quality = 'SD'
        
        longtitle = title + ' [COLOR blue][' + quality + '][/COLOR]'

        if item.contentType == 'tvshow':
            action = 'episodios'
        else:
            action ='findvideos'

        itemlist.append(
                Item(channel=item.channel,
                     action=action,
                     contentType=item.contentType,
                     title=longtitle,
                     fulltitle=title,
                     show=title,
                     quality=quality,
                     url=scrapedurl,
                     thumbnail=scrapedthumb
                     ))
    
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    next_page = scrapertoolsV2.find_single_match(data, '<a href="([^"]+)">Pagina')
    if next_page != "":
            itemlist.append(
                Item(channel=item.channel,
                     action="peliculas",
                     contentType=item.contentType,
                     title="[COLOR blue]" + config.get_localized_string(30992) + " >[/COLOR]",
                     url=next_page,
                     thumbnails=thumb()))

    return itemlist


def episodios(item):
    logger.info(item.channel + 'findvideos')
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    

    if 'accordion-item' in data:
        block = scrapertoolsV2.find_single_match(data, 'accordion-item.*?>(.*?)<div id="disqus_thread">')
        patron = r'<img src="([^"]+)">.*?<li class="season-no">(.*?)<\/li>(.*?)<\/table>'
        matches = scrapertoolsV2.find_multiple_matches(block, patron)

        for scrapedthumb, scrapedtitle, scrapedurl in matches:
            title = scrapedtitle + ' - ' + item.title
            if title[0] == 'x':
                title = '1' + title

            itemlist.append(
                    Item(channel=item.channel,
                         action='findvideos',
                         contentType='episode',
                         title=title,
                         fulltitle=title,
                         show=title,
                         quality=item.quality,
                         url=scrapedurl,
                         thumbnail=scrapedthumb
                        ))
        

    else:
        block = scrapertoolsV2.find_single_match(data, '<div id="info" class="pad">(.*?)<div id="disqus_thread">').replace('</p>','<br />').replace('×','x')
        matches = scrapertoolsV2.find_multiple_matches(block, r'<strong>(.*?)<\/strong>.*?<p>(.*?)<span')
        for lang, seasons in matches:
            lang = re.sub('.*?Stagione[^a-zA-Z]+', '', lang)
            # patron = r'([0-9]+x[0-9]+) (.*?)<br'
            season = scrapertoolsV2.find_multiple_matches(seasons, r'([0-9]+x[0-9]+) (.*?)<br')
            for title, url in season:
                title = title + ' - ' + lang
                itemlist.append(
                    Item(channel=item.channel,
                         title=title,
                         fulltitle=title,
                         show=title,
                         url=url,
                         contentType='episodie',
                         action='findvideos'
                    ))

    return itemlist


def findvideos(item):
    logger.info(item.channel + 'findvideos')

    if item.contentType == 'movie':
        data = httptools.downloadpage(item.url, headers=headers).data
    else:
        data = item.url
    
    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.title + ' - [COLOR limegreen][[/COLOR]' + videoitem.title + '[COLOR limegreen]][/COLOR]'
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.show = item.show
        videoitem.plot = item.plot
        videoitem.channel = item.channel
        videoitem.contentType = item.contentType
        videoitem.quality = item.quality

    autoplay.start(itemlist, item)

    if item.contentType != 'episode':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            itemlist.append(
                Item(channel=item.channel, title='[COLOR yellow][B]'+config.get_localized_string(30161)+'[/B][/COLOR]', url=item.url,
                     action="add_pelicula_to_library", extra="findvideos", contentTitle=item.fulltitle))

    return itemlist

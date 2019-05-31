# -*- coding: utf-8 -*-
# -*- Channel SleazeMovies -*-
# -*- Created for Alfa-addon -*-
# -*- By Sculkurt -*-

import re

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger

host = 'http://www.eroti.ga/'


def mainlist(item):
    logger.info()

    itemlist = list()
    itemlist.append(item.clone(title="Todas", action="list_all", url=host, thumbnail=get_thumb('all', auto=True)))
    itemlist.append(item.clone(title="Generos", action="genero", url=host, thumbnail=get_thumb('genres', auto=True)))
    itemlist.append(item.clone(title="Buscar", action="search", thumbnail=get_thumb('search', auto=True)))

    return itemlist

def genero(item):
    logger.info()
    itemlist = list()
    data = httptools.downloadpage(host).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<li class="cat-item.*?<a href="([^"]+)".*?>([^<]+)</a>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle in matches:
        
            itemlist.append(item.clone(action='list_all', title=scrapedtitle, url=scrapedurl))
    return itemlist


def list_all(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)  # Eliminamos tabuladores, dobles espacios saltos de linea, etc...

    patron = '<div class="featured-thumb"><a href="([^"]+)"><img.*?src="([^?]+).*?data-image-title="([^\(]+).*?\(([^\)]+)'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, img, scrapedtitle, year in matches:
        itemlist.append(Item(channel = item.channel,
                             title = scrapedtitle, 
                             url = scrapedurl, 
                             action = "findvideos",
                             thumbnail = img,
                             contentTitle = scrapedtitle,
                             contentType = "movie",
                             infoLabels = {'year': year}))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb = True)

    # Extrae la marca de siguiente página
    next_page = scrapertools.find_single_match(data, '<a class="next page-numbers" href="([^"]+)">Next</a></div>')
    if next_page != "":
	    itemlist.append(Item(channel=item.channel, action="list_all", title=">> Página siguiente", url=next_page, folder=True))
    return itemlist


    
def search(item, texto):
    logger.info()
    if texto != "":
        texto = texto.replace(" ", "+")
    item.url = host + "?s=" + texto
    item.extra = "busqueda"
    try:
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def findvideos(item): 
    logger.info() 

    itemlist = [] 

    data = httptools.downloadpage(item.url).data 
    logger.debug('codigo = ' + data) 

    itemlist.extend(servertools.find_video_items(data=data)) 

    for video in itemlist: 

        video.channel = item.channel
        video.contentTitle = item.contentTitle
		
    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(Item(channel = item.channel, 
                             title = '[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url = item.url,
                             action = "add_pelicula_to_library",
                             extra = "findvideos",
                             contentTitle = item.contentTitle,
                             thumbnail = item.thumbnail
                             ))

    return itemlist 

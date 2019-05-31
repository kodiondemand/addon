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

host = 'http://www.cat3plus.com/'

headers = [
    ['User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:38.0) Gecko/20100101 Firefox/38.0'],
    ['Accept-Encoding', 'gzip, deflate'],
    ['Referer', host]
]

def mainlist(item):
    logger.info()

    itemlist = list()
    itemlist.append(item.clone(title="Todas", action="list_all", url=host, thumbnail=get_thumb('all', auto=True)))
    itemlist.append(item.clone(title="Años", action="years", url=host, thumbnail=get_thumb('year', auto=True)))
    itemlist.append(item.clone(title="Buscar", action="search", thumbnail=get_thumb('search', auto=True)))

    return itemlist

def years(item):
    logger.info()
    itemlist = list()
    data = httptools.downloadpage(item.url, cookies=False).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = "<a dir='ltr' href='([^']+)'>([^<]+)</a>"
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle in matches:
        itemlist.append(item.clone(action='list_all', title=scrapedtitle, url=scrapedurl))
    return itemlist

def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    return data


def list_all(item):
    logger.info()
    itemlist = []
    data = get_source(item.url)

    patron = "<h2 class='post-title entry-title'><a href='([^']+)'>([^(]+).*?\(([^)]+).*?"
    patron += 'src="([^"]+).*?'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle, year, img in matches:
        itemlist.append(Item(channel = item.channel,
                             title = scrapedtitle, 
                             url = scrapedurl, 
                             action = "findvideos",
                             thumbnail = img,
                             contentTitle = scrapedtitle,
                             contentType = "movie",
                             infoLabels = {'year': year}))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb = True)

    # Extraer la marca de siguiente página
    next_page = scrapertools.find_single_match(data, "<a class='blog-pager-older-link' href='([^']+)'")
    if next_page != "":
	itemlist.append(Item(channel=item.channel, action="list_all", title=">> Página siguiente", url=next_page, folder=True))
	
    return itemlist


    
def search(item, texto):
    logger.info()
    if texto != "":
        texto = texto.replace(" ", "+")
    item.url = host + "search?q=" + texto
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
    
    patron = '<h2>\s*<a href="([^"]+)" target="_blank">.*?</a></h2>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for url in matches:
        data = httptools.downloadpage(url,	headers={'Referer': item.url}).data

        itemlist.extend(servertools.find_video_items(data=data)) 

    for video in itemlist: 

        video.channel = item.channel
        video.contentTitle = item.contentTitle
        video.title = video.server.capitalize()

	# Opción "Añadir esta pelicula a la videoteca"
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
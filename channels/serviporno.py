# -*- coding: utf-8 -*-

import re

import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger

host = "https://www.serviporno.com"

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, action="videos", title="Útimos videos",
                         url=host + "/ajax/homepage/?page=1", last= host))
    itemlist.append(Item(channel=item.channel, action="videos", title="Más vistos", 
                         url=host + "/ajax/most_viewed/?page=1", last= host + "/mas-vistos/"))
    itemlist.append(Item(channel=item.channel, action="videos", title="Más votados",
                         url=host + "/ajax/best_rated/?page=1", last= host + "/mas-votados/"))
    itemlist.append(Item(channel=item.channel, action="categorias", title="Canal",
                         url=host + "/ajax/list_producers/?page=1", last= host + "/sitios/"))
    itemlist.append(Item(channel=item.channel, action="categorias", title="Categorias", url= host + "/categorias/"))
    itemlist.append(Item(channel=item.channel, action="chicas", title="Chicas",
                         url=host + "/ajax/list_pornstars/?page=1", last= host + "/pornstars/"))
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar", last=""))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + '/ajax/new_search/?q=%s&page=1' % texto
    try:
        return videos(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def get_last_page(url):
    logger.info()
    data = httptools.downloadpage(url).data
    last_page= int(scrapertools.find_single_match(data,'data-ajax-last-page="(\d+)"'))
    return last_page


def videos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '(?s)<div class="wrap-box-escena">.*?'
    patron += '<div class="box-escena">.*?'
    patron += '<a\s*href="([^"]+)".*?'
    patron += 'data-stats-video-name="([^"]+)".*?'
    patron += '<img\s*src="([^"]+)".*?'
    patron += '<div class="duracion">([^"]+) min</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for url, title, thumbnail,duration in matches:
        title = "[COLOR yellow]" + duration + "[/COLOR] " + title
        url = urlparse.urljoin(item.url, url)
        itemlist.append(Item(channel=item.channel, action='play', title=title, url=url, thumbnail=thumbnail, fanart=thumbnail))
    # Paginador   "Página Siguiente >>"
    current_page = int(scrapertools.find_single_match(item.url, "/?page=(\d+)"))
    if not item.last_page:
        last_page = get_last_page(item.last)
    else:
        last_page = int(item.last_page)
    if current_page < last_page:
         next_page = "?page=" + str(current_page + 1)
         next_page = urlparse.urljoin(item.url,next_page)
         itemlist.append(Item(channel=item.channel, action="videos", title="Página Siguiente >>", text_color="blue",
                              url=next_page, thumbnail="", last_page=last_page))
    return itemlist


def chicas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div class="box-chica">.*?'
    patron += '<a href="([^"]+)" title="">.*?'
    patron += '<img class="img" src=\'([^"]+)\' width="175" height="150" border=\'0\' alt="[^"]+" />.*?'
    patron += '<h4><a href="[^"]+" title="">([^"]+)</a></h4>.*?'
    patron += '<a class="total-videos" href="[^"]+" title="">([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for url, thumbnail, title, videos in matches:
        last = urlparse.urljoin(item.url, url)
        url= last.replace("/pornstar", "/ajax/show_pornstar") + "?page=1"
        title = title + " (" + videos + ")"
        itemlist.append(Item(channel=item.channel, action='videos', title=title, url=url, last=last, thumbnail=thumbnail, fanart=thumbnail))
    # Paginador   "Página Siguiente >>"
    current_page = int(scrapertools.find_single_match(item.url, "/?page=(\d+)"))
    if not item.last_page:
        last_page = get_last_page(item.last)
    else:
        last_page = int(item.last_page)
    if current_page < last_page:
         next_page = "?page=" + str(current_page + 1)
         next_page = urlparse.urljoin(item.url,next_page)
         itemlist.append(Item(channel=item.channel, action="chicas", title="Página Siguiente >>", text_color="blue",
                              url=next_page, thumbnail="", last_page=last_page))
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div class="wrap-box-escena.*?'
    patron += 'href="([^"]+)"><img src="([^"]+)".*?'
    patron += '<h4.*?<a href="[^"]+">([^<]+)</a></h4>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for url, thumbnail, title in matches:
        last = urlparse.urljoin(item.url, url)
        url= last.replace("/videos-porno", "/ajax/show_category").replace("/sitio","/ajax/show_producer") + "?page=1"
        itemlist.append(Item(channel=item.channel, action='videos', title=title, url=url, last=last, thumbnail=thumbnail, plot=""))
    # Paginador   "Página Siguiente >>"
    current_page = int(scrapertools.find_single_match(item.url, "/?page=(\d+)"))
    if not item.last_page:
        last_page = get_last_page(item.last)
    else:
        last_page = int(item.last_page)
    if current_page < last_page:
         next_page = "?page=" + str(current_page + 1)
         next_page = urlparse.urljoin(item.url,next_page)
         itemlist.append(Item(channel=item.channel, action="categorias", title="Página Siguiente >>", text_color="blue",
                              url=next_page, thumbnail="", last_page=last_page))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(data, "sendCdnInfo.'([^']+)")
    itemlist.append(
        Item(channel=item.channel, action="play", server="directo", title=item.title, url=url, thumbnail=item.thumbnail,
             plot=item.plot, folder=False))
    return itemlist


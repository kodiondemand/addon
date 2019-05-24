# -*- coding: utf-8 -*-

import re

import urlparse

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import logger

host = 'http://sexgalaxy.net'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Peliculas", action="lista", url=host + "/full-movies/"))
    itemlist.append(Item(channel=item.channel, title="Videos", action="lista", url=host + "/new-releases/"))
    itemlist.append(Item(channel=item.channel, title="Canales", action="canales", url=host))
    itemlist.append(Item(channel=item.channel, title="Categorias", action="categorias", url=host))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/?s=%s" % texto
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def canales(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(host).data
    data = scrapertools.find_single_match(data, 'Top Networks</a>(.*?)</ul>')
    patron = '<li id=.*?<a href="(.*?)">(.*?)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = str(scrapedtitle)
        thumbnail = urlparse.urljoin(item.url, scrapedthumbnail)
        itemlist.append(Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                             thumbnail=scrapedthumbnail, plot=scrapedplot))
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, 'More Categories</a>(.*?)</ul>')
    patron = '<li id=.*?<a href="(.*?)">(.*?)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = str(scrapedtitle)
        thumbnail = urlparse.urljoin(item.url, scrapedthumbnail)
        itemlist.append(Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                             thumbnail=scrapedthumbnail, plot=scrapedplot))
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div class="post-img small-post-img">.*?<a href="(.*?)" title="(.*?)">.*?<img src="(.*?)"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        scrapedplot = ""
        calidad = scrapertools.find_single_match(scrapedtitle, '\(.*?/(\w+)\)')
        if calidad:
            scrapedtitle = "[COLOR red]" + calidad + "[/COLOR] " + scrapedtitle
        itemlist.append(Item(channel=item.channel, action="play", title=scrapedtitle, url=scrapedurl,
                             fanart=scrapedthumbnail, thumbnail=scrapedthumbnail, fulltitle=scrapedtitle, plot=scrapedplot))
    next_page = scrapertools.find_single_match(data, '<a class="next page-numbers" href="([^"]+)"')
    if next_page != "":
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page))
    return itemlist


def play(item):
    logger.info()
    data = httptools.downloadpage(item.url).data
    itemlist = servertools.find_video_items(data=data)
    for videoitem in itemlist:
        videoitem.title = item.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
    return itemlist

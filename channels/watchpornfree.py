# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re
import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger

# https://playpornfree.org/    https://mangoporn.net/   https://watchfreexxx.net/   https://losporn.org/  https://xxxstreams.me/  https://speedporn.net/

host = 'https://watchpornfree.ws'

def mainlist(item):
    logger.info("")
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Videos" , action="lista", url=host + "/category/clips-scenes"))
    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="lista", url=host + "/movies"))
    itemlist.append( Item(channel=item.channel, title="Parodia" , action="lista", url=host + "/category/parodies-hd"))
    itemlist.append( Item(channel=item.channel, title="Canal" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Año" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info("")
    texto = texto.replace(" ", "+")
    item.url = host + "/?s=%s" % texto
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info("")
    itemlist = []
    data = httptools.downloadpage(item.url).data
    if item.title == "Canal":
        data = scrapertools.find_single_match(data,'>Studios</a>(.*?)</ul>')
    if item.title == "Año":
        data = scrapertools.find_single_match(data,'>Years</a>(.*?)</ul>')
    if item.title == "Categorias":
        data = scrapertools.find_single_match(data,'>XXX Genres</div>(.*?)</ul>')
    patron  = '<a href="([^"]+)".*?>([^"]+)</a>(.*?)</li>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,cantidad  in matches:
        scrapedplot = ""
        scrapedtitle = scrapedtitle + cantidad
        scrapedthumbnail = ""
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist

def lista(item):
    logger.info("")
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<article class="TPost B">.*?<a href="([^"]+)">.*?src="([^"]+)".*?<div class="Title">([^"]+)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
        scrapedplot = ""
        itemlist.append( Item(channel=item.channel, action="findvideos", title=scrapedtitle, url=scrapedurl,
                              fanart=scrapedthumbnail, thumbnail=scrapedthumbnail, plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data,'<a class="next page-numbers" href="([^"]+)">Next &raquo;</a>')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


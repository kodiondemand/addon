# -*- coding: utf-8 -*-
#------------------------------------------------------------
import base64
import re

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import logger

host = 'http://www.pornhive.tv/en'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="lista", url=host))
    itemlist.append( Item(channel=item.channel, title="Canal" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search?keyword=%s" % texto
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    if item.title == "Categorias" :
        data = scrapertools.find_single_match(data,'Categories(.*?)Channels')
    else:
        data = scrapertools.find_single_match(data,'Channels(.*?)</ul>')
    patron  = '<li><a href="([^"]+)" title="[^"]+">(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<div class="col-lg-3 col-md-3 col-sm-4 col-xs-6 col-thumb panel-video-\d+">.*?'
    patron  += '<a href="([^"]+)".*?'
    patron  += 'data-src="([^"]+)".*?'
    patron  += 'alt="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
        title = scrapedtitle
        thumbnail = scrapedthumbnail
        plot = ""
        itemlist.append( Item(channel=item.channel, action="findvideos" , title=title, url=scrapedurl, thumbnail=thumbnail,
                              fanart=thumbnail, plot=plot, contentTitle=title))
    next_page = scrapertools.find_single_match(data,'<li><a href="([^"]+)" data-ci-pagination-page="\d+" rel="next">Next &rsaquo;')
    if next_page != "" :
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = ';extra_urls\[\d+\]=\'([^\']+)\''
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl in matches:
        scrapedurl = base64.b64decode(scrapedurl)
        itemlist.append(item.clone(action="play", title="%s", url=scrapedurl))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize()) 
    return itemlist



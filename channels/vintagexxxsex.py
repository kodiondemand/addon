# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re
import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger

host = 'http://www.vintagexxxsex.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Top" , action="lista", url=host + "/all-top/1/"))
    itemlist.append( Item(channel=item.channel, title="Novedades" , action="lista", url=host + "/all-new/1/"))
    itemlist.append( Item(channel=item.channel, title="Longitud" , action="lista", url=host + "/all-longest/1/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
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


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<li><a href="([^"]+)"><i class="fa fa-tag"></i>(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedurl = host + scrapedurl
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div class="th">.*?'
    patron += '<a href="([^"]+)".*?'
    patron += '<img src="([^"]+)".*?'
    patron += '<span class="th_nm">([^"]+)</span>.*?'
    patron += '<i class="fa fa-clock-o"></i>([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,time in matches:
        contentTitle = scrapedtitle
        title = "[COLOR yellow]" + time + " [/COLOR]" + scrapedtitle
        scrapedurl = scrapedurl.replace("/up.php?xxx=", "")
        scrapedurl = host + scrapedurl
        thumbnail = scrapedthumbnail
        plot = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=scrapedurl, thumbnail=thumbnail,
                              fanart=thumbnail, plot=plot, contentTitle=contentTitle))
    next_page = scrapertools.find_single_match(data,'<li><span class="pg_nm">\d+</span></li>.*?href="([^"]+)"')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist



def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    scrapedurl = scrapertools.find_single_match(data,'<iframe src="([^"]+)"')
    data = httptools.downloadpage(scrapedurl).data
    scrapedurl = scrapertools.find_single_match(data,'<source src="([^"]+)"')
    if scrapedurl == "":
        scrapedurl = "http:" + scrapertools.find_single_match(data,'<iframe src="([^"]+)"')
        data = httptools.downloadpage(scrapedurl).data
        scrapedurl = scrapertools.find_single_match(data,'file: "([^"]+)"')
    itemlist.append(Item(channel=item.channel, action="play", title=item.title, fulltitle=item.fulltitle, url=scrapedurl,
                    thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))
    return itemlist


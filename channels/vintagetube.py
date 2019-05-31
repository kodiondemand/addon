# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re
import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger

host = 'http://www.vintagetube.club'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Ultimos" , action="peliculas", url=host + "/tube/last-1/"))
    itemlist.append( Item(channel=item.channel, title="Popular" , action="peliculas", url=host + "/tube/popular-1/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/%s" % texto
    item.url =     item.url + "/popular-1/"
    try:
        return peliculas(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<div class="prev prev-ct">.*?'
    patron += '<a href="([^"]+)">.*?'
    patron += '<img src="([^"]+)".*?'
    patron += '<span class="prev-tit">([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
        scrapedplot = ""
        scrapedurl = host + scrapedurl
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail, fanart=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div class="prev">.*?'
    patron += '<a href="([^"]+)">.*?'
    patron += '<img src="([^"]+)">.*?'
    patron += '<span class="prev-tit">([^"]+)</span>.*?'
    patron += '<div class="prev-dur"><span>([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,scrapedtime in matches:
        scrapedplot = ""
        scrapedtitle = "[COLOR yellow]" + (scrapedtime) + "[/COLOR] " + str(scrapedtitle)
        scrapedurl = scrapedurl.replace("/xxx.php?tube=", "")
        scrapedurl = host + scrapedurl
        itemlist.append( Item(channel=item.channel, action="play", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail, fanart=scrapedthumbnail, plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data,'<span class="page">.*?<a target="_self" href="([^"]+)"')

    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="peliculas", title="Página Siguiente >>", text_color="blue", url=next_page) )
                
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    scrapedurl = scrapertools.find_single_match(data,'<iframe frameborder=0 scrolling="no"  src=\'(.*?)\'')
    if scrapedurl == "":
        scrapedurl = scrapertools.find_single_match(data,'<iframe src="([^"]+)"')
        data = httptools.downloadpage(scrapedurl).data
    else:
        data = httptools.downloadpage(scrapedurl).data
        scrapedurl = scrapertools.find_single_match(data,'<iframe src="([^"]+)"')
        data = httptools.downloadpage("https:" + scrapedurl).data
    scrapedurl = scrapertools.find_single_match(data,'<source src="([^"]+)"')
    itemlist = []
    itemlist.append(Item(channel=item.channel, action="play", title=item.title, fulltitle=item.title, url=scrapedurl,
                         thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))
    return itemlist
    

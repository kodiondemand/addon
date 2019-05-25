# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re
import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger

host = 'http://www.tryboobs.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="lista", url=host))
    itemlist.append( Item(channel=item.channel, title="Popular" , action="lista", url=host + "/most-popular/week/"))
    itemlist.append( Item(channel=item.channel, title="Mejor Valorado" , action="lista", url=host + "/top-rated/week/"))
    itemlist.append( Item(channel=item.channel, title="Modelos" , action="categorias", url=host + "/models/model-viewed/1/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/?q=%s" % texto
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
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<a href="([^"]+)" class="th-[^"]+">.*?'
    patron += 'src="([^"]+)".*?'
    patron += '<span>(\d+)</span>.*?'
    patron += '<span class="title">([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,cantidad,scrapedtitle in matches:
        scrapedplot = ""
        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              fanart=scrapedthumbnail, thumbnail=scrapedthumbnail, plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data,'<li><a class="pag-next" href="([^"]+)"><ins>Next</ins></a>')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="categorias", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = 'href="([^"]+)"\s*class="th-video.*?'
    patron += '<img src="([^"]+)".*?'
    patron += '<span class="time">([^"]+)</span>.*?'
    patron += '<span class="title">([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,duracion,scrapedtitle  in matches:
        url = scrapedurl
        contentTitle = scrapedtitle
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        thumbnail = scrapedthumbnail
        plot = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title, url=url, thumbnail=thumbnail,
                              fanart=thumbnail, plot=plot, contentTitle = contentTitle))
    next_page = scrapertools.find_single_match(data,'<li><a class="pag-next" href="([^"]+)"><ins>Next</ins></a>')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<video src="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url  in matches:
        itemlist.append(Item(channel=item.channel, action="play", title=item.title, fulltitle=item.fulltitle, url=url,
                         thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))
    return itemlist


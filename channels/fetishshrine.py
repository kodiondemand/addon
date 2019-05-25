# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re
import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger

host = 'https://www.fetishshrine.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="lista", url=host + "/latest-updates/"))
    itemlist.append( Item(channel=item.channel, title="Popular" , action="lista", url=host + "/most-popular/"))
    itemlist.append( Item(channel=item.channel, title="Mejor Valorado" , action="lista", url=host + "/top-rated/"))
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
    patron = '<a href="([^"]+)" title="([^"]+)">.*?'
    patron += '<img src="([^"]+)".*?'
    patron += '<span class="vids">(\d+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,cantidad in matches:
        scrapedplot = ""
        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              fanart=scrapedthumbnail, thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<a href="([^"]+)" itemprop="url">.*?'
    patron += '<img src="([^"]+)" alt="([^"]+)">.*?'
    patron += '<span itemprop="duration" class="length">(.*?)</span>(.*?)<span class="thumb-info">'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,duracion,calidad  in matches:
        url = scrapedurl
        if ">HD<" in calidad:
            title = "[COLOR yellow]" + duracion + "[/COLOR] " + "[COLOR red]" + "HD" + "[/COLOR] " +scrapedtitle
        else:
            title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        contentTitle = scrapedtitle
        thumbnail = scrapedthumbnail
        plot = ""
        itemlist.append( Item(channel=item.channel, action="play", title=title, url=url, thumbnail=thumbnail,
                               plot=plot, fanart=scrapedthumbnail, contentTitle = contentTitle ))
    next_page = scrapertools.find_single_match(data,'<li><a data=\'\d+\' href="([^"]+)" title="Next">')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista" , title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = 'video_url: \'([^\']+)\''
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl  in matches:
        itemlist.append(Item(channel=item.channel, action="play", title=item.title, url=scrapedurl,
                            thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))
    return itemlist


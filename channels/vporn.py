# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re
import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger

host = 'https://www.vporn.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Novedades" , action="lista", url=host + "/newest/month/"))
    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="lista", url=host + "/views/month/"))
    itemlist.append( Item(channel=item.channel, title="Mejor Valoradas" , action="lista", url=host + "/rating/month/"))
    itemlist.append( Item(channel=item.channel, title="Favoritas" , action="lista", url=host + "/favorites/month/"))
    itemlist.append( Item(channel=item.channel, title="Mas Votada" , action="lista", url=host + "/votes/month/"))
    itemlist.append( Item(channel=item.channel, title="Longitud" , action="lista", url=host + "/longest/month/"))
    itemlist.append( Item(channel=item.channel, title="PornStar" , action="catalogo", url=host + "/pornstars/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search?q=%s" % texto
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def catalogo(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<div class=\'star\'>.*?'
    patron += '<a href="([^"]+)">.*?'
    patron += '<img src="([^"]+)" alt="([^"]+)".*?'
    patron += '<span> (\d+) Videos'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,cantidad in matches:
        scrapedplot = ""
        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
        scrapedurl = host + scrapedurl
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              fanart=scrapedthumbnail, thumbnail=scrapedthumbnail, plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data,'<a class="next" href="([^"]+)">')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="catalogo", title="Next page >>", text_color="blue", url=next_page) )
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    data = scrapertools.find_single_match(data,'<div class="cats-all categories-list">(.*?)</div>')
    patron  = '<a href="([^"]+)".*?>([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
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
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<div class="video">.*?'
    patron += '<a href="([^"]+)".*?'
    patron += '<span class="time">(.*?)</span>(.*?)</span>.*?'
    patron += '<img src="([^"]+)" alt="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,time,calidad,scrapedthumbnail,scrapedtitle in matches:
        scrapedtitle = scrapedtitle.replace("&comma; ", " & ").replace("&lpar;", "(").replace("&rpar;", ")") 
        title = "[COLOR yellow]" + time + "  [/COLOR]" + scrapedtitle
        if "hd-marker is-hd" in  calidad:
            title = "[COLOR yellow]" + time + " [/COLOR]" + "[COLOR red]" + "HD" + "  [/COLOR]" + scrapedtitle
        thumbnail = scrapedthumbnail
        plot = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=scrapedurl,
                              fanart=thumbnail, thumbnail=thumbnail, plot=plot, contentTitle = title))
    next_page = scrapertools.find_single_match(data,'<a class="next.*?title="Next Page" href="([^"]+)">')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="Next page >>", text_color="blue", url=next_page) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<source src="([^"]+)" type="video/mp4" label="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl,scrapedtitle  in matches:
        itemlist.append(item.clone(action="play", title=scrapedtitle, fulltitle = item.title, url=scrapedurl))
    return itemlist


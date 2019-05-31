# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re
import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger

host = 'https://www.youporn.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevas", action="lista", url=host + "/browse/time/"))
    itemlist.append( Item(channel=item.channel, title="Mas Vistas", action="lista", url=host + "/browse/views/"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorada", action="lista", url=host + "/top_rated/"))
    itemlist.append( Item(channel=item.channel, title="Canal", action="categorias", url=host + "/channels/most_popular/"))
    itemlist.append( Item(channel=item.channel, title="Pornstars", action="catalogo", url=host + "/pornstars/most_popular/"))
    itemlist.append( Item(channel=item.channel, title="Categorias", action="categorias", url=host + "/categories/alphabetical/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/?query=%s" % texto
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
    data1 = scrapertools.find_single_match(data,'>Most Popular Pornstars<(.*?)<i class=\'icon-menu-right\'></i></a>')
    patron = '<a href="([^"]+)".*?'
    patron += 'data-original="([^"]+)".*?'
    patron += '<span class="porn-star-name">([^"]+)</span>.*?'
    patron += '<span class="video-count">([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data1)
    for scrapedurl,scrapedthumbnail,scrapedtitle,cantidad in matches:
        scrapedplot = ""
        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              fanart=scrapedthumbnail, thumbnail=scrapedthumbnail, plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data,'<div class="currentPage".*?<a href="([^"]+)"')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="catalogo", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    if item.title == "Canal":
        data = scrapertools.find_single_match(data,'>All</div>(.*?)<i class=\'icon-menu-right\'></i></a>')
    if item.title == "Categorias":
        data = scrapertools.find_single_match(data,'<div class=\'row alphabetical\'.*?>(.*?)>Popular by Country</h2>')
    patron = '<a href="([^"]+)".*?'
    patron += '<img src=(.*?)>.*?'
    patron += '>([^<]+) (?:Videos|videos)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,cantidad in matches:
        scrapedplot = ""
        thumbnail = scrapertools.find_single_match(scrapedthumbnail,'data-original="([^"]+)"') 
        scrapedtitle = scrapertools.find_single_match(scrapedthumbnail,'alt="([^"]+)"')
        if scrapedtitle == "" :
            scrapedtitle = scrapertools.find_single_match(scrapedthumbnail,'alt=\'([^\']+)\'')
        title = scrapedtitle + " (" + cantidad +")"
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append( Item(channel=item.channel, action="lista", title=title, url=scrapedurl,
                              fanart=thumbnail, thumbnail=thumbnail, plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data,'<div class="currentPage".*?<a href="([^"]+)"')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="categorias", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<a href="([^"]+)" class=\'video-box-image\'.*?'
    patron += 'data-original="([^"]+)".*?'
    patron += '<div class="video-box-title">([^"]+)</div>.*?'
    patron += '<div class="video-duration">(.*?)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,duracion  in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        contentTitle = title
        thumbnail = scrapedthumbnail
        plot = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail,
                              fanart=thumbnail, plot=plot, contentTitle = contentTitle))
    next_page = scrapertools.find_single_match(data,'<link rel="next" href="([^"]+)"')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = 'page_params.video.mediaDefinition =.*?"videoUrl":"([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl  in matches:
        scrapedurl =  scrapedurl.replace("\/", "/")
    itemlist.append(item.clone(action="play", title=scrapedurl, fulltitle = item.title, url=scrapedurl))
    return itemlist



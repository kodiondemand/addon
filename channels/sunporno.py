# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re
import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger

host = 'https://www.sunporno.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="lista", url=host +"/most-recent/"))
    itemlist.append( Item(channel=item.channel, title="Popular" , action="lista", url=host + "/most-viewed/date-last-week/"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="lista", url=host + "/top-rated/date-last-week/"))
    itemlist.append( Item(channel=item.channel, title="Mas largas" , action="lista", url=host + "/long-movies/date-last-month/"))
    itemlist.append( Item(channel=item.channel, title="PornStars" , action="catalogo", url=host + "/pornstars/most-viewed/1/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/channels"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/%s/" % texto
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
    patron = '<div class="thumb-container with-title moviec">.*?'
    patron += '<a href="([^"]+)".*?'
    patron += 'src="([^"]+)".*?'
    patron += '<a title="([^"]+)".*?'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
        scrapedplot = ""
        scrapedurl = scrapedurl + "/most-recent/"
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              fanart=scrapedthumbnail, thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def catalogo(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<div class="starec">.*?'
    patron += '<a href="([^"]+)".*?'
    patron += '<img class="thumb" src="([^"]+)"  alt="([^"]+)".*?'
    patron += '<p class="videos">(\d+)</p>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl, scrapedthumbnail, scrapedtitle, cantidad in matches:
        scrapedplot = ""
        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              fanart=scrapedthumbnail, thumbnail=scrapedthumbnail, plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data,'<li><a class="pag-next" href="(.*?)">Next &gt;</a>')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append( Item(channel=item.channel , action="catalogo", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist    


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    data = scrapertools.find_single_match(data,'class="thumbs-container">(.*?)<div class="clearfix">')
    patron  = '<p class="btime">([^"]+)</p>.*?'
    patron += '>(.*?)<img width=.*?'
    patron += '="([^"]+)" class="thumb.*?'
    patron += 'title="([^"]+)".*?'
    patron += 'href="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for duracion,calidad,scrapedthumbnail,scrapedtitle,scrapedurl in matches:
        url = scrapedurl
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        if ">HD<" in calidad:
            title = "[COLOR yellow]" + duracion + "[/COLOR] " + "[COLOR red]" + "HD" + "[/COLOR] " + scrapedtitle
        thumbnail = scrapedthumbnail
        plot = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail,
                              fanart=scrapedthumbnail, plot=plot, contentTitle = scrapedtitle))
    next_page = scrapertools.find_single_match(data,'<li><a class="pag-next" href="(.*?)">Next &gt;</a>')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append( Item(channel=item.channel , action="lista", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<video src="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl  in matches:
        scrapedurl = scrapedurl.replace("https:", "http:")
        itemlist.append(Item(channel=item.channel, action="play", title=item.title, url=scrapedurl,
                            thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))
    return itemlist


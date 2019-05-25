# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re
import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger

host = 'https://www.pornburst.xxx'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="lista", url=host + "/page3.html"))
    itemlist.append( Item(channel=item.channel, title="Pornstars" , action="categorias", url=host + "/pornstars/"))
    itemlist.append( Item(channel=item.channel, title="Canal" , action="categorias", url=host + "/sites/"))
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
    if "/sites/" in item.url:
        patron = '<div class="muestra-escena muestra-canales">.*?'
        patron += 'href="([^"]+)">.*?'
        patron += 'src="([^"]+)".*?'
        patron += '<a title="([^"]+)".*?'
        patron += '</span> (\d+) videos</span>'
    if "/pornstars/" in item.url:
        patron = '<a class="muestra-escena muestra-pornostar" href="([^"]+)">.*?'
        patron += 'src="([^"]+)".*?'
        patron += 'alt="([^"]+)".*?'
        patron += '</span> (\d+) videos</span>'
    else:
        patron  = '<a class="muestra-escena muestra-categoria" href="([^"]+)" title="[^"]+">.*?'
        patron += 'src="([^"]+)".*?'
        patron += '</span> ([^"]+) </h2>(.*?)>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,cantidad in matches:
        scrapedplot = ""
        cantidad =  " (" + cantidad + ")"
        if "</a" in cantidad:
            cantidad = ""
        scrapedtitle = scrapedtitle +  cantidad
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              fanart=scrapedthumbnail, thumbnail=scrapedthumbnail , plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data,'<link rel="next" href="([^"]+)"')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="categorias", title="Página Siguiente >>", text_color="blue", url=next_page) )

    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<a class="muestra-escena"\s*href="([^"]+)".*?'
    patron += 'data-stats-video-name="([^"]+)".*?'
    patron += '<img src="([^"]+)".*?'
    patron += '<span class="ico-minutos sprite" title="Length"></span>([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,duracion  in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        contentTitle = title
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play", title=title, url=url, thumbnail=thumbnail,
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
    patron  = '<source src="([^"]+)" type="video/mp4"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl  in matches:
        title = scrapedurl
    itemlist.append(item.clone(action="play", title=title, fulltitle = item.title, url=scrapedurl))
    return itemlist


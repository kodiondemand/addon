# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re
import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger

host = 'http://www.perfectgirls.net'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Ultimos" , action="peliculas", url=host))
    itemlist.append( Item(channel=item.channel, title="Top" , action="peliculas", url=host + "/top/3days/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/%s/" % texto
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
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<li class="additional_list__item"><a href="([^"]+)">([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        url = urlparse.urljoin(item.url,scrapedurl) + "/1"
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle, url=url,
                               thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<div class="list__item_link"><a href="([^"]+)" title="([^"]+)">.*?'
    patron  += 'data-original="([^"]+)".*?'
    patron  += '<time>(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedtitle,scrapedthumbnail,duracion in matches:
        plot = ""
        time = scrapertools.find_single_match(duracion, '([^"]+)</time>')
        if not 'HD' in duracion :
            title = "[COLOR yellow]" + time + "[/COLOR] " + scrapedtitle
        else:
            title = "[COLOR yellow]" + time + "[/COLOR] " + "[COLOR red]" + "HD" + "[/COLOR]  " + scrapedtitle
        scrapedthumbnail = "http:" + scrapedthumbnail
        url = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append( Item(channel=item.channel, action="play", title=title, url=url, thumbnail=scrapedthumbnail,
                              fanart=scrapedthumbnail, plot=plot, contentTitle = title))
    next_page = scrapertools.find_single_match(data, '<a class="btn_wrapper__btn" href="([^"]+)">Next</a></li>')
    if next_page:
        next_page = urlparse.urljoin(item.url, next_page)
        itemlist.append(item.clone(action="peliculas", title="Página Siguiente >>", text_color="blue", url=next_page ))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<source src="([^"]+)" res="\d+" label="([^"]+)" type="video/mp4" default/>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle  in matches:
        itemlist.append(item.clone(action="play", title=scrapedtitle, url=scrapedurl))
    return itemlist


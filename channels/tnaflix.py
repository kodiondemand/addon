# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re
import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger

host = 'https://www.tnaflix.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host + "/new/?d=all&period=all"))
    itemlist.append( Item(channel=item.channel, title="Popular" , action="peliculas", url=host + "/popular/?d=all&period=all"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorado" , action="peliculas", url=host + "/toprated/?d=all&period=month"))
    itemlist.append( Item(channel=item.channel, title="Canal" , action="catalogo", url=host + "/channels/all/top-rated/1/all"))
    itemlist.append( Item(channel=item.channel, title="PornStars" , action="categorias", url=host + "/pornstars"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search.php?what=%s&tab=" % texto
    try:
        return peliculas(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def catalogo(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<div class="vidcountSp">(\d+)</div>.*?<a class="categoryTitle channelTitle" href="([^"]+)" title="([^"]+)">.*?data-original="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for cantidad,scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        title = scrapedtitle + " (" + cantidad + ")"
        scrapedplot = ""
        itemlist.append( Item(channel=item.channel, action="peliculas", title=title , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    next_page_url = scrapertools.find_single_match(data,'<a class="llNav" href="([^"]+)">')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="catalogo" , title="Página Siguiente >>" , text_color="blue", url=next_page_url , folder=True) )
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    if item.title=="PornStars" :
        data = scrapertools.find_single_match(data,'</i> Hall Of Fame Pornstars</h1>(.*?)</section>')
    patron  = '<a class="thumb" href="([^"]+)">.*?<img src="([^"]+)".*?<div class="vidcountSp">(.*?)</div>.*?<a class="categoryTitle".*?>([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,cantidad,scrapedtitle in matches:
        scrapedplot = ""
        if item.title=="Categorias" :
            scrapedthumbnail = "http:" + scrapedthumbnail
            scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        if item.title=="PornStars" :
            scrapedurl = urlparse.urljoin(item.url,scrapedurl) + "?section=videos"
        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    next_page_url = scrapertools.find_single_match(data,'<a class="llNav" href="([^"]+)">')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="categorias" , title="Página Siguiente >>" , text_color="blue", url=next_page_url , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<a class=\'thumb no_ajax\' href=\'(.*?)\'.*?'
    patron += 'data-original=\'(.*?)\' alt="([^"]+)"><div class=\'videoDuration\'>([^<]+)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,duracion  in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        contentTitle = title
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))
    next_page_url = scrapertools.find_single_match(data,'<a class="llNav" href="([^"]+)">')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Página Siguiente >>" , text_color="blue", url=next_page_url , folder=True) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<meta itemprop="contentUrl" content="([^"]+)" />'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url  in matches:
        itemlist.append(Item(channel=item.channel, action="play", title=item.title, fulltitle=item.fulltitle, url=url,
                         thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))
    return itemlist


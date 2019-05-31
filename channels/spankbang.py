# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re
import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger

host = 'https://es.spankbang.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevos", action="lista", url= host + "/new_videos/"))
    itemlist.append( Item(channel=item.channel, title="Mas valorados", action="lista", url=host + "/trending_videos/"))
    itemlist.append( Item(channel=item.channel, title="Mas vistos", action="lista", url= host + "/most_popular/"))
    itemlist.append( Item(channel=item.channel, title="Mas largos", action="lista", url= host + "/longest_videos/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/s/%s" % texto
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
    patron  = '<a href="([^"]+)/?order=trending"><img src="([^"]+)"><span>([^"]+)</span></a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
        scrapedplot = ""
        scrapedurl =  urlparse.urljoin(item.url,scrapedurl)
        scrapedthumbnail =  urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle , url=scrapedurl , 
                              thumbnail=scrapedthumbnail, fanart=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div class="video-item" data-id="\d+">.*?'
    patron += '<a href="([^"]+)" class="thumb ">.*?'
    patron += 'data-src="([^"]+)" alt="([^"]+)".*?'
    patron += '</span>(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,scrapedtime in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        scrapedhd = scrapertools.find_single_match(scrapedtime, '<span class="i-hd">(.*?)</span>')
        duration = scrapertools.find_single_match(scrapedtime, '<i class="fa fa-clock-o"></i>(.*?)</span>')
        if scrapedhd != '':
            title = "[COLOR yellow]" + duration + " min[/COLOR] " + "[COLOR red]" +scrapedhd+ "[/COLOR]  "+scrapedtitle
        else:
            title = "[COLOR yellow]" + duration + " min[/COLOR] " + scrapedtitle
        thumbnail = "http:" + scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail, 
                              fanart=thumbnail, plot=plot, contentTitle=title) )
    next_page = scrapertools.find_single_match(data, '<li class="next"><a href="([^"]+)">')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append( Item(channel=item.channel, action="lista", title="Página Siguiente >>" , text_color="blue",
                              url=next_page ) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    scrapedurl = scrapertools.find_single_match(data, 'var stream_url_1080p  = \'([^\']+)\';')
    if scrapedurl == "":
        scrapedurl = scrapertools.find_single_match(data, 'var stream_url_720p  = \'([^\']+)\';')
    if scrapedurl == "":
        scrapedurl = scrapertools.find_single_match(data, 'var stream_url_480p  = \'([^\']+)\';')
    scrapedurl = scrapedurl.replace("amp;", "")
    itemlist.append(Item(channel=item.channel, action="play", title=item.title, url=scrapedurl, thumbnail=item.thumbnail,
                         plot=item.plot, show=item.title, server="directo"))
    return itemlist


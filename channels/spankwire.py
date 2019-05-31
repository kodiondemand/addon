# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re
import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger

host = 'https://www.spankwire.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="lista", url=host + "/recentvideos/straight"))
    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="lista", url=host + "/home1/Straight/Month/Views"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="lista", url=host + "/home1/Straight/Month/Rating"))
    itemlist.append( Item(channel=item.channel, title="Longitud" , action="lista", url=host + "/home1/Straight/Month/Duration"))
    #itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories/Straight"))
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
    patron  = '<div class="category-thumb"><a href="([^"]+)".*?'
    patron += '<img src="([^"]+)" alt="([^"]+)" />.*?'
    patron += '<span>([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedthumbnail,scrapedtitle,cantidad in matches:
        scrapedplot = ""
        scrapedthumbnail = "http:" + scrapedthumbnail
        scrapedtitle = scrapedtitle + " (" + cantidad +")"
        scrapedurl = urlparse.urljoin(item.url,scrapedurl) + "/Submitted/59"
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              fanart=scrapedthumbnail, thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<div class="video_thumb_wrapper">.*?'
    patron += '<a href="([^"]+)".*?data-original="([^"]+)".*?'
    patron += 'title="([^"]+)".*?'
    patron += '<div class="video_thumb_wrapper__thumb_info video_thumb_wrapper__duration">(.*?)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,duracion  in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        contentTitle = title
        thumbnail = scrapedthumbnail
        plot = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail,
                              fanart=thumbnail, plot=plot, contentTitle = contentTitle))
    next_page = scrapertools.find_single_match(data,'<link rel="next" href="([^"]+)" />')
    #Para el buscador
    if next_page=="":
        next_page = scrapertools.find_single_match(data,'<div class="paginator_wrapper__buttons"><a class="" href="([^"]+)"')
        next_page = urlparse.urljoin(item.url,next_page)
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append( Item(channel=item.channel , action="lista" , title="Página Siguiente >>" , text_color="blue", url=next_page) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data,'Copy Embed Code(.*?)For Desktop')
    patron  = '<div class="shareDownload_container__item__dropdown">.*?<a href="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl  in matches:
        url = scrapedurl
        if url=="#":
            scrapedurl = scrapertools.find_single_match(data,'playerData.cdnPath480         = \'([^\']+)\'')
        itemlist.append(item.clone(action="play", title=scrapedurl, fulltitle = scrapedurl, url=scrapedurl))

    return itemlist


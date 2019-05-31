# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re
import urlparse

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import logger

host = 'http://hd.xtapes.to'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="lista", url=host + "/full-porn-movies/?display=tube&filtre=date"))
    itemlist.append( Item(channel=item.channel, title="Productora" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Nuevos" , action="lista", url=host + "/?filtre=date&cat=0"))
    itemlist.append( Item(channel=item.channel, title="Mas Vistos" , action="lista", url=host + "/?display=tube&filtre=views"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorado" , action="lista", url=host + "/?display=tube&filtre=rate"))
    itemlist.append( Item(channel=item.channel, title="Longitud" , action="lista", url=host + "/?display=tube&filtre=duree"))
    itemlist.append( Item(channel=item.channel, title="Canal" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/?s=%s" % texto
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
    if item.title=="Canal":
        data = scrapertools.find_single_match(data,'<div class="footer-banner">(.*?)<div id="footer-copyright">')
    if item.title=="Productora" :
       data = scrapertools.find_single_match(data,'<li id="menu-item-16"(.*?)</ul>')
    if item.title=="Categorias" :
       data = scrapertools.find_single_match(data,'<a>Categories</a>(.*?)</ul>')
    patron  = '<a href="([^"]+)">([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = scrapedtitle
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<li class="border-radius-5 box-shadow">.*?'
    patron += 'src="([^"]+)".*?<a href="([^"]+)" title="([^"]+)">.*?'
    patron += '<div class="time-infos".*?>([^"]+)<span class="time-img">'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedthumbnail,scrapedurl,scrapedtitle,duracion  in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        title = scrapedtitle
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        contentTitle = title
        thumbnail = scrapedthumbnail
        plot = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail,
                              fanart=thumbnail, plot=plot, fulltitle = title,  contentTitle = contentTitle))
    next_page = scrapertools.find_single_match(data,'<a class="next page-numbers" href="([^"]+)">Next video')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        next_page = next_page.replace("#038;cat=0#038;", "")
        next_page = next_page.replace("#038;filtre=views#038;", "").replace("&#038;filtre=rate#038;", "&").replace("#038;filtre=duree#038;", "")
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    variable = scrapertools.find_single_match(data,'<script type=\'text/javascript\'> str=\'([^\']+)\'')
    resuelta = re.sub("@[A-F0-9][A-F0-9]", lambda m: m.group()[1:].decode('hex'), variable)
    url = scrapertools.find_single_match(resuelta,'<iframe src="([^"]+)"')
    data = httptools.downloadpage(item.url).data
    itemlist = servertools.find_video_items(data=data)
    for videoitem in itemlist:
        videoitem.title = item.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
    return itemlist


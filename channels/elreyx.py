# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re
import urlparse

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import logger

host = 'http://www.elreyx.com'


def mainlist(item):
    logger.info()
    itemlist = []
    
    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="lista", url=host + "/peliculasporno.html") )
    itemlist.append( Item(channel=item.channel, title="Escenas" , action="lista", url=host + "/index.html"))
    itemlist.append( Item(channel=item.channel, title="Productora" , action="categorias", url=host + "/index.html") )
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/peliculasporno.html") )
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search") )
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search-%s" % texto + ".html"
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
    if item.title == "Categorias" :
        patron  = '<td><a href="([^<]+)" title="Movies ([^<]+)">.*?</a>'
    else:
        patron  = '<a href="([^<]+)" title="View Category ([^<]+)">.*?</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        url="https:" + scrapedurl
        scrapedthumbnail = ""
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=url,
                              thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    if not "/peliculasporno" in item.url:
        patron  = '<div class="notice_image">.*?<a title="([^"]+)" href="([^"]+)">.*?<img src="(.*?)">'
    else:
        patron  = '<div class="captura"><a title="([^"]+)" href="([^"]+)".*?><img src="(.*?)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedtitle,scrapedurl,scrapedthumbnail in matches:
        scrapedplot = ""
        url="https:" + scrapedurl
        thumbnail="https:" + scrapedthumbnail
        itemlist.append( Item(channel=item.channel, action="play", title=scrapedtitle, url=url, thumbnail=thumbnail,
                              fanart=thumbnail, plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data,'<li class="float-xs-right"><a href=\'([^\']+)\' title=\'Pagina \d+\'>')
    if next_page == "":
        next_page = scrapertools.find_single_match(data,'<li><a href=\'([^\']+)\' title=\'Pagina \d+\'>&raquo;</a>')
    if next_page!= "":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


def play(item):
    logger.info()
    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(data, '<IFRAME SRC="(.*?)"')
    if url == "":
        url = scrapertools.find_single_match(data,'<iframe src="(.*?)"')
    data = httptools.downloadpage(url).data
    itemlist = servertools.find_video_items(data=data)
    for videoitem in itemlist:
        videoitem.title = item.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
    return itemlist


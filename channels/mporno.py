# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re
import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger

host = 'http://mporno.tv'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Novedades" , action="peliculas", url=host + "/most-recent/"))
    itemlist.append( Item(channel=item.channel, title="Mejor valoradas" , action="peliculas", url=host + "/top-rated/"))
    itemlist.append( Item(channel=item.channel, title="Mas vistas" , action="peliculas", url=host + "/most-viewed/"))
    itemlist.append( Item(channel=item.channel, title="Longitud" , action="peliculas", url=host + "/longest/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/channels/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/videos/%s/page1.html" % texto
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
    patron  = '<h3><a href="([^"]+)">(.*?)</a> <small>(.*?)</small></h3>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,cantidad in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = scrapedtitle + "  " + cantidad
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail , plot=scrapedplot) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<img class="content_image" src="([^"]+).mp4/.*?" alt="([^"]+)".*?this.src="(.*?)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        contentTitle = scrapedtitle
        title = scrapedtitle
        scrapedurl = scrapedurl.replace("/thumbs/", "/videos/") + ".mp4"
        thumbnail = scrapedthumbnail
        plot = ""
        itemlist.append( Item(channel=item.channel, action="play", title=title, url=scrapedurl, thumbnail=thumbnail,
                              fanart=thumbnail, plot=plot, contentTitle=contentTitle))
    next_page_url = scrapertools.find_single_match(data,'<a href=\'([^\']+)\' class="next">Next &gt;&gt;</a>')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append(item.clone(action="peliculas", title="Página Siguiente >>", text_color="blue", url=next_page_url) )
        
    return itemlist


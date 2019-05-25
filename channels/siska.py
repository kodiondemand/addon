# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re
import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger

host = 'http://www.siska.tv/'


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Nuevos" , action="lista", url=host + "newVideo.php?language=en"))
    itemlist.append( Item(channel=item.channel, title="Mas vistos" , action="lista", url=host + "MostViewed.php?views=month&language=en"))
    itemlist.append( Item(channel=item.channel, title="Canal" , action="categorias", url=host + "Channel.php?language=en"))

    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "index.php?category=1&language=en"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "search.php?q=%s&language=en&search=Search" % texto
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
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    data = scrapertools.find_single_match(data,'<div id="content">(.*?)<div class="maincat">')
    patron = '<a href="(.*?)".*?'
    patron += '<img src="(.*?)".*?alt="(.*?)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
        scrapedplot = ""
        scrapedtitle = scrapedtitle.replace("Watch Channel ", "")
        url = urlparse.urljoin(item.url,scrapedurl)
        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=url,
                              thumbnail=thumbnail , plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    if "catID=" in item.url:
        patron = '<li><h3><a href="([^"]+)">.*?'
        patron += '<img src="([^"]+)" class="imgt" alt="([^"]+)".*?'
        patron += '<div class="time">(.*?)</div>'
    else:
        patron = '<li><h3><a href=\'([^\']+)\'>.*?'
        patron += '<img src=\'([^\']+)\' class=\'imgt\' alt=\'(.*?)\'.*?'
        patron += '<div class=\'time\'>(.*?)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,scrapedtime in matches:
        scrapedtime = scrapedtime.replace("Duration: ", "").replace(" : ", ":")
        url = urlparse.urljoin(item.url,scrapedurl)
        title = "[COLOR yellow]" + scrapedtime + "[/COLOR] " + scrapedtitle
        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        plot = ""
        itemlist.append( Item(channel=item.channel, action="findvideos", title=title, url=url, thumbnail=thumbnail, plot=plot,
                              contentTitle = scrapedtitle))
    next_page = scrapertools.find_single_match(data, '<a href="([^"]+)"><span>Next')
    if next_page == "":
        next_page = scrapertools.find_single_match(data, '<a href=\'([^\']+)\' title=\'Next Page\'>')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append( Item(channel=item.channel, action="lista", title="Página Siguiente >>", text_color="blue", 
                              url=next_page) )
    return itemlist


# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re
import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger

host = 'https://tubedupe.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevos" , action="lista", url=host + "/latest-updates/"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorados" , action="lista", url=host + "/top-rated/"))
    itemlist.append( Item(channel=item.channel, title="Mas vistos" , action="lista", url=host + "/most-popular/"))
    itemlist.append( Item(channel=item.channel, title="Modelos" , action="categorias", url=host + "/models/?sort_by=model_viewed"))
    itemlist.append( Item(channel=item.channel, title="Canal" , action="categorias", url=host + "/channels/?sort_by=cs_viewed"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories/?sort_by=avg_videos_popularity"))
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
    patron = '<div class="block-[^"]+">.*?'
    patron += '<a href="([^"]+)".*?title="([^"]+)".*?'
    patron += 'src="([^"]+)".*?'
    if '/models/' in item.url:
        patron += '<span class="strong">Videos</span>(.*?)</div>'
    else:
        patron += '<var class="duree">([^"]+) </var>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedtitle,scrapedthumbnail,cantidad  in matches:
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        cantidad = cantidad.strip()
        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
        scrapedplot = ""
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail,fanart=scrapedthumbnail, plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data, '<li class="active">.*?<a href="([^"]+)" title="Page')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="categorias", title="Página Siguiente >>", text_color="blue", url=next_page ) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div class="block-video">.*?'
    patron += '<a href="([^"]+)" class="[^"]+" title="([^"]+)">.*?'
    patron += '<img src="([^"]+)".*?'
    patron += '<var class="duree">(.*?)</var>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,scrapedtime in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        title = "[COLOR yellow]" + scrapedtime + "[/COLOR] " + scrapedtitle
        thumbnail = scrapedthumbnail
        plot = ""
        itemlist.append( Item(channel=item.channel, action="play", title=title, url=url, thumbnail=thumbnail,
                              fanart=thumbnail,plot=plot, contentTitle = title))
    next_page = scrapertools.find_single_match(data, '<li class="active">.*?<a href="([^"]+)" title="Page')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page ) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    scrapedurl = scrapertools.find_single_match(data, 'video_alt_url3: \'([^\']+)\'')
    if scrapedurl == "" :
        scrapedurl = scrapertools.find_single_match(data, 'video_alt_url2: \'([^\']+)\'')
    if scrapedurl == "" :
        scrapedurl = scrapertools.find_single_match(data, 'video_alt_url: \'([^\']+)\'')
    if scrapedurl == "" :
        scrapedurl = scrapertools.find_single_match(data, 'video_url: \'([^\']+)\'')

    itemlist.append(Item(channel=item.channel, action="play", title=scrapedurl, fulltitle=item.title, url=scrapedurl,
                        thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))
    return itemlist



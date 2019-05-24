# -*- coding: utf-8 -*-

import re

import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger

host = 'http://www.submityourflicks.com'

def mainlist(item):
    logger.info()
    itemlist = []
    
    itemlist.append(Item(channel=item.channel, action="videos", title="Útimos videos", url= host))
    itemlist.append(Item(channel=item.channel, action="videos", title="Mas vistos", url= host + "/most-viewed/"))
    itemlist.append(Item(channel=item.channel, action="videos", title="Mejor valorados", url= host + "/top-rated/"))
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar", url= host))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "-")
    item.url = host + "/search/%s/" % texto
    try:
        return videos(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def videos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div class="item-block item-normal col".*?'
    patron += '<a href="([^"]+)" title="([^"]+)">.*?'
    patron += 'data-src="([^"]+)".*?'
    patron += '</span> ([^"]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle, scrapedthumbnail, scrapedtime in matches:
        title = "[COLOR yellow]" + scrapedtime + "[/COLOR] " + scrapedtitle
        url = scrapedurl
        thumbnail = scrapedthumbnail.replace(" ", "%20")
        itemlist.append(Item(channel=item.channel, action="play", title=title, url=url, thumbnail=thumbnail,
                             fanart=thumbnail))
    next_page = scrapertools.find_single_match(data, "<a href='([^']+)' class=\"next\">NEXT</a>")
    if next_page != "":
        url = urlparse.urljoin(item.url, next_page)
        itemlist.append(Item(channel=item.channel, action="videos", title=">> Página siguiente", url=url))
    return itemlist


def play(item):
    logger.info()
    data = httptools.downloadpage(item.url).data
    media_url = "https:" + scrapertools.find_single_match(data, 'source src="([^"]+)"')
    itemlist = []
    itemlist.append(Item(channel=item.channel, action="play", title=item.title, fulltitle=item.fulltitle, url=media_url,
                         thumbnail=item.thumbnail, show=item.title, server="directo", folder=False))
    return itemlist


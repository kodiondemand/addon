# -*- coding: utf-8 -*-

import re

import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger


def mainlist(item):
    logger.info()
    itemlist = []
    if item.url == "":
        item.url = "http://www.peliculaseroticas.net/"
    data = httptools.downloadpage(item.url).data
    patron = '<div class="post">.*?'
    patron += '<a href="([^"]+)">([^<]+)</a>.*?'
    patron += '<img src="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        url = urlparse.urljoin(item.url, scrapedurl)
        title = scrapedtitle.strip()
        thumbnail = urlparse.urljoin(item.url, scrapedthumbnail)
        plot = ""
        itemlist.append( Item(channel=item.channel, action="findvideos", title=title, fulltitle=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot=plot, viewmode="movie"))
    # Extrae la marca de siguiente página
    if item.url == "http://www.peliculaseroticas.net/":
        next_page_url = "http://www.peliculaseroticas.net/cine-erotico/2.html"
    else:
        current_page = scrapertools.find_single_match(item.url, "(\d+)")
        next_page = int(current_page) + 1
        next_page_url = "http://www.peliculaseroticas.net/cine-erotico/" + str(next_page) + ".html"
    itemlist.append( Item(channel=item.channel, action="mainlist", title=">> Página siguiente", url=next_page_url))
    return itemlist


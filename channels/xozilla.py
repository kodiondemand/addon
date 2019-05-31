# -*- coding: utf-8 -*-
# ------------------------------------------------------------
import re

import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger

host = 'https://www.xozilla.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Nuevas", action="lista", url=host + "/latest-updates/"))
    itemlist.append(Item(channel=item.channel, title="Popular", action="lista", url=host + "/most-popular/"))
    itemlist.append(Item(channel=item.channel, title="Mejor valorada", action="lista", url=host + "/top-rated/"))

    itemlist.append(Item(channel=item.channel, title="PornStar", action="categorias", url=host + "/models/"))
    itemlist.append(Item(channel=item.channel, title="Canal", action="categorias", url=host + "/channels/"))
    itemlist.append(Item(channel=item.channel, title="Categorias", action="categorias", url=host + "/categories/"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/%s/" % texto
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
    patron = '<a class="item" href="([^"]+)" title="([^"]+)">.*?'
    patron += '<img class="thumb" src="([^"]+)".*?'
    patron += '(.*?)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle, scrapedthumbnail, cantidad in matches:
        scrapedplot = ""
        cantidad = scrapertools.find_single_match(cantidad, '(\d+) videos</div>')
        if cantidad:
            scrapedtitle += " (" + cantidad + ")"
        itemlist.append(Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                             thumbnail=scrapedthumbnail, fanart=scrapedthumbnail, plot=scrapedplot))
    next_page = scrapertools.find_single_match(data, '<li class="next"><a href="([^"]+)"')
    if next_page != "#videos":
        next_page = urlparse.urljoin(item.url, next_page)
        itemlist.append(item.clone(action="categorias", title="Página Siguiente >>", text_color="blue", url=next_page))
    if next_page == "#videos":
        next_page = scrapertools.find_single_match(data, 'from:(\d+)">Next</a>')
        next_page = urlparse.urljoin(item.url, next_page) + "/"
        itemlist.append(item.clone(action="categorias", title="Página Siguiente >>", text_color="blue", url=next_page))
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<a href="([^"]+)" class="item.*?'
    patron += 'data-original="([^"]+)".*?'
    patron += 'alt="([^"]+)".*?'
    patron += '<div class="duration">(.*?)</div>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedthumbnail, scrapedtitle, duracion in matches:
        url = scrapedurl
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        contentTitle = title
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append(Item(channel=item.channel, action="play", title=title, url=url, thumbnail=thumbnail,
                             fanart=thumbnail, plot=plot, contentTitle=contentTitle))
    next_page = scrapertools.find_single_match(data, '<li class="next"><a href="([^"]+)"')
    if next_page != "#videos":
        next_page = urlparse.urljoin(item.url, next_page)
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page))
    if next_page == "#videos":
        next_page = scrapertools.find_single_match(data, 'from:(\d+)">Next</a>')
        next_page = urlparse.urljoin(item.url, next_page) + "/"
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    media_url = scrapertools.find_single_match(data, 'video_alt_url: \'([^\']+)/\'')
    if media_url == "":
        media_url = scrapertools.find_single_match(data, 'video_url: \'([^\']+)/\'')
    itemlist.append(Item(channel=item.channel, action="play", title=item.title, fulltitle=item.fulltitle, url=media_url,
                         thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))
    return itemlist

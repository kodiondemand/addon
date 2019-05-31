# -*- coding: utf-8 -*-
# ------------------------------------------------------------
import re

import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger

host = 'https://www.youjizz.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Nuevas", action="lista", url=host + "/newest-clips/1.html"))
    itemlist.append(Item(channel=item.channel, title="Popular", action="lista", url=host + "/most-popular/1.html"))
    itemlist.append(
        Item(channel=item.channel, title="Mejor valorada", action="lista", url=host + "/top-rated-week/1.html"))
    itemlist.append(Item(channel=item.channel, title="Categorias", action="categorias", url=host))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/%s-1.html" % texto
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
    data = scrapertools.find_single_match(data, '<h4>Trending(.*?)</ul>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<li><a href="([^"]+)">([^"]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = scrapedtitle
        scrapedurl = urlparse.urljoin(item.url, scrapedurl)
        itemlist.append(Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                             thumbnail=scrapedthumbnail, plot=scrapedplot))
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<div class="video-item">.*?'
    patron += 'class="frame image" href="([^"]+)".*?'
    patron += 'data-original="([^"]+)" />.*?'
    patron += '<div class="video-title">.*?'
    patron += '>(.*?)</a>.*?'
    patron += '<span class="time">(.*?)</span>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedthumbnail, scrapedtitle, duracion in matches:
        url = urlparse.urljoin(item.url, scrapedurl)
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        quality = ""
        if '-720-' in scrapedthumbnail:
            quality = "720"
        if '-1080-' in scrapedthumbnail:
            quality = "1080"
        if quality:
            title = "[COLOR yellow]" + duracion + "[/COLOR] " + "[COLOR red]" + quality + "p[/COLOR] " + scrapedtitle
        contentTitle = title
        thumbnail = "http:" + scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append(Item(channel=item.channel, action="play", title=title, url=url, thumbnail=thumbnail,
                             plot=plot, quality=quality, contentTitle=contentTitle))
    next_page = scrapertools.find_single_match(data, '<li><a class="pagination-next" href="([^"]+)">Next &raquo;</a>')
    if next_page != "":
        next_page = urlparse.urljoin(item.url, next_page)
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, 'var encodings(.*?)var')
    if '360' in data:
        patron = '"360".*?"filename"\:"(.*?)"'
    if '720' in data:
        patron = '"720".*?"filename"\:"(.*?)"'
    if '1080' in data:
        patron = '"1080".*?"filename"\:"(.*?)"'
    media_url = scrapertools.find_single_match(data, patron)
    media_url = "https:" + media_url.replace("\\", "")
    itemlist.append(Item(channel=item.channel, action="play", title=item.title, fulltitle=item.fulltitle, url=media_url,
                         thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))
    return itemlist

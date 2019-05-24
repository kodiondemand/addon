# -*- coding: utf-8 -*-
# ------------------------------------------------------------
import re

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger

host = 'http://porneq.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Ultimos", action="lista", url=host + "/videos/browse/"))
    itemlist.append(Item(channel=item.channel, title="Mas Vistos", action="lista", url=host + "/videos/most-viewed/"))
    itemlist.append(Item(channel=item.channel, title="Mas Votado", action="lista", url=host + "/videos/most-liked/"))
    itemlist.append(Item(channel=item.channel, title="Big Tits", action="lista", url=host + "/show/big+tits&sort=w"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/show/%s" % texto
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<a class="clip-link" data-id="\d+" title="([^"]+)" href="([^"]+)">.*?'
    patron += '<img src="([^"]+)".*?'
    patron += '<span class="timer">(.*?)</span></div>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedtitle, scrapedurl, scrapedthumbnail, scrapedtime in matches:
        scrapedplot = ""
        scrapedtitle = "[COLOR yellow]" + (scrapedtime) + "[/COLOR] " + scrapedtitle
        itemlist.append(Item(channel=item.channel, action="play", title=scrapedtitle, url=scrapedurl,
                             fanart=scrapedthumbnail, thumbnail=scrapedthumbnail, plot=scrapedplot))
    next_page = scrapertools.find_single_match(data, '<nav id="page_nav"><a href="(.*?)"')
    if next_page != "":
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    scrapedurl = scrapertools.find_single_match(data, '<source src="([^"]+)"')
    itemlist.append(
        Item(channel=item.channel, action="play", title=item.title, fulltitle=item.fulltitle, url=scrapedurl,
             thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))
    return itemlist

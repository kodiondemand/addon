# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per cinetecadibologna
# ------------------------------------------------------------

import re

import urlparse

from core import httptools, scrapertools
from core.item import Item
from platformcode import logger, config

host = "http://cinestore.cinetecadibologna.it"

headers = [['Referer', host]]

def mainlist(item):
    logger.info("kod.cinetecadibologna mainlist")
    itemlist = [Item(channel=item.channel, 
                     title="[COLOR azure]Elenco Film - Cineteca di Bologna[/COLOR]", 
                     action="peliculas",
                     url="%s/video/alfabetico_completo" % host,
                     thumbnail="http://cinestore.cinetecadibologna.it/pics/logo.gif"),
                Item(channel=item.channel,
                     title="[COLOR azure]Epoche - Cineteca di Bologna[/COLOR]",
                     action="epoche",
                     url="%s/video/epoche" % host,
                     thumbnail="http://cinestore.cinetecadibologna.it/pics/logo.gif"),
                Item(channel=item.channel,
                     title="[COLOR azure]Percorsi Tematici - Cineteca di Bologna[/COLOR]",
                     action="percorsi",
                     url="%s/video/percorsi" % host,
                     thumbnail="http://cinestore.cinetecadibologna.it/pics/logo.gif")]

    return itemlist


def peliculas(item):
    logger.info("kod.cinetecadibologna peliculas")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    # Estrae i contenuti 
    patron = '<img src="([^"]+)"[^>]+>\s*[^>]+>\s*<div[^>]+>\s*<div[^>]+>[^>]+>\s*<a href="([^"]+)"[^>]+>(.*?)<'
    matches = re.compile(patron, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedthumbnail, scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        scrapedthumbnail = host + scrapedthumbnail
        scrapedurl = host + scrapedurl
        if not "/video/" in scrapedurl:
            continue
##        html = scrapertools.cache_page(scrapedurl)
        html = httptools.downloadpage(scrapedurl, headers=headers).data
        start = html.find("Sinossi:")
        end = html.find('<div class="sx_col">', start)
        scrapedplot = html[start:end]
        scrapedplot = re.sub(r'<[^>]*>', '', scrapedplot)
        scrapedplot = scrapertools.decodeHtmlentities(scrapedplot)
        itemlist.append(Item(channel=item.channel, action="findvideos", fulltitle=scrapedtitle, show=scrapedtitle,
                             title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot,
                             folder=True))

    # Paginazione 
    patronvideos = '<div class="footerList clearfix">\s*<div class="sx">\s*[^>]+>[^g]+gina[^>]+>\s*[^>]+>\s*<div class="dx">\s*<a href="(.*?)">pagina suc'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)

    if len(matches) > 0:
        scrapedurl = urlparse.urljoin(item.url, matches[0])
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url= scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))

    return itemlist

def epoche(item):
    logger.info("kod.cinetecadibologna categorias")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    # Narrow search by selecting only the combo
    bloque = scrapertools.find_single_match(data, '<h1 class="pagetitle">Epoche</h1>(.*?)</ul>')

    # The categories are the options for the combo
    patron = '<a href="([^"]+)">(.*?)<'
    matches = re.compile(patron, re.DOTALL).findall(bloque)

    for scrapedurl, scrapedtitle in matches:
        scrapedurl = host + scrapedurl
        scrapedplot = ""
        if scrapedtitle.startswith(("'")):
           scrapedtitle = scrapedtitle.replace("'", "Anni '")
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://www.cinetecadibologna.it/pics/cinema-ritrovato-alcinema.png",
                 plot=scrapedplot))

    return itemlist

def percorsi(item):
    logger.info("kod.cinetecadibologna categorias")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    patron = '<div class="cover_percorso">\s*<a href="([^"]+)">\s*<img src="([^"]+)"[^>]+>\s*[^>]+>(.*?)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        scrapedurl = host + scrapedurl
        scrapedplot = ""
        scrapedthumbnail = host + scrapedthumbnail
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot))

    return itemlist

def findvideos(item):
    logger.info("kod.cinetecadibologna findvideos")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    patron = 'filename: "(.*?)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for video in matches:
        video = host + video
        itemlist.append(
            Item(
                channel=item.channel,
                action="play",
                title=item.title + " [[COLOR orange]Diretto[/COLOR]]",
                url=video,
                folder=False))

    return itemlist


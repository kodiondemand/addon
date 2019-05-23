# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per itastreaming
# ----------------------------------------------------------
import base64
import re
import urlparse

from core import scrapertools, httptools, servertools, tmdb, support
from core.item import Item
from platformcode import logger, config



host = "https://itastreaming.film"

headers = [['Referer', host]]


def mainlist(item):
    logger.info("[itastreaming.py] mainlist")

    itemlist = [
        Item(channel=item.channel,
             title="[COLOR azure]Home[/COLOR]",
             action="fichas",
             url=host,
             thumbnail=""),
        Item(channel=item.channel,
             title="[COLOR azure]Nuove uscite[/COLOR]",
             action="fichas",
             url=host + "/nuove-uscite/",
             thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
        Item(channel=item.channel,
             title="[COLOR azure]Film per Genere[/COLOR]",
             action="genere",
             url=host,
             thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
        Item(channel=item.channel,
             title="[COLOR azure]Film per Qualita'[/COLOR]",
             action="quality",
             url=host,
             thumbnail="http://files.softicons.com/download/computer-icons/disks-icons-by-wil-nichols/png/256x256/Blu-Ray.png"),

        Item(channel=item.channel,
             title="[COLOR azure]Film A-Z[/COLOR]",
             action="atoz",
             url=host + "/tag/a/",
             thumbnail="http://i.imgur.com/IjCmx5r.png"),

        Item(channel=item.channel,
             title="[COLOR orange]Cerca...[/COLOR]",
             action="search",
             extra="movie",
             thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

    return itemlist


def newest(categoria):
    logger.info("[itastreaming.py] newest" + categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "film":
            item.url = host + "/nuove-uscite/"
            item.action = "fichas"
            itemlist = fichas(item)

            if itemlist[-1].action == "fichas":
                itemlist.pop()

    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def search(item, texto):
    logger.info("[itastreaming.py] " + item.url + " search " + texto)

    item.url = host + "/?s=" + texto

    try:
        return searchfilm(item)

    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def searchfilm(item):
    logger.info("[itastreaming.py] fichas")

    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data
    # fix - calidad
    data = re.sub(
        r'<div class="wrapperImage"[^<]+<a',
        '<div class="wrapperImage"><fix>SD</fix><a',
        data
    )
    # fix - IMDB
    data = re.sub(
        r'<h5> </div>',
        '<fix>IMDB: 0.0</fix>',
        data
    )

    patron = '<li class="s-item">.*?'
    patron += 'src="([^"]+)".*?'
    patron += 'alt="([^"]+)".*?'
    patron += 'href="([^"]+)".*?'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedtitle, scrapedurl in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)

        # ------------------------------------------------
        scrapedthumbnail = httptools.get_url_headers(scrapedthumbnail)
        # ------------------------------------------------
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 title=scrapedtitle,
                 contentType="movie",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 fulltitle=scrapedtitle,
                 show=scrapedtitle))

    # Paginación
    next_page = scrapertools.find_single_match(data, "href='([^']+)'>Seguente &rsaquo;")
    if next_page != "":
        itemlist.append(
            Item(channel=item.channel,
                 action="searchfilm",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=next_page,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png"))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def genere(item):
    logger.info("[itastreaming.py] genere")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    patron = '<ul class="sub-menu">(.+?)</ul>'
    data = scrapertools.find_single_match(data, patron)

    patron = '<li[^>]+><a href="([^"]+)">(.*?)</a></li>'

    matches = re.compile(patron, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapedtitle.replace('&amp;', '-')
        itemlist.append(
            Item(channel=item.channel,
                 action="fichas",
                 title=scrapedtitle,
                 url=scrapedurl,
                 folder=True))

    return itemlist


def atoz(item):
    logger.info("[itastreaming.py] genere")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    patron = '<div class="generos">(.+?)</ul>'
    data = scrapertools.find_single_match(data, patron)

    patron = '<li>.*?'
    patron += 'href="([^"]+)".*?'
    patron += '>([^"]+)</a>'

    matches = re.compile(patron, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapedtitle.replace('&amp;', '-')
        itemlist.append(
            Item(channel=item.channel,
                 action="fichas",
                 title=scrapedtitle,
                 url=scrapedurl,
                 folder=True))

    return itemlist


def quality(item):
    logger.info("[itastreaming.py] genere")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    patron = '<a>Qualità</a>(.+?)</ul>'
    data = scrapertools.find_single_match(data, patron)

    patron = '<li id=".*?'
    patron += 'href="([^"]+)".*?'
    patron += '>([^"]+)</a>'

    matches = re.compile(patron, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapedtitle.replace('&amp;', '-')
        itemlist.append(
            Item(channel=item.channel,
                 action="fichas",
                 title=scrapedtitle,
                 url=scrapedurl,
                 folder=True))

    return itemlist


def fichas(item):
    logger.info("[itastreaming.py] fichas")

    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data
    # fix - calidad
    data = re.sub(
        r'<div class="wrapperImage"[^<]+<a',
        '<div class="wrapperImage"><fix>SD</fix><a',
        data
    )
    # fix - IMDB
    data = re.sub(
        r'<h5> </div>',
        '<fix>IMDB: 0.0</fix>',
        data
    )

    patron = '<div class="item">.*?'
    patron += 'href="([^"]+)".*?'
    patron += 'title="([^"]+)".*?'
    patron += '<img src="([^"]+)".*?'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)

        # ------------------------------------------------
        scrapedthumbnail = httptools.get_url_headers(scrapedthumbnail)
        # ------------------------------------------------
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 title=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 fulltitle=scrapedtitle,
                 show=scrapedtitle))

    # Paginación
    next_page = scrapertools.find_single_match(data, "href='([^']+)'>Seguente &rsaquo;")
    if next_page != "":
        itemlist.append(
            Item(channel=item.channel,
                 action="fichas",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=next_page,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png"))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def findvideos(item):
    logger.info("[italiafilmvideohd.py] findvideos")

    itemlist = support.hdpass_get_servers(item)

    return itemlist



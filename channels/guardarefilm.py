# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per guardarefilm
# ----------------------------------------------------------
import re

import urlparse

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import logger, config

host = "https://www.guardarefilm.video"

headers = [['Referer', host]]


def mainlist(item):
    logger.info("kod.guardarefilm mainlist")
    itemlist = [Item(channel=item.channel,
                     title="[COLOR azure]Novita'[/COLOR]",
                     action="peliculas",
                     url="%s/streaming-al-cinema/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR azure]HD[/COLOR]",
                     action="peliculas",
                     url="%s/film-streaming-hd/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR azure]Popolari[/COLOR]",
                     action="pelis_top100",
                     url="%s/top100.html" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR azure]Categorie[/COLOR]",
                     action="categorias",
                     url=host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR azure]Animazione[/COLOR]",
                     action="peliculas",
                     url="%s/streaming-cartoni-animati/" % host,
                     thumbnail="http://orig09.deviantart.net/df5a/f/2014/169/2/a/fist_of_the_north_star_folder_icon_by_minacsky_saya-d7mq8c8.png"),
                Item(channel=item.channel,
                     title="[COLOR yellow]Cerca...[/COLOR]",
                     action="search",
                     extra="movie",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search"),
                Item(channel=item.channel,
                     title="[COLOR azure]Serie TV[/COLOR]",
                     action="peliculas_tv",
                     extra="tvshow",
                     url="%s/serie-tv-streaming/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR yellow]Cerca Serie TV...[/COLOR]",
                     action="search",
                     extra="tvshow",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]
    return itemlist


def newest(categoria):
    logger.info("kod.guardarefilm newest" + categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "film":
            item.url = host + "/streaming-al-cinema/"
            item.action = "peliculas"
            itemlist = peliculas(item)

            if itemlist[-1].action == "peliculas":
                itemlist.pop()

    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def categorias(item):
    logger.info("kod.guardarefilm categorias")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    # Narrow search by selecting only the combo
    bloque = scrapertools.find_single_match(data, '<ul class="reset dropmenu">(.*?)</ul>')

    # The categories are the options for the combo
    patron = '<li><a href="([^"]+)">(.*?)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(bloque)

    for scrapedurl, scrapedtitle in matches:
        scrapedurl = urlparse.urljoin(item.url, scrapedurl)
        scrapedthumbnail = ""
        scrapedplot = ""
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot))

    return itemlist


def search(item, texto):
    logger.info("[guardarefilm.py] " + item.url + " search " + texto)
    section = ""
    if item.extra == "tvshow":
        section = "0"
    elif item.extra == "movie":
        section = "1"
    item.url = '%s?do=search_advanced&q=%s&section=%s&director=&actor=&year_from=&year_to=' % (host, texto, section)
    try:
        if item.extra == "movie":
            return peliculas(item)
        if item.extra == "tvshow":
            return peliculas_tv(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def peliculas(item):
    logger.info("kod.guardarefilm peliculas")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    # Estrae i contenuti 
    patron = '<div class="poster"><a href="([^"]+)".*?><img src="([^"]+)".*?><span.*?</div>\s*'
    patron += '<div.*?><a.*?>(.*?)</a></div>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        scrapedplot = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(
            Item(channel=item.channel,
                 action="episodios" if item.extra == "tvshow" else "findvideos",
                 contentType="movie",
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=urlparse.urljoin(host, scrapedthumbnail),
                 plot=scrapedplot,
                 folder=True))

    # Paginazione 
    patronvideos = '<div class="pages".*?<span>.*?<a href="([^"]+)">'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)

    if len(matches) > 0:
        scrapedurl = urlparse.urljoin(item.url, matches[0])
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))

    return itemlist


def peliculas_tv(item):
    logger.info("kod.guardarefilm peliculas")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    # Estrae i contenuti 
    patron = '<div class="poster"><a href="([^"]+)".*?><img src="([^"]+)".*?><span.*?</div>\s*'
    patron += '<div.*?><a.*?>(.*?)</a></div>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        scrapedplot = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(
            Item(channel=item.channel,
                 action="episodios" if item.extra == "tvshow" else "findvideos",
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=urlparse.urljoin(host, scrapedthumbnail),
                 plot=scrapedplot,
                 folder=True))

    # Paginazione 
    patronvideos = '<div class="pages".*?<span>.*?<a href="([^"]+)">'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)

    if len(matches) > 0:
        scrapedurl = urlparse.urljoin(item.url, matches[0])
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas_tv",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))

    return itemlist

def pelis_top100(item):
    logger.info("kod.guardarefilm peliculas")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    # Estrae i contenuti 
    patron = r'<span class="top100_title"><a href="([^"]+)">(.*?\(\d+\))</a>'
    matches = re.compile(patron).findall(data)

    for scrapedurl, scrapedtitle in matches:
        html = httptools.downloadpage(scrapedurl, headers=headers).data
        start = html.find("<div class=\"textwrap\" itemprop=\"description\">")
        end = html.find("</div>", start)
        scrapedplot = html[start:end]
        scrapedplot = re.sub(r'<[^>]*>', '', scrapedplot)
        scrapedplot = scrapertools.decodeHtmlentities(scrapedplot)
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        scrapedthumbnail = scrapertools.find_single_match(html, r'class="poster-wrapp"><a href="([^"]+)"')
        itemlist.append(
            Item(channel=item.channel,
                 action="episodios" if item.extra == "tvshow" else "findvideos",
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=urlparse.urljoin(host, scrapedthumbnail),
                 plot=scrapedplot,
                 folder=True,
                 fanart=host + scrapedthumbnail))

    return itemlist


def episodios(item):
    logger.info("kod.guardarefilm episodios")

    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data

    patron = r'<li id="serie-[^"]+" data-title="Stai guardando: ([^"]+)">'
    patron += r'[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(.*?)</span>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedtitle, scrapedurl in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentType="episode",
                 title=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=item.thumbnail,
                 extra=item.extra,
                 fulltitle=item.fulltitle,
                 show=item.show))

    if config.get_videolibrary_support() and len(itemlist) != 0:
        itemlist.append(
            Item(channel=item.channel,
                 title="[COLOR lightblue]%s[/COLOR]" % config.get_localized_string(30161),
                 url=item.url,
                 action="add_serie_to_library",
                 extra="episodios",
                 show=item.show))

    return itemlist


def findvideos(item):
    logger.info("kod.guardarefilm findvideos")

    # Carica la pagina 
    data = item.url if item.contentType == "episode" else httptools.downloadpage(item.url).data

    itemlist = servertools.find_video_items(data=data)
    for videoitem in itemlist:
        videoitem.title = item.title + videoitem.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.show = item.show
        videoitem.plot = item.plot
        videoitem.channel = item.channel
        videoitem.contentType = item.contentType

    return itemlist

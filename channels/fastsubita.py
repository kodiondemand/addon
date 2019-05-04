# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per fastsubita
# ------------------------------------------------------------

import re, urlparse

from channels import autoplay, filtertools
from core import scrapertools, servertools, httptools, tmdb
from core.item import Item
from platformcode import config, logger

host = "http://fastsubita.com"

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['verystream', 'openload', 'speedvideo', 'wstream', 'flashx', 'vidoza', 'vidtome']
list_quality = ['default']

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'fastsubita')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'fastsubita')

headers = [
    ['Host', 'fastsubita.com'],
    ['User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0'],
    ['Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'],
    ['Accept-Language', 'en-US,en;q=0.5'],
    ['Accept-Encoding', 'gzip, deflate'],
    ['Referer', host],
    ['DNT', '1'],
    ['Connection', 'keep-alive'],
    ['Upgrade-Insecure-Requests', '1'],
    ['Cache-Control', 'max-age=0']
]

PERPAGE = 14


def mainlist(item):
    logger.info("[fastsubita.py] mainlist")

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = [Item(channel=item.channel,
                     title="[COLOR azure]Aggiornamenti[/COLOR]",
                     action="serietv",
                     extra='serie',
                     url=host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR azure]Tutte le Serie TV[/COLOR]",
                     action="all_quick",
                     extra='serie',
                     url="%s/elenco-serie-tv/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR yellow]Cerca...[/COLOR]",
                     action="search",
                     extra='serie',
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def newest(categoria):
    logger.info("[fastsubita.py]==> newest" + categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "series":
            item.url = host
            item.action = "serietv"
            itemlist = serietv(item)

            if itemlist[-1].action == "serietv":
                itemlist.pop()

    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def serietv(item):
    logger.info("[fastsubita.py] peliculas")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data
    logger.info("[fastsubita.py] peliculas")

    # Estrae i contenuti 
    patron = r'<h3 class="entry-title title-font"><a href="([^"]+)" rel="bookmark">(.*?)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scraped_1 = scrapedtitle.split("&#215;")[0][:-2]
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        scrapedtitle = scrapedtitle.replace(scraped_1, "")

        if "http:" in scrapedurl:
            scrapedurl = scrapedurl
        else:
            scrapedurl = "http:" + scrapedurl

        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentTpye="tvshow",
                 title="[COLOR azure]" + scraped_1 + "[/COLOR]" + " " + scrapedtitle,
                 fulltitle=scraped_1,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 show=scraped_1,
                 extra=item.extra,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Paginazione 
    patronvideos = r'<a class="next page-numbers" href="(.*?)">Successivi'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)

    if len(matches) > 0:
        scrapedurl = urlparse.urljoin(item.url, matches[0])
        itemlist.append(
            Item(channel=item.channel,
                 action="serietv",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 extra=item.extra,
                 folder=True))

    return itemlist


def all_quick(item):
    logger.info("[fastsubita.py] peliculas")
    itemlist = []

    p = 1
    if '{}' in item.url:
        item.url, p = item.url.split('{}')
        p = int(p)

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    # Estrae i contenuti 
    patron = r'<a style.*?href="([^"]+)">([^<]+)<\/a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for i, (scrapedurl, scrapedtitle) in enumerate(matches):
        if (p - 1) * PERPAGE > i: continue
        if i >= p * PERPAGE: break
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        if 'S' in scrapedtitle.lower(): continue

        if "http:" in scrapedurl:
            scrapedurl = scrapedurl
        else:
            scrapedurl = "http:" + scrapedurl

        itemlist.append(
            Item(channel=item.channel,
                 action="serietv",
                 contentType="tvshow",
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 text_color="azure",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 show=scrapedtitle,
                 extra=item.extra,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if len(matches) >= p * PERPAGE:
        scrapedurl = item.url + '{}' + str(p + 1)
        itemlist.append(
            Item(channel=item.channel,
                 extra=item.extra,
                 action="all_quick",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))

    return itemlist

def findvideos(item):
    logger.info("[fastsubita.py] findvideos")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    bloque = scrapertools.find_single_match(data, '<div class="entry-content">(.*?)<footer class="entry-footer">')

    patron = r'<a href="([^"]+)">'
    matches = re.compile(patron, re.DOTALL).findall(bloque)
    for scrapedurl in matches:
        if 'is.gd' in scrapedurl:
            resp = httptools.downloadpage(
                 scrapedurl, follow_redirects=False)
            data += resp.headers.get("location", "") + '\n'

    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.title + videoitem.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.show = item.show
        videoitem.plot = item.plot
        videoitem.channel = item.channel
        videoitem.contentType = item.contentType
        videoitem.language = IDIOMAS['Italiano']

    # Requerido para Filtrar enlaces

    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)

    # Requerido para FilterTools

    # itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)



    return itemlist


def search(item, texto):
    logger.info("[fastsubita.py] " + item.url + " search " + texto)
    item.url = "%s/?s=%s" % (host, texto)
    try:
        return serietv(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

    

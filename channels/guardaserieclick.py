# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per guardaserie.click
# ------------------------------------------------------------

import re

from core import httptools, scrapertools, servertools, support
from core import tmdb
from core.item import Item
from platformcode import logger, config

host = "http://www.guardaserie.watch"

headers = [['Referer', host]]


# ----------------------------------------------------------------------------------------------------------------
def mainlist(item):
    logger.info("[GuardaSerieClick.py]==> mainlist")
    itemlist = [Item(channel=item.channel,
                     action="nuoveserie",
                     title=support.color("Nuove serie TV", "orange"),
                     url="%s/lista-serie-tv" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="serietvaggiornate",
                     title=support.color("Serie TV Aggiornate", "azure"),
                     url="%s/lista-serie-tv" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="lista_serie",
                     title=support.color("Anime", "azure"),
                     url="%s/category/animazione/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="categorie",
                     title=support.color("Categorie", "azure"),
                     url=host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="search",
                     title=support.color("Cerca ...", "yellow"),
                     extra="serie",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def newest(categoria):
    logger.info("[GuardaSerieClick.py]==> newest" + categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "series":
            item.url = "%s/lista-serie-tv" % host
            item.action = "serietvaggiornate"
            itemlist = serietvaggiornate(item)

            if itemlist[-1].action == "serietvaggiornate":
                itemlist.pop()

    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def search(item, texto):
    logger.info("[GuardaSerieClick.py]==> search")
    item.url = host + "/?s=" + texto
    try:
        return lista_serie(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def nuoveserie(item):
    logger.info("[GuardaSerieClick.py]==> nuoveserie")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    blocco = scrapertools.find_single_match(data, '<div\s*class="container container-title-serie-new container-scheda" meta-slug="new">(.*?)</div></div><div')

    patron = r'<a\s*href="([^"]+)".*?>\s*<img\s*.*?src="([^"]+)" />[^>]+>[^>]+>[^>]+>[^>]+>'
    patron += r'[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)</p>'
    matches = re.compile(patron, re.DOTALL).findall(blocco)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(
            Item(channel=item.channel,
                 action="episodi",
                 contentType="tv",
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 extra="tv",
                 show=scrapedtitle,
                 thumbnail=scrapedthumbnail,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def serietvaggiornate(item):
    logger.info("[GuardaSerieClick.py]==> serietvaggiornate")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    blocco = scrapertools.find_single_match(data,
                                    r'<div\s*class="container container-title-serie-lastep  container-scheda" meta-slug="lastep">(.*?)</div></div><div')

    patron = r'<a\s*rel="nofollow" href="([^"]+)"[^>]+> <img\s*.*?src="([^"]+)"[^>]+>[^>]+>'
    patron += r'[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)<[^>]+>'
    matches = re.compile(patron, re.DOTALL).findall(blocco)

    for scrapedurl, scrapedthumbnail, scrapedep, scrapedtitle in matches:
        episode = re.compile(r'^(\d+)x(\d+)', re.DOTALL).findall(scrapedep)  # Prendo stagione ed episodio
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        title = "%s %s" % (scrapedtitle, scrapedep)
        extra = r'<span\s*.*?meta-stag="%s" meta-ep="%s" meta-embed="([^"]+)"[^>]*>' % (
            episode[0][0], episode[0][1].lstrip("0"))
        itemlist.append(
            Item(channel=item.channel,
                 action="findepvideos",
                 contentType="tv",
                 title=title,
                 show=title,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 extra=extra,
                 thumbnail=scrapedthumbnail,
                 folder=True))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def categorie(item):
    logger.info("[GuardaSerieClick.py]==> categorie")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    blocco = scrapertools.find_single_match(data, r'<ul\s*class="dropdown-menu category">(.*?)</ul>')
    patron = r'<li>\s*<a\s*href="([^"]+)"[^>]+>([^<]+)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(blocco)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action="lista_serie",
                 title=scrapedtitle,
                 contentType="tv",
                 url="".join([host, scrapedurl]),
                 thumbnail=item.thumbnail,
                 extra="tv",
                 folder=True))

    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def lista_serie(item):
    logger.info("[GuardaSerieClick.py]==> lista_serie")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    patron = r'<a\s*href="([^"]+)".*?>\s*<img\s*.*?src="([^"]+)" />[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)</p></div>'
    blocco = scrapertools.find_single_match(data,
                                    r'<div\s*class="col-xs-\d+ col-sm-\d+-\d+">(.*?)<div\s*class="container-fluid whitebg" style="">')
    matches = re.compile(patron, re.DOTALL).findall(blocco)

    for scrapedurl, scrapedimg, scrapedtitle in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        itemlist.append(
            Item(channel=item.channel,
                 action="episodi",
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedimg,
                 extra=item.extra,
                 show=scrapedtitle,
                 folder=True))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def episodi(item):
    logger.info("[GuardaSerieClick.py]==> episodi")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    patron = r'<div\s*class="[^"]+">([^<]+)<\/div>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>'
    patron += r'[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s*<span\s*.*?'
    patron += r'embed="([^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s*'
    patron += r'<img\s*class="[^"]+" src="" data-original="([^"]+)"[^>]+>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedtitle, scrapedurl, scrapedthumbnail in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 contentType="episode",
                 thumbnail=scrapedthumbnail,
                 folder=True))

    if config.get_videolibrary_support() and len(itemlist) != 0:
        itemlist.append(
            Item(channel=item.channel,
                 title="[COLOR lightblue]%s[/COLOR]" % config.get_localized_string(30161),
                 url=item.url,
                 action="add_serie_to_library",
                 extra="episodi",
                 show=item.show))

    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def findepvideos(item):
    logger.info("[GuardaSerieClick.py]==> findepvideos")

    data = httptools.downloadpage(item.url, headers=headers).data
    data = scrapertools.find_single_match(data, item.extra)
    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        server = re.sub(r'[-\[\]\s]+', '', videoitem.title).capitalize()
        videoitem.title = "".join(["[%s] " % support.color(server.capitalize(), 'orange'), item.title])
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.show = item.show
        videoitem.plot = item.plot
        videoitem.channel = item.channel

    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def findvideos(item):
    logger.info("[GuardaSerieClick.py]==> findvideos")

    itemlist = servertools.find_video_items(data=item.url)

    for videoitem in itemlist:
        server = re.sub(r'[-\[\]\s]+', '', videoitem.title).capitalize()
        videoitem.title = "".join(["[%s] " % support.color(server.capitalize(), 'orange'), item.title])
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.show = item.show
        videoitem.plot = item.plot
        videoitem.channel = item.channel

    return itemlist

# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per casacinema
# ------------------------------------------------------------
import re, urlparse, base64

from core import scrapertoolsV2, httptools, servertools, tmdb
from channels import autoplay, support
from core.item import Item
from platformcode import logger, config


host = 'https://casacinema.info'

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['verystream', 'openload', 'wstream', 'speedvideo']
list_quality = ['1080p', '720', '480p', '360p']

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'casacinema')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'casacinema')


def mainlist(item):
    logger.info("alfa.casacinema mainlist")

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = [Item(channel=item.channel,
                     title="Film",
                     action="peliculas",
                     extra="movie",
                     url=host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="In sala",
                     action="peliculas",
                     extra="movie",
                     url="%s/category/in-sala/" % host,
                     thumbnail="http://jcrent.com/apple%20tv%20final/HD.png"),
                Item(channel=item.channel,
                     title="Novità",
                     action="peliculas",
                     extra="movie",
                     url="%s/category/nuove-uscite/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="Sub - Ita",
                     action="peliculas",
                     extra="movie",
                     url="%s/category/sub-ita/" % host,
                     thumbnail="http://i.imgur.com/qUENzxl.png"),
                Item(channel=item.channel,
                     title="[COLOR yellow]Cerca...[/COLOR]",
                     action="search",
                     extra="movie",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

    
    autoplay.show_option(item.channel, itemlist)

    return itemlist


def search(item, texto):
    logger.info("[casacinemaInfo.py] " + item.url + " search " + texto)

    item.url = host + "?s=" + texto
    data = httptools.downloadpage(item.url).data

    itemlist = []

    patron = '<li class="col-md-12 itemlist">.*?<a href="([^"]+)" title="([^"]+)".*?<img src="([^"]+)".*?Film dell\\\'anno: ([0-9]{4}).*?<p class="text-list">([^<>]+)</p>'
    matches = scrapertoolsV2.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle, scrapedthumbnail, scrapedyear, scrapedplot in matches:
        title = scrapertoolsV2.decodeHtmlentities(scrapedtitle)
        cleantitle = title.replace('[Sub-ITA]', '').strip()

        infoLabels = {"plot": scrapertoolsV2.decodeHtmlentities(scrapedplot), "year": scrapedyear}

        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentType="movie",
                 title=title,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 infoLabels=infoLabels,
                 fulltitle=cleantitle))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def peliculas(item):
    logger.info("[casacinemaInfo.py] peliculas")

    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data

    # Estrae i contenuti

    patron = '<div class="col-mt-5 postsh">[^<>]+<div class="poster-media-card">[^<>]+<a href="([^"]+)" title="([^"]+)".*?<img src="([^"]+)"'

    matches = scrapertoolsV2.find_multiple_matches(data, patron)

    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        title = scrapertoolsV2.decodeHtmlentities(scrapedtitle)
        cleantitle = title.replace('[Sub-ITA]', '').strip()

        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentType="movie",
                 title=title,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 fulltitle=cleantitle))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    ## Paginación
    next_page = scrapertoolsV2.find_single_match(data, '<a href="([^"]+)"><i class="glyphicon glyphicon-chevron-right"')  ### <- Regex rimosso spazio - precedente <li><a href="([^"]+)" >Pagina -> Continua. riga 221

    if next_page != "":
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=next_page,
                 extra=item.extra,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png"))

    return itemlist


def findvideos(item):
    logger.info("[casacinemaInfo.py] findvideos")

    itemlist = support.hdpass_get_servers(item)

    # Requerido para Filtrar enlaces

    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)
    return itemlist

# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per piratestreaming
# ----------------------------------------------------------
import re

import urlparse

from core import httptools, scrapertools, servertools
from core import tmdb
from core.item import Item
from lib import unshortenit
from platformcode import logger, config
from specials import autoplay

__channel__ = "piratestreaming"

host = "http://www.piratestreaming.watch"

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['speedvideo', 'openload', 'youtube']
list_quality = ['default']


__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'piratestreaming')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'piratestreaming')

headers = [['Referer', host]]


def mainlist(item):

    autoplay.init(item.channel, list_servers, list_quality)

    logger.info()
    itemlist = [Item(channel=item.channel,
                     title="[COLOR azure]Film[/COLOR]",
                     action="peliculas",
                     extra="movie",
                     url="%s/category/films/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR yellow]Cerca...[/COLOR]",
                     action="search",
                     extra="movie",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search"),
                Item(channel=item.channel,
                     title="[COLOR azure]Serie TV[/COLOR]",
                     extra="tvshow",
                     action="peliculas_tv",
                     url="%s/category/serie/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR azure]Anime[/COLOR]",
                     extra="tvshow",
                     action="peliculas_tv",
                     url="%s/category/anime-cartoni-animati/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR yellow]Cerca SerieTV...[/COLOR]",
                     action="search",
                     extra="tvshow",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data

    # Estrae i contenuti 
    patron = 'data-placement="bottom" title="(.*?)" alt=[^=]+="([^"]+)"> <img'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedtitle, scrapedurl in matches:
        scrapedthumbnail = ""
        scrapedplot = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentType="movie",
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 extra=item.extra,
                 folder=True))

    # Paginazione
    patronvideos = '<a\s*class="nextpostslink" rel="next" href="([^"]+)">Avanti'
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

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def peliculas_tv(item):
    logger.info()
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data

    # Estrae i contenuti 
    patron = 'data-placement="bottom" title="(.*?)" alt=[^=]+="([^"]+)"> <img'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedtitle, scrapedurl in matches:
        scrapedthumbnail = ""
        scrapedplot = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        itemlist.append(
            Item(channel=item.channel,
                 action="episodios",
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 extra=item.extra,
                 folder=True))

    # Paginazione
    patronvideos = '<a\s*class="nextpostslink" rel="next" href="([^"]+)">Avanti'
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

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

def search(item, texto):
    logger.info("[piratestreaming.py] " + item.url + " search " + texto)
    item.url = host + "/?s=" + texto
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


def episodios(item):
    itemlist = []

    data = httptools.downloadpage(item.url).data

    # patron = 'link-episode">(.*?)<\/span>\s*<a\s*ref="nofollow" target="[^"]+"[^h]+href="([^"]+)"'
    patron = r'link-episode">(.*?)<\/span>\s*(.*?)</div>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedtitle, scrapedurl in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        scrapedtitle = re.sub(r'\s+', ' ', scrapedtitle)
        scrapedtitle = scrapedtitle.replace(" -", "")
        scrapedtitle = scrapedtitle.replace("<strong>", "")
        scrapedtitle = scrapedtitle.replace("</strong>", " ")

        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentType="episode",
                 title=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=item.thumbnail,
                 extra=item.extra,
                 fulltitle=scrapedtitle,
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
    logger.info()
    itemlist = []

    if item.contentType == 'episode':
        data = item.url
        urls = re.findall(r'<a\s*ref="nofollow" target="_blank" act="\d+"[^n]+newlink="([^"]+)" class="blue-link">[^<]+</a>', data, re.DOTALL)
    else:
        data = httptools.downloadpage(item.url).data
        urls = re.findall(r'<iframe\s*allowfullscreen class="embed-responsive-item" src="([^"]+)"></iframe></div>', data, re.DOTALL)

    if urls:
        for url in urls:
            url, c = unshortenit.unshorten(url)
            data += url + '\n'

    itemlist += servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = "[[COLOR green][B]%s[/B][/COLOR]] %s" % (videoitem.title.capitalize(), item.title)
        videoitem.fulltitle = item.fulltitle
        videoitem.show = item.show
        videoitem.thumbnail = item.thumbnail
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



    if item.contentType != 'episode':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            itemlist.append(
                Item(channel=item.channel, title='[COLOR yellow][B]Aggiungi alla videoteca[/B][/COLOR]', url=item.url,
                     action="add_pelicula_to_library", extra="findvideos", contentTitle=item.contentTitle))

    return itemlist

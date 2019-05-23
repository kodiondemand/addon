# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per ilgeniodellostreaming
# ------------------------------------------------------------
import re, urlparse

from platformcode import config, logger
from core import scrapertools, servertools, httptools
from core.item import Item
from specials import autoplay
from specials import filtertools
from core import tmdb

__channel__ = "ilgeniodellostreaming"

host = "https://ilgeniodellostreaming.pw"

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['verystream', 'openload', 'streamango', 'youtube']
list_quality = ['default']


__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'ilgeniodellostreaming')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'ilgeniodellostreaming')

headers = [['Referer', host]]

PERPAGE = 10

def mainlist(item):
    logger.info("kod.ilgeniodellostreaming mainlist")

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = [Item(channel=__channel__,
                     title="[COLOR azure]Ultimi Film Inseriti[/COLOR]",
                     action="peliculas",
                     url="%s/film/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=__channel__,
                     title="[COLOR azure]Film Per Categoria[/COLOR]",
                     action="categorias",
                     url=host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=__channel__,
                     title="[COLOR azure]Serie TV[/COLOR]",
                     action="serie",
                     url="%s/serie/" % host,
                     thumbnail="http://www.ilmioprofessionista.it/wp-content/uploads/2015/04/TVSeries3.png"),
                Item(channel=__channel__,
                     title="[COLOR azure]Nuovi Episodi Serie TV[/COLOR]",
                     action="nuoviep",
                     url="%s/aggiornamenti-serie/" % host,
                     thumbnail="http://www.ilmioprofessionista.it/wp-content/uploads/2015/04/TVSeries3.png"),
                Item(channel=__channel__,
                     title="[COLOR azure]Anime[/COLOR]",
                     action="serie",
                     url="%s/anime/" % host,
                     thumbnail="http://orig09.deviantart.net/df5a/f/2014/169/2/a/fist_of_the_north_star_folder_icon_by_minacsky_saya-d7mq8c8.png"),
                Item(channel=__channel__,
                     title="[COLOR yellow]Cerca...[/COLOR]",
                     action="search",
                     extra="movie",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def newest(categoria):
    logger.info("kod.ilgeniodellostreaming newest" + categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "film":
            item.url = "%s/film/" % host
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
    logger.info("kod.ilgeniodellostreaming categorias")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, '<ul class="genres scrolling">(.*?)</ul>')

    # Estrae i contenuti 
    patron = '<li[^>]+><a href="(.*?)"[^>]+>(.*?)</a>'
    matches = re.compile(patron, re.DOTALL).findall(bloque)

    for scrapedurl, scrapedtitle in matches:
        logger.info("title=[" + scrapedtitle + "]")
        itemlist.append(
            Item(channel=__channel__,
                 action="peliculas",
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png",
                 folder=True))

    return itemlist


def search(item, texto):
    logger.info("[ilgeniodellostreaming.py] " + item.url + " search " + texto)
    item.url = host + "/?s=" + texto

    try:
        return peliculas_src(item)

    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)

    return []


def peliculas_src(item):
    logger.info("kod.ilgeniodellostreaming peliculas")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data

    patron = '<div class="thumbnail animation-2"><a href="(.*?)"><img src="(.*?)" alt="(.*?)" />[^>]+>(.*?)</span>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedtipo in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        logger.info("title=[" + scrapedtitle + "], url=[" + scrapedurl + "], thumbnail=[" + scrapedthumbnail + "]")

        if scrapedtipo == "TV":
            itemlist.append(
                Item(channel=__channel__,
                     action="episodios",
                     fulltitle=scrapedtitle,
                     show=scrapedtitle,
                     title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                     url=scrapedurl,
                     thumbnail=scrapedthumbnail,
                     folder=True))
        else:
            itemlist.append(
                Item(channel=__channel__,
                     action="findvideos",
                     contentType="movie",
                     fulltitle=scrapedtitle,
                     show=scrapedtitle,
                     title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                     url=scrapedurl,
                     thumbnail=scrapedthumbnail,
                     folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def peliculas(item):
    logger.info("kod.ilgeniodellostreaming peliculas")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data

    # Estrae i contenuti 
    patron = '<div class="poster">\s*<a href="([^"]+)"><img src="([^"]+)" alt="([^"]+)"></a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        scrapedplot = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(
            Item(channel=__channel__,
                 action="findvideos",
                 contentType="movie",
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 folder=True))

    # Paginazione
    patronvideos = '<span class="current">[^<]+<[^>]+><a href=\'(.*?)\''
    matches = re.compile(patronvideos, re.DOTALL).findall(data)

    if len(matches) > 0:
        scrapedurl = urlparse.urljoin(item.url, matches[0])
        itemlist.append(
            Item(channel=__channel__,
                 action="peliculas",
                 title="[COLOR orange]Successivo >>[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def nuoviep(item):
    logger.info("kod.ilgeniodellostreaming nuoviep")
    itemlist = []

    p = 1
    if '{}' in item.url:
        item.url, p = item.url.split('{}')
        p = int(p)

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data
    #blocco = scrapertools.find_single_match(data,
                                  #  r'<div class="items" style="margin-bottom:0px!important">(.*?)<div class="items" style="margin-bottom:0px!important">')

    # Estrae i contenuti 
    patron = r'<div class="poster"><img src="([^"]+)" alt="([^"]+)">[^>]+><a href="([^"]+)">'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for i, (scrapedthumbnail, scrapedtitle, scrapedurl) in enumerate(matches):
        if (p - 1) * PERPAGE > i: continue
        if i >= p * PERPAGE: break
        scrapedplot = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(
            Item(channel=__channel__,
                 action="findvideos",
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 folder=True))

    if len(matches) >= p * PERPAGE:
        scrapedurl = item.url + '{}' + str(p + 1)
        itemlist.append(
            Item(channel=__channel__,
                 extra=item.extra,
                 action="nuoviep",
                 title="[COLOR orange]Successivo >>[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def serie(item):
    logger.info("kod.ilgeniodellostreaming peliculas")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data

    # Estrae i contenuti 
    patron = '<div class="poster">\s*<a href="([^"]+)"><img src="([^"]+)" alt="([^"]+)"></a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        scrapedplot = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(
            Item(channel=__channel__,
                 action="episodios",
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 folder=True))

    # Paginazione
    patronvideos = '<span class="current">[^<]+<[^>]+><a href=\'(.*?)\''
    matches = re.compile(patronvideos, re.DOTALL).findall(data)

    if len(matches) > 0:
        scrapedurl = urlparse.urljoin(item.url, matches[0])
        itemlist.append(
            Item(channel=__channel__,
                 action="peliculas",
                 title="[COLOR orange]Successivo >>[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def episodios(item):
    logger.info("kod.ilgeniodellostreaming episodios")
    itemlist = []

    patron = '<ul class="episodios">.*?</ul>'

    data = httptools.downloadpage(item.url).data
    matches = re.compile(patron, re.DOTALL).findall(data)

    for match in matches:

        patron = '<li><div class="imagen"><a href="(.*?)">[^>]+>[^>]+>[^>]+><.*?numerando">(.*?)<[^>]+>[^>]+>[^>]+>(.*?)</a>'
        episodi = re.compile(patron, re.DOTALL).findall(match)

        for scrapedurl, scrapednumber, scrapedtitle in episodi:
            n0 = scrapednumber.replace(" ", "")
            n1 = n0.replace("-", "x")

            itemlist.append(Item(channel=__channel__,
                                 action="findvideos",
                                 contentType="episode",
                                 fulltitle=n1 + " " + scrapedtitle,
                                 show=n1 + " " + scrapedtitle,
                                 title=n1 + " [COLOR orange] " + scrapedtitle + "[/COLOR]",
                                 url=scrapedurl,
                                 thumbnail=item.thumbnail,
                                 plot=item.plot,
                                 folder=True))

    if config.get_videolibrary_support() and len(itemlist) != 0:
        itemlist.append(
            Item(channel=__channel__,
                 title=config.get_localized_string(30161),
                 url=item.url,
                 action="add_serie_to_library",
                 extra="episodios",
                 show=item.show))

    return itemlist


def findvideos(item):
    logger.info()

    data = httptools.downloadpage(item.url).data

    patron = '<td><a class="link_a" href="(.*?)" target="_blank">'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for url in matches:
        html = httptools.downloadpage(url).data
        data += str(scrapertools.find_multiple_matches(html, 'window.location.href=\'(.*?)\''))

    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.title + " - " + videoitem.title
        videoitem.fulltitle = item.fulltitle
        videoitem.show = item.show
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = __channel__
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


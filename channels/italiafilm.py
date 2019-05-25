# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per italiafilm
# ----------------------------------------------------------
import re

import urlparse

from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import logger, config

host = "https://www.italia-film.pro"

headers = [['Referer', host]]


def mainlist(item):
    logger.info("[italiafilm.py] mainlist")
    itemlist = [Item(channel=item.channel,
                     title="[COLOR azure]Film - Novita'[/COLOR]",
                     action="peliculas",
                     extra="movie",
                     url="%s/novita-streaming-1/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR azure]Film HD[/COLOR]",
                     action="peliculas",
                     extra="movie",
                     url="%s/category/film-hd/" % host,
                     thumbnail="http://i.imgur.com/3ED6lOP.png"),
                Item(channel=item.channel,
                     title="[COLOR azure]Categorie[/COLOR]",
                     action="categorias",
                     extra="movie",
                     url="%s/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR yellow]Cerca...[/COLOR]",
                     action="search",
                     extra="movie",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search"),
                Item(channel=item.channel,
                     title="[COLOR azure]Serie TV[/COLOR]",
                     action="peliculas_tv",
                     extra="tvshow",
                     url="%s/category/serie-tv/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR azure]Ultime serie TV[/COLOR]",
                     action="pel_tv",
                     extra="tvshow",
                     url="%s/ultimi-telefilm-streaming/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR azure]Ultimi Episodi[/COLOR]",
                     action="latestep",
                     extra="tvshow",
                     url="%s/ultime-serie-tv-streaming/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR yellow]Cerca Serie TV...[/COLOR]",
                     action="search",
                     extra="tvshow",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]
    return itemlist


def newest(categoria):
    itemlist = []
    item = Item()
    try:
        if categoria == "film":
            item.url = "%s/novita-streaming-1/" % host
            item.action = "peliculas"
            item.extra = "movie"
            itemlist = peliculas(item)

            if itemlist[-1].action == "peliculas":
                itemlist.pop()
        elif categoria == "series":
            item.url = "%s/ultime-serie-tv-streaming/" % host
            item.action = "latestep"
            itemlist = latestep(item)

            if itemlist[-1].action == "series":
                itemlist.pop()

    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def categorias(item):
    logger.info("[italiafilm.py] categorias")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    data = scrapertools.find_single_match(data, '<a href=".">Categorie</a>(.*?)</div>')

    patron = '<li[^>]+><a href="([^"]+)">Film([^<]+)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for url, title in matches:
        scrapedtitle = title
        scrapedurl = urlparse.urljoin(item.url, url)

        if scrapedtitle.startswith((" Porno")):
            continue

        scrapedplot = ""
        scrapedthumbnail = ""
        itemlist.append(
            Item(channel=item.channel,
                 action='peliculas',
                 extra=item.extra,
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 folder=True))

    return itemlist


def search(item, texto):
    logger.info("[italiafilm.py] search " + texto)
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


def latestep(item):
    logger.info("[italiafilm.py] latestep")
    itemlist = []

    data = httptools.downloadpage(item.url).data
    blocco = scrapertools.find_single_match(data, r'<li class="section_date">(.*?)<li class="section_date">')
    patron = r'<li class="[^"]+">\s*[^>]+>([^<|^(]+)[^>]+>\s*<a href="([^"]+)"'
    patron += r'[^>]+>[^>]+>[^>]+>(?:[^>]+>[^>]+>|)([^<]+)(?:[^>]+>[^>]+>|)</a>'
    matches = re.compile(patron, re.DOTALL).findall(blocco)

    for scrapedtitle, scrapedurl, scrapedepisode in matches:
        scrapedepisode = scrapertools.decodeHtmlentities(scrapedepisode)
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        completetitle = "%s - %s" % (scrapedtitle, scrapedepisode)

        unsupportedeps = re.compile(r'\d+\-\d+', re.DOTALL).findall(scrapedepisode)
        if len(unsupportedeps) > 0:
            continue

        if 'completa' in scrapedtitle.lower():
            itemlist.append(
                Item(channel=item.channel,
                     action="episodios",
                     title=completetitle,
                     contentSerieName=completetitle,
                     fulltitle=scrapedtitle,
                     url=scrapedurl,
                     folder=True))
        else:
            if 'episodio' not in scrapedepisode:
                replace = re.compile(r'(\d+)x(\d+)')
                ep_pattern = r'%s(.*?(?:<br\s*/>|</p>))' % replace.sub(r'\g<1>&#215;\g<2>', scrapedepisode)
            else:
                ep_pattern = r'%s(.*?(?:<br\s*/>|</p>))' % scrapedepisode

            itemlist.append(
                Item(channel=item.channel,
                     action="findvideos_single_ep",
                     title=completetitle,
                     contentSerieName=completetitle,
                     fulltitle=scrapedtitle,
                     url=scrapedurl,
                     extra=ep_pattern,
                     folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def peliculas(item):
    logger.info("[italiafilm.py] peliculas")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    patron = '<article(.*?)</article>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for match in matches:
        title = scrapertools.find_single_match(match, '<h3[^<]+<a href="[^"]+"[^<]+>([^<]+)</a>')
        title = title.replace("Streaming", "")
        title = scrapertools.decodeHtmlentities(title).strip()
        url = scrapertools.find_single_match(match, '<h3[^<]+<a href="([^"]+)"')
        if 'film-porno' in url: continue
        plot = ""
        thumbnail = scrapertools.find_single_match(match, 'data-echo="([^"]+)"')

        itemlist.append(
            Item(channel=item.channel,
                 extra=item.extra,
                 action='findvideos',
                 contentType="movie",
                 fulltitle=title,
                 show=title,
                 title="[COLOR azure]" + title + "[/COLOR]",
                 url=url,
                 thumbnail=thumbnail,
                 plot=plot,
                 viewmode="movie_with_plot",
                 folder=True))

    # Pagina successiva
    try:
        pagina_siguiente = scrapertools.find_single_match(data, '<a class="next page-numbers" href="([^"]+)"')
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 extra=item.extra,
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=pagina_siguiente,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))
    except:
        pass

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def findvid(item):
    logger.info("kod.italiafilm findvid")

    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data
    
    # Estrae i contenuti redirect
    urls = scrapertools.find_multiple_matches(data, '<a href="([^"]+)" target="_blank" rel="noopener">')   #
    for url in urls:                                                                                       #   Fix
        page = httptools.downloadpage(url, headers=headers).data                                           #
        data += '\n' + scrapertools.find_single_match(page,'<meta name="og:url" content="([^=]+)">')       #
        

    for videoitem in servertools.find_video_items(data=data):
        videoitem.title = item.title + videoitem.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.show = item.show
        videoitem.plot = item.plot
        videoitem.channel = item.channel
        videoitem.contentType = item.contentType
        itemlist.append(videoitem)

    return itemlist


def peliculas_tv(item):
    logger.info("[italiafilm.py] peliculas")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    patron = '<article(.*?)</article>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for match in matches:
        title = scrapertools.find_single_match(match, '<h3[^<]+<a href="[^"]+"[^<]+>([^<]+)</a>')
        title = title.replace("Streaming", "")
        title = scrapertools.decodeHtmlentities(title).strip()
        show_title = re.sub('\(.*?\)', '', title.replace('Serie TV', ''))
        url = scrapertools.find_single_match(match, '<h3[^<]+<a href="([^"]+)"')
        plot = ""
        thumbnail = scrapertools.find_single_match(match, 'data-echo="([^"]+)"')

        itemlist.append(
            Item(channel=item.channel,
                 extra=item.extra,
                 action='episodios',
                 fulltitle=title,
                 show=show_title,
                 title="[COLOR azure]" + title + "[/COLOR]",
                 url=url,
                 thumbnail=thumbnail,
                 plot=plot,
                 viewmode="movie_with_plot",
                 folder=True))

    # Successivo
    try:
        pagina_siguiente = scrapertools.find_single_match(data, '<a class="next page-numbers" href="([^"]+)"')
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas_tv",
                 extra=item.extra,
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=pagina_siguiente,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))
    except:
        pass

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def pel_tv(item):
    logger.info("[italiafilm.py] peliculas")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    patron = '<span class="tvseries_name">(.*?)</span>\s*<a href="([^"]+)"[^>]+><i class="icon-link"></i>(.*?)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scraptitle1, scrapedurl, scraptitle2 in matches:
        title = scraptitle1 + scraptitle2
        plot = ""
        thumbnail = ""
        url = scrapedurl

        itemlist.append(
            Item(channel=item.channel,
                 extra=item.extra,
                 action='episodios',
                 fulltitle=title,
                 show=title,
                 title="[COLOR azure]" + title + "[/COLOR]",
                 url=url,
                 thumbnail=thumbnail,
                 plot=plot,
                 viewmode="movie_with_plot",
                 folder=True))

    # Siguiente
    try:
        pagina_siguiente = scrapertools.find_single_match(data, '<a class="next page-numbers" href="([^"]+)"')
        itemlist.append(
            Item(channel=item.channel,
                 action="pel_tv",
                 extra=item.extra,
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=pagina_siguiente,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))
    except:
        pass

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def episodios(item):
    def load_episodios(html, item, itemlist, lang_title):
        for data in scrapertools.decodeHtmlentities(html).splitlines():
            # Estrae i contenuti 
            end = data.find('<a ')
            if end > 0:
                scrapedtitle = re.sub(r'<[^>]*>', '', data[:end]).strip()
            else:
                scrapedtitle = ''
            if scrapedtitle == '':
                patron = '<a.*?href="[^"]+".*?>([^<]+)</a>'
                scrapedtitle = scrapertools.find_single_match(data, patron).strip()
            title = scrapertools.find_single_match(scrapedtitle, '\d+[^\d]+\d+')
            if title == '':
                title = scrapedtitle
            if title != '':
                title = re.sub(r"(\d+)[^\d]+(\d+)", r"\1x\2", title)
                title += " (" + lang_title + ")"
                itemlist.append(
                    Item(channel=item.channel,
                         action="findvideos",
                         contentType="episode",
                         title=title,
                         url=data,
                         thumbnail=item.thumbnail,
                         extra=item.extra,
                         fulltitle=title + ' - ' + item.show,
                         show=item.show))

    logger.info("[italiafilm.py] episodios")

    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data.replace('<br>','\n') # fix

    start = data.find('id="pd_rating_holder')
    end = data.find('id="linkcorrotto-show"', start)

    data = data[start:end]

    lang_titles = []
    starts = []
    patron = r"STAGION[I|E](.*?ITA)?"
    matches = re.compile(patron, re.IGNORECASE).finditer(data)
    for match in matches:
        season_title = match.group()
        # if season_title != '':
        lang_titles.append('SUB ITA' if 'SUB' in season_title.upper() else 'ITA')
        starts.append(match.end())

    i = 1
    len_lang_titles = len(lang_titles)

    while i <= len_lang_titles:
        inizio = starts[i - 1]
        fine = starts[i] if i < len_lang_titles else -1

        html = data[inizio:fine]
        lang_title = lang_titles[i - 1]

        load_episodios(html, item, itemlist, lang_title)

        i += 1

    if len(itemlist) == 0:
        load_episodios(data, item, itemlist, 'ITA')

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
    logger.info("kod.italiafilm findvideos")

    if item.contentType == "movie":
        return findvid(item)

    # Carica la pagina 
    data = item.url

    urls = scrapertools.find_multiple_matches(data, '<a.*?href="([^"]+)".*?>')                             #
    for url in urls:                                                                                       #   Fix
        page = httptools.downloadpage(url, headers=headers).data                                           #
        data += '\n' + scrapertools.find_single_match(page,'<meta name="og:url" content="([^=]+)">')       #

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


def findvideos_single_ep(item):
    logger.info("[italiafilm.py] findvideos_single_ep")

    data = httptools.downloadpage(item.url).data

    data = scrapertools.find_single_match(data, item.extra)

    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        server = re.sub(r'[-\[\]\s]+', '', videoitem.title)
        videoitem.title = "".join(["[[COLOR orange]%s[/COLOR]] " % server.capitalize(), item.title])
        videoitem.fulltitle = item.fulltitle
        videoitem.show = item.show
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel

    return itemlist

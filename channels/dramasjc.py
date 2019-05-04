# -*- coding: utf-8 -*-
# -*- Channel DramasJC -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import urllib
from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channels import autoplay
from channels import filtertools


host = 'https://www.dramasjc.com/'

IDIOMAS = {'VOSE': 'VOSE', 'VO':'VO'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['okru', 'mailru', 'openload']

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()
    itemlist.append(Item(channel=item.channel, title="Doramas", action="menu_doramas",
                         thumbnail=get_thumb('doramas', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Películas", action="list_all", url=host+'peliculas/',
                         type='movie', thumbnail=get_thumb('movies', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host+'?s=',
                               thumbnail=get_thumb('search', auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def menu_doramas(item):
    logger.info()

    itemlist = []

    itemlist.append(Item(channel=item.channel, title="Todos", action="list_all", url=host + 'series',
                         thumbnail=get_thumb('all', auto=True)))
    itemlist.append(Item(channel=item.channel, title="Generos", action="section",
                         thumbnail=get_thumb('genres', auto=True)))

    return itemlist

def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data


def list_all(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)
    full_data = data
    data = scrapertools.find_single_match(data, '<ul class="MovieList NoLmtxt.*?>(.*?)</ul>')

    patron = '<article id="post-.*?<a href="([^"]+)">.*?(?:<img |-)src="([^"]+)".*?alt=".*?'
    patron += '<h3 class="Title">([^<]+)<\/h3>.?(?:</a>|<span class="Year">(\d{4})<\/span>).*?'
    patron += '(movie|TV)'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedthumbnail, scrapedtitle, year, type in matches:

        url = scrapedurl
        if year == '':
            year = '-'
        if "|" in scrapedtitle:
            scrapedtitle= scrapedtitle.split("|")
            contentname = scrapedtitle[0].strip()
        else:
            contentname = scrapedtitle

        contentname = re.sub('\(.*?\)','', contentname)

        title = '%s [%s]'%(contentname, year)
        thumbnail = 'http:'+scrapedthumbnail
        new_item = Item(channel=item.channel,
                        title=title,
                        url=url,
                        thumbnail=thumbnail,
                        infoLabels={'year':year}
                        )

        if type == 'movie':
            new_item.contentTitle = contentname
            new_item.action = 'findvideos'
        else:
            new_item.contentSerieName = contentname
            new_item.action = 'seasons'
        itemlist.append(new_item)
    tmdb.set_infoLabels_itemlist(itemlist, True)

    #  Paginación

    url_next_page = scrapertools.find_single_match(full_data,'<a class="next.*?href="([^"]+)">')
    if url_next_page:
        itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=url_next_page, action='list_all'))
    return itemlist

def section(item):
    logger.info()
    itemlist = []

    full_data = get_source(host)
    data = scrapertools.find_single_match(full_data, '<a href="#">Dramas por Genero</a>(.*?)</ul>')
    patron = '<a href="([^ ]+)">([^<]+)<'
    action = 'list_all'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for data_one, data_two in matches:

        url = data_one
        title = data_two
        new_item = Item(channel=item.channel, title= title, url=url, action=action)
        itemlist.append(new_item)

    return itemlist


def seasons(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    patron = 'class="Title AA-Season On" data-tab="1">Temporada <span>([^<]+)</span>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for temporada in matches:
        title = 'Temporada %s' % temporada
        contentSeasonNumber = temporada
        item.infoLabels['season'] = contentSeasonNumber
        itemlist.append(item.clone(action='episodesxseason',
                                   title=title,
                                   contentSeasonNumber=contentSeasonNumber
                                   ))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'episodios':
        itemlist.append(Item(channel=item.channel,
                             title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]',
                             url=item.url,
                             action="add_serie_to_library",
                             extra="episodios",
                             contentSerieName=item.contentSerieName,
                             contentSeasonNumber=contentSeasonNumber
                             ))

    return itemlist

def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseason(tempitem)

    return itemlist


def episodesxseason(item):
    logger.info()

    itemlist = []
    season = item.contentSeasonNumber
    data = get_source(item.url)
    data = scrapertools.find_single_match(data, '>Temporada <span>%s</span>(.*?)</ul>' % season)
    patron = '<a href="([^"]+)">([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    ep = 1
    for scrapedurl, scrapedtitle in matches:
        epi = str(ep)
        title = season + 'x%s - Episodio %s' % (epi, epi)
        url = scrapedurl
        contentEpisodeNumber = epi
        item.infoLabels['episode'] = contentEpisodeNumber
        if 'próximamente' not in scrapedtitle.lower():
            itemlist.append(item.clone(action='findvideos',
                                       title=title,
                                       url=url,
                                       contentEpisodeNumber=contentEpisodeNumber,
                                       ))
        ep += 1
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

def findvideos(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)
    data = scrapertools.unescape(data)
    data = scrapertools.decodeHtmlentities(data)

    # patron = 'id="(Opt\d+)">.*?src="([^"]+)" frameborder.*?</iframe>'
    patron = 'id="(Opt\d+)">.*?src="(?!about:blank)([^"]+)" frameborder.*?</iframe>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for option, scrapedurl in matches:
        scrapedurl = scrapedurl.replace('"','').replace('&#038;','&')
        data_video = get_source(scrapedurl)
        url = scrapertools.find_single_match(data_video, '<div class="Video">.*?src="([^"]+)"')
        opt_data = scrapertools.find_single_match(data,'"%s"><span>.*?</span>.*?<span>([^<]+)</span>'%option).split('-')
        language = opt_data[0].strip()
        quality = opt_data[1].strip()
        if 'sub' in language.lower():
            language='VOSE'
        else:
            language = 'VO'
        if url != '' and 'youtube' not in url:
            itemlist.append(Item(channel=item.channel, title='%s', url=url, language=IDIOMAS[language], quality=quality,
                                 action='play'))
        elif 'youtube' in url:
            trailer = Item(channel=item.channel, title='Trailer', url=url, action='play', server='youtube')

    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % '%s [%s] [%s]'%(i.server.capitalize(),
                                                                                              i.language, i.quality))
    try:
        itemlist.append(trailer)
    except:
        pass

    # Requerido para FilterTools
    # itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]', url=item.url,
                 action="add_pelicula_to_library", extra="findvideos", contentTitle=item.contentTitle))


    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto

    if texto != '':
        return list_all(item)
    else:
        return []

def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas']:
            item.url = host+'peliculas/'

        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist

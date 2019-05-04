# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Filmsenzalimiti
# ------------------------------------------------------------
import base64
import re
import urlparse

from channelselector import get_thumb
from channels import autoplay
from channels import filtertools, support
from core import scrapertools, servertools, httptools
from platformcode import logger, config
from core.item import Item
from platformcode import config
from core import tmdb

__channel__ = 'filmsenzalimiti'

host = 'https://filmsenzalimiti.space'

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['verystream', 'openload', 'streamango', 'vidoza', 'okru']
list_quality = ['1080p', '720p', '480p', '360']

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'filmsenzalimiti')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'filmsenzalimiti')

headers = [['Referer', host]]


def mainlist(item):
    logger.info('[filmsenzalimiti.py] mainlist')

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = [Item(channel=item.channel,
                     action='video',
                     title='Film',
                     contentType='movie',
                     url=host,
                     thumbnail= ''),
                Item(channel=item.channel,
                     action='video',
                     title='Novità',
                     contentType='movie',
                     url=host + '/category/nuove-uscite',
                     thumbnail=''),
                Item(channel=item.channel,
                     action='video',
                     title='In Sala',
                     contentType='movie',
                     url=host + '/category/in-sala',
                     thumbnail=''),
                Item(channel=item.channel,
                     action='video',
                     title='Sottotitolati',
                     contentType='movie',
                     url=host + '/category/sub-ita',
                     thumbnail=''),
                Item(channel=item.channel,
                     action='sottomenu',
                     title='[B]Categoria[/B]',
                     contentType='movie',
                     url=host,
                     thumbnail=''),
                Item(channel=item.channel,
                     action='search',
                     extra='tvshow',
                     title='[B]Cerca...[/B]',
                     contentType='movie',
                     thumbnail='')]

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def search(item, texto):
    logger.info('[filmsenzalimiti.py] search')

    item.url = host + '/?s=' + texto

    try:
        return cerca(item)

    # Continua la ricerca in caso di errore .
    except:
        import sys
        for line in sys.exc_info():
            logger.error('%s' % line)
        return []


def sottomenu(item):
    logger.info('[filmsenzalimiti.py] sottomenu')
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = '<li class="cat-item.*?<a href="([^"]+)">(.*?)<'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action='video',
                 title=scrapedtitle,
                 url=scrapedurl))

    # Elimina Film dal Sottomenù
    itemlist.pop(0)

    return itemlist


def video(item):
    logger.info('[filmsenzalimiti.py] video')
    itemlist = []

    patron = '<div class="col-mt-5 postsh">.*?<a href="([^"]+)" title="([^"]+)">.*?<span class="rating-number">(.*?)<.*?<img src="([^"]+)"'
    patronNext = '<a href="([^"]+)"><i class="glyphicon glyphicon-chevron-right"'

    support.scrape(item, itemlist, patron, ['url', 'title', 'rating', 'thumb'], patronNext=patronNext)

    return itemlist

def cerca(item):
    logger.info('[filmsenzalimiti.py] cerca')
    itemlist = []

    data = httptools.downloadpage(item.url).data.replace('\t','').replace('\n','')
    logger.info('[filmsenzalimiti.py] video' +data)

    patron = '<div class="list-score">(.*?)<.*?<a href="([^"]+)" title="([^"]+)"><img src="([^"]+)"'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedrating, scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        scrapedthumbnail = httptools.get_url_headers(scrapedthumbnail)
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        scrapedrating = scrapertools.decodeHtmlentities(scrapedrating)

        itemlist.append(
            Item(channel=item.channel,
                 action='findvideos',
                 title=scrapedtitle + ' (' + scrapedrating + ')',
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 show=scrapedtitle,
                 contentType=item.contentType,
                 thumbnail=scrapedthumbnail), tipo='movie')

    patron = '<a href="([^"]+)"><i class="glyphicon glyphicon-chevron-right"'
    next_page = scrapertools.find_single_match(data, patron)
    if next_page != '':
        itemlist.append(
            Item(channel=item.channel,
                 action='video',
                 title='[COLOR lightgreen]' + config.get_localized_string(30992) + '[/COLOR]',
                 contentType=item.contentType,
                 url=next_page))

    return itemlist


def findvideos(item):
    logger.info('[filmsenzalimiti.py] findvideos')

    itemlist = support.hdpass_get_servers(item)

   # Link Aggiungi alla Libreria
    if item.contentType == 'movie':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findservers':
            itemlist.append(
                Item(channel=item.channel, title='[COLOR lightblue][B]Aggiungi alla videoteca[/B][/COLOR]', url=item.url,
                     action="add_pelicula_to_library", extra="findservers", contentTitle=item.contentTitle))

    #Necessario per filtrare i Link
    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)

    # Necessario per  FilterTools
    # itemlist = filtertools.get_links(itemlist, item, list_language)

    # Necessario per  AutoPlay
    autoplay.start(itemlist, item)

    return itemlist


def play(item):
    itemlist = servertools.find_video_items(data=item.url)

    return itemlist

def newest(categoria):
    logger.info('[filmsenzalimiti.py] newest' + categoria)
    itemlist = []
    item = Item()
    try:

        ## cambiare i valori 'peliculas, infantiles, series, anime, documentales por los que correspondan aqui en
        # nel py e nel json ###
        if categoria == 'peliculas':
            item.url = host
            itemlist = video(item)

            if 'Successivo>>' in itemlist[-1].title:
                itemlist.pop()

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error('{0}'.format(line))
        return []

    return itemlist

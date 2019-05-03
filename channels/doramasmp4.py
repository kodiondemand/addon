# -*- coding: utf-8 -*-
# -*- Channel DoramasMP4 -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re

from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import jsontools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb

host = 'https://www4.doramasmp4.com/'

IDIOMAS = {'sub': 'VOSE', 'VO': 'VO'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['verystream', 'openload', 'streamango', 'netutv', 'okru', 'directo', 'mp4upload']

def get_source(url, referer=None):
    logger.info()
    if referer is None:
        data = httptools.downloadpage(url).data
    else:
        data = httptools.downloadpage(url, headers={'Referer':referer}).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = []

    itemlist.append(Item(channel= item.channel, title="Doramas", action="doramas_menu",
                         thumbnail=get_thumb('doramas', auto=True), type='dorama'))

    itemlist.append(Item(channel=item.channel, title="Variedades", action="list_all",
                         url=host + 'catalogue?format%5B%5D=varieties&sort=latest',
                         thumbnail='', type='dorama'))

    itemlist.append(Item(channel=item.channel, title="Películas", action="list_all",
                         url=host + 'catalogue?format%5B%5D=movie&sort=latest',
                         thumbnail=get_thumb('movies', auto=True), type='movie'))
    itemlist.append(Item(channel=item.channel, title = 'Buscar', action="search", url= host+'search?s=',
                         thumbnail=get_thumb('search', auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist

def doramas_menu(item):
    logger.info()

    itemlist =[]

    itemlist.append(Item(channel=item.channel, title="Todas", action="list_all",
                         url=host + 'catalogue?format%5B%5D=drama&sort=latest', thumbnail=get_thumb('all', auto=True),
                         type='dorama'))
    itemlist.append(Item(channel=item.channel, title="Nuevos capitulos", action="latest_episodes",
                         url=host + 'latest-episodes', thumbnail=get_thumb('new episodes', auto=True), type='dorama'))
    return itemlist

def list_all(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)

    patron = '<div class="col-lg-2 col-md-3 col-6 mb-3"><a href="([^"]+)".*?<img src="([^"]+)".*?'
    patron += 'txt-size-12">(\d{4})<.*?text-truncate">([^<]+)<.*?description">([^<]+)<.*?'

    matches = re.compile(patron, re.DOTALL).findall(data)

    media_type = item.type
    for scrapedurl, scrapedthumbnail, year, scrapedtitle, scrapedplot in matches:
        url = scrapedurl
        scrapedtitle = scrapedtitle
        thumbnail = scrapedthumbnail
        new_item = Item(channel=item.channel, title=scrapedtitle, url=url,
                        thumbnail=thumbnail, type=media_type, infoLabels={'year':year})
        if media_type != 'dorama':
            new_item.action = 'findvideos'
            new_item.contentTitle = scrapedtitle
            new_item.type = item.type

        else:
            new_item.contentSerieName=scrapedtitle
            new_item.action = 'episodios'
        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    # Paginacion

    if itemlist != []:
        next_page = scrapertools.find_single_match(data, '<a href="([^"]+)" aria-label="Netx">')
        if next_page != '':
            itemlist.append(Item(channel=item.channel, action="list_all", title='Siguiente >>>',
                                 url=host+'catalogue'+next_page, thumbnail='https://s16.postimg.cc/9okdu7hhx/siguiente.png',
                                 type=item.type))
    return itemlist

def latest_episodes(item):
    logger.info()
    itemlist = []
    infoLabels = dict()
    data = get_source(item.url)
    patron = 'shadow-lg rounded" href="([^"]+)".*?src="([^"]+)".*?style="">([^<]+)<.*?>Capítulo (\d+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedep in matches:

        title = '%s %s' % (scrapedtitle, scrapedep)
        contentSerieName = scrapedtitle
        itemlist.append(Item(channel=item.channel, action='findvideos', url=scrapedurl, thumbnail=scrapedthumbnail,
                             title=title, contentSerieName=contentSerieName, type='episode'))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    data = get_source(item.url)
    patron = '<a itemprop="url".*?href="([^"]+)".*?title="(.*?) Cap.*?".*?>Capítulo (\d+)<'

    matches = re.compile(patron, re.DOTALL).findall(data)
    infoLabels = item.infoLabels

    for scrapedurl, scrapedtitle, scrapedep in matches:
        url = scrapedurl
        contentEpisodeNumber = scrapedep

        infoLabels['season'] = 1
        infoLabels['episode'] = contentEpisodeNumber

        if scrapedtitle != '':
            title = '%sx%s - %s' % ('1',scrapedep, scrapedtitle)
        else:
            title = 'episodio %s' % scrapedep

        infoLabels = item.infoLabels

        itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url,
                             contentEpisodeNumber=contentEpisodeNumber, type='episode', infoLabels=infoLabels))


    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            item.clone(title="Añadir esta serie a la videoteca", action="add_serie_to_library", extra="episodios", text_color='yellow'))
    return itemlist

def findvideos(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    new_dom=scrapertools.find_single_match(data,"var web = { domain: '(.*?)'")
    
    patron = 'link="([^"]+)"'

    matches = re.compile(patron, re.DOTALL).findall(data)

    if '</strong> ¡Este capítulo no tiene subtítulos, solo audio original! </div>' in data:
        language = IDIOMAS['vo']
    else:
        language = IDIOMAS['sub']

    #if item.type !='episode' and '<meta property=article:section content=Pelicula>' not in data:
    # if item.type !='episode' and item.type != 'movie':
    #     item.type = 'dorama'
    #     item.contentSerieName = item.contentTitle
    #     item.contentTitle = ''
    #     return episodios(item)
    # else:

    for video_url in matches:
        headers = {'referer': video_url}
        token = scrapertools.find_single_match(video_url, 'token=(.*)')
        if 'fast.php' in video_url:
            video_url = 'https://player.rldev.in/fast.php?token=%s' % token
            video_data = httptools.downloadpage(video_url, headers=headers).data
            url = scrapertools.find_single_match(video_data, "'file':'([^']+)'")
        else:
            video_url = new_dom+'api/redirect.php?token=%s' % token
            video_data = httptools.downloadpage(video_url, headers=headers, follow_redirects=False).headers
            url = scrapertools.find_single_match(video_data['location'], '\d+@@@(.*?)@@@')



        new_item = Item(channel=item.channel, title='[%s] [%s]', url=url, action='play', language = language)
        itemlist.append(new_item)

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % (x.server.capitalize(), x.language))

    if len(itemlist) == 0 and item.type == 'search':
        item.contentSerieName = item.contentTitle
        item.contentTitle = ''
        return episodios(item)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist


def search(item, texto):
    logger.info()
    import urllib
    itemlist = []
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    item.type = 'search'
    if texto != '':
        try:
            return list_all(item)
        except:
            itemlist.append(item.clone(url='', title='No hay elementos...', action=''))
            return itemlist

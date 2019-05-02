# -*- coding: utf-8 -*-
# -*- Channel Playview -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import urllib
from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb


IDIOMAS = {'Latino':'Lat', 'Español':'Cast', 'Subtitulado':'VOSE'}
list_language = IDIOMAS.values()
list_quality = ['HD 1080p', 'HD 720p', 'DVDRIP', 'CAM']
list_servers = ['verystream', 'openload', 'vidoza', 'clipwatching', 'fastplay', 'flashx', 'gamovideo', 'powvideo', 'streamango',
                'streamcherry', 'rapidvideo']

host = 'https://playview.io/'


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel, title='Películas', action='submenu', type='movie',
                         thumbnail=get_thumb('movies', auto=True)))
    itemlist.append(Item(channel=item.channel, title='Series', action='submenu', type='tvshow',
                         thumbnail=get_thumb('tvshows', auto=True)))
    itemlist.append(Item(channel=item.channel, title='Anime', action='list_all', url=host+'anime-online',
                         type='tvshow', first=0, thumbnail=get_thumb('anime', auto=True)))
    itemlist.append(Item(channel=item.channel, title='Buscar', action='search', url=host+'search/',
                         thumbnail=get_thumb('search', auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def submenu(item):
    logger.info()

    itemlist = []
    if item.type == 'movie':
        itemlist.append(
            Item(channel=item.channel, title='Todas', action='list_all', url=host + 'peliculas-online', type='movie',
                 first=0, thumbnail=get_thumb('all', auto=True)))
        itemlist.append(
            Item(channel=item.channel, title='Generos', action='genres', thumbnail=get_thumb('genres', auto=True)))
    else:
        itemlist.append(
            Item(channel=item.channel, title='Todas', action='list_all', url=host + 'series-online', type='tvshow',
                 first=0, thumbnail=get_thumb('all', auto=True)))
        itemlist.append(
            Item(channel=item.channel, title='Series Animadas', action='list_all', url=host + 'series-animadas-online',
                 type='tvshow', first=0, thumbnail=get_thumb('animacion', auto=True)))

    return itemlist


def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def genres(item):
    logger.info()

    itemlist = []

    data = get_source(host)
    patron = '<li value=(\d+)><a href=(.*?)>(.*?)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for value, url, title in matches:
        if value not in ['1', '4', '22', '23', '24']:
            if value == '20':
                title = 'Familiar'
            itemlist.append(Item(channel=item.channel, title=title, action='list_all', url=url, type='Movie', first=0))


    return sorted(itemlist, key=lambda i: i.title)

def list_all(item):
    logger.info()

    itemlist = []
    next = False

    data = get_source(item.url)
    patron = 'spotlight_container>.*?image lazy data-original=(.*?)>.*?<div class=spotlight_title>(.*?)<'
    patron += '(.*?) sres>(\d{4})<.*?playLink href=(.*?)>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    first = item.first
    last = first+19
    if last > len(matches):
        last = len(matches)
        next = True

    for scrapedthumbnail, scrapedtitle, type_data, year, scrapedurl in matches[first:last]:

        url = scrapedurl
        title = scrapedtitle
        season = scrapertools.find_single_match(type_data, 'class=title-season>Temporada<.*?> (\d+) <')
        episode = scrapertools.find_single_match(type_data, 'class=title-season>Episodio<.*?> (\d+) <')
        if season != '' or episode != '':
            item.type = 'tvshow'
        else:
            item.type = 'movie'

        new_item = Item(channel=item.channel, title=title, url=url, thumbnail=scrapedthumbnail, type=item.type,
                        infoLabels={'year': year})

        if item.type == 'tvshow':
            new_item.action = 'episodios'
            new_item.contentSerieName = scrapedtitle
            season = season.strip()
            episode = episode.strip()
            if season == '':
                if 'Anime' in item.title:
                    season = 1
                else:
                    season = scrapertools.find_single_match(url, '.*?temp-(\d+)')
                new_item.contentSeasonNumber = season
            else:
                new_item.contentSeasonNumber = season

            if episode != '':
                new_item.contentEpisodeNumber = episode

            if season != '' and episode != '':
                new_item.title = '%s %sx%s' % (new_item.title, season, episode)
            elif episode == '':
                new_item.title = '%s Temporada %s' % (new_item.title, season)
        else:
            new_item.action = 'findvideos'
            new_item.contentTitle = scrapedtitle
        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    # Paginación

    if not next:
        url_next_page = item.url
        first = last
    else:
        url_next_page = scrapertools.find_single_match(data, "<a href=([^ ]+) class=page-link aria-label=Next>")
        first = 0

    if url_next_page:
        itemlist.append(item.clone(title="Siguiente >>", url=url_next_page, action='list_all', first=first))
    return itemlist


def get_data(post):
    logger.info()

    post = urllib.urlencode(post)
    data = httptools.downloadpage(host + 'playview', post=post).data

    return data

def episodios(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)
    try:
        id, type = scrapertools.find_single_match(data, 'data-id=(\d+) data-type=(.*?) ')
        post = {'set': 'LoadOptionsEpisode', 'action': 'EpisodeList', 'id': id, 'type': '1'}
        data = get_data(post)
        patron = 'data-episode="(\d+)".*?title="(.*?)"'
        matches = re.compile(patron, re.DOTALL).findall(data)
        infoLabels = item.infoLabels
        for episode, title in matches:
            post = {'set': 'LoadOptionsEpisode', 'action': 'Step1', 'id': id, 'type': '1',
                    'episode': episode}
            season = scrapertools.find_single_match(item.url, '.*?temp-(\d+)')
            if season == '':
                season = 1
            infoLabels['season'] = season
            infoLabels['episode'] = episode
            if title[0].isdigit():
                title = '%sx%s' % (season, title)
            else:
                title = '%sx%s - %s' % (season, episode, title)
            itemlist.append(Item(channel=item.channel, title=title, contentSeasonNumber=season,
                                 contentEpisodeNumber=episode, action='findvideos', post=post, type=item.type,
                                 infoLabels=infoLabels))

        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

        if config.get_videolibrary_support() and len(itemlist) > 0:
            itemlist.append(
                Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                     action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName, ))
    except:
        pass

    return itemlist



def findvideos(item):
    logger.info()
    itemlist = []
    set_mode = 'LoadOptions'
    episode = ''
    if item.type == 'tvshow':
        post = item.post
        id= post['id']
        episode = post['episode']
        type = post['type']
        set_mode = 'LoadOptionsEpisode'

    else:
        data=get_source(item.url)
        try:
            id, type = scrapertools.find_single_match(data, 'data-id=(\d+) data-type=(.*?) ')
            post = {'set': set_mode, 'action': 'Step1', 'id': id, 'type': type}
        except:
            pass

    try:
        data = get_data(post)
        patron = 'data-quality="(.*?)"'
        matches = re.compile(patron, re.DOTALL).findall(data)

        for quality in matches:
            post = {'set': set_mode, 'action': 'Step2', 'id': id, 'type': type, 'quality': quality, 'episode':episode}
            data = get_data(post)
            patron = 'getplayer" data-id="(\d+)"> <h4>(.*?)</h4>.*?title="(.*?)"'
            matches = re.compile(patron, re.DOTALL).findall(data)

            for video_id, language, server in matches:
                post = {'set': set_mode, 'action': 'Step3', 'id': video_id, 'type': type}
                data = get_data(post)
                url = scrapertools.find_single_match(data, '<iframe class="embed.*?src="(.*?)"')
                if 'clipwatching' in url:
                    url = url.replace('https://clipwatching.com/embed-', '')
                title = '%s [%s] [%s]'
                quality = quality.replace('(','').replace(')', '')
                if url != '':
                    itemlist.append(Item(channel=item.channel, title=title, language=IDIOMAS[language], url=url,
                                         action='play', quality=quality, infoLabels=item.infoLabels))
        itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % (i.server.capitalize(), i.quality,
                                                                                   i.language))

        itemlist=sorted(itemlist, key=lambda i: i.language)

        # Requerido para FilterTools

        itemlist = filtertools.get_links(itemlist, item, list_language)

        # Requerido para AutoPlay

        autoplay.start(itemlist, item)

        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos' and type == 'Movie':
            itemlist.append(
                    Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                         url=item.url, action="add_pelicula_to_library", extra="findvideos",
                         contentTitle=item.contentTitle))
        return itemlist
    except:
        return itemlist

def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    item.first = 0

    if texto != '':
        return list_all(item)

def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    item.type = 'movie'
    item.first = 0
    try:
        if categoria == 'peliculas':
            item.url = host + 'peliculas-online'
        elif categoria == 'infantiles':
            item.url = host + 'peliculas-online/animacion'
        elif categoria == 'terror':
            item.url = host + 'peliculas-online/terror'

        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist






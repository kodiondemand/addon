# -*- coding: utf-8 -*-
# -*- Channel Estreno Doramas -*-
# -*- Created for Alfa-addon -*-
# -*- By the BDamian (Based on channels from Alfa Develop Group) -*-

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
import ast

host = 'https://www.estrenosdoramas.net/'

IDIOMAS = {'Latino': 'LAT', 'Vo':'VO', 'Vose': 'VOSE'}
IDIOMA = "no filtrar"
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['verystream', 'openload', 'streamango', 'netutv', 'okru', 'mp4upload']

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

    itemlist.append(Item(channel= item.channel, title="Doramas", action="list_all",
                         url=host + 'category/doramas-online',
                         thumbnail=get_thumb('doramas', auto=True), type='dorama'))

    itemlist.append(Item(channel=item.channel, title="Películas", action="list_all",
                         url=host + 'category/peliculas',
                         thumbnail=get_thumb('movies', auto=True), type='movie'))
    
    itemlist.append(Item(channel=item.channel, title="Últimos capítulos", action="list_all",
                         url=host + 'category/ultimos-capitulos-online',
                         thumbnail=get_thumb('doramas', auto=True), type='movie'))

    itemlist.append(Item(channel=item.channel, title="Por Genero", action="menu_generos",
                         url=host,
                         thumbnail=get_thumb('doramas', auto=True), type='dorama'))

    itemlist.append(Item(channel=item.channel, title="Doblado Latino", action="list_all",
                         url=host + 'category/latino',
                         thumbnail=get_thumb('doramas', auto=True), type='dorama'))

    itemlist.append(Item(channel=item.channel, title = 'Buscar', action="search", url= host+'search/',
                         thumbnail=get_thumb('search', auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def menu_generos(item):
    logger.info()

    data = get_source(item.url)
    data = scrapertools.find_single_match(data, '<div id="genuno">(.*?)</div>')
    
    itemlist = []

    patron = '<li><a.*?href="(.*?)">(.*?)</a>.*?</li>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    media_type = item.type
    for scrapedurl, scrapedtitle in matches:
        new_item = Item(channel=item.channel, title=scrapedtitle, url=scrapedurl, 
                        thumbnail=item.thumbnail, type=item.type, action="list_all")
        itemlist.append(new_item)

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)
    data = scrapertools.find_single_match(data, '<h3 class="widgetitulo">Resultados</h3>.*?<div id="sidebar-wrapper">')
    
    patron = '<div.*?<a href="(.*?)"><img src="(.*?)" alt="(.*?)".*?</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        new_item = Item(channel=item.channel, title=scrapedtitle, url=scrapedurl,
                        thumbnail=scrapedthumbnail)
        if scrapedtitle.startswith("Pelicula") or item.type == "movie":
            new_item.action = 'findvideos'
            new_item.contentTitle = scrapedtitle
        else:
            new_item.contentSerieName=scrapedtitle
            new_item.action = 'episodios'
        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Paginacion
    patron = '<a class="nextpostslink" rel="next" href="(.*?)">'
    matches = re.compile(patron, re.DOTALL).findall(data)

    if matches:
        itemlist.append(Item(channel=item.channel, action="list_all", title='Siguiente >>>',
                             url=matches[0], type=item.type))
    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    data = get_source(item.url)
    
    plot_regex = '(<span class="clms"><b>Nombre.*?)<\/div>'
    plot_match = re.compile(plot_regex, re.DOTALL).findall(data)
    if plot_match:
        plot = scrapertools.htmlclean(plot_match[0].replace('<br />', '\n'))
    
    data = scrapertools.find_single_match(data, '<ul class="lcp_catlist".*?</ul>')
    patron = '<li.*?<a href="(.*?)" title="(.*?)">.*?(\d*?)<\/a>'
    
    matches = re.compile(patron, re.DOTALL).findall(data)
    infoLabels = item.infoLabels

    for scrapedurl, scrapedtitle, scrapedep in matches:
        if item.url == scrapedurl:
            continue
        url = scrapedurl        
        contentEpisodeNumber = scrapedep
        if contentEpisodeNumber == "":
            title = '1xEE - ' + scrapedtitle
        else:
            title = '1x' + ("0" + contentEpisodeNumber)[-2:] + " - " + scrapedtitle
            # title = ("0" + contentEpisodeNumber)[-2:]

        infoLabels['season'] = 1
        infoLabels['episode'] = contentEpisodeNumber
        infoLabels = item.infoLabels

        itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url, plot=plot,
                             contentEpisodeNumber=contentEpisodeNumber, type='episode', infoLabels=infoLabels))

    itemlist.sort(key=lambda x: x.title)
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            item.clone(title="Añadir esta serie a la videoteca", action="add_serie_to_library", extra="episodios", text_color='yellow'))
    return itemlist

def findvideos(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)
    data = scrapertools.find_single_match(data, '<div id="marco-post">.*?<div id="sidebar">')
    data = scrapertools.unescape(data)
    data = scrapertools.decodeHtmlentities(data)
    
    options_regex = '<a href="#tab.*?">.*?<b>(.*?)</b>'
    option_matches = re.compile(options_regex, re.DOTALL).findall(data)

    video_regex = '<iframe.*?src="(.*?)".*?</iframe>'
    video_matches = re.compile(video_regex, re.DOTALL).findall(data)

    # for option, scrapedurl in matches:
    for option, scrapedurl in map(None, option_matches, video_matches):
        if scrapedurl is None:
            continue
        
        scrapedurl = scrapedurl.replace('"','').replace('&#038;','&')
        logger.info(scrapedurl)
        try:
            data_video = get_source(scrapedurl)
        except Exception as e:
            logger.info('Error en url: ' + scrapedurl)
            continue
        
        # logger.info(data_video)

        # Este sitio pone multiples páginas intermedias, cada una con sus reglas.
        source_headers = dict()
        source_headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
        source_headers["X-Requested-With"] = "XMLHttpRequest"
        if scrapedurl.find("https://repro") != 0:
            logger.info("Caso 0: url externa")
            url = scrapedurl
            itemlist.append(Item(channel=item.channel, title=option, url=url, action='play', language=IDIOMA))
        elif scrapedurl.find("pi76823.php") > 0:
            logger.info("Caso 1")
            source_data = get_source(scrapedurl)
            source_regex = 'post\( "(.*?)", { acc: "(.*?)", id: \'(.*?)\', tk: \'(.*?)\' }'
            source_matches = re.compile(source_regex, re.DOTALL).findall(source_data)
            for source_page, source_acc, source_id, source_tk in source_matches:
                source_url = scrapedurl[0:scrapedurl.find("pi76823.php")] + source_page
                source_result = httptools.downloadpage(source_url, 'acc=' + source_acc + '&id=' + 
                                                       source_id + '&tk=' + source_tk, source_headers)
                if source_result.code == 200:
                    source_json = jsontools.load(source_result.data)
                    itemlist.append(Item(channel=item.channel, title=option, url=source_json['urlremoto'], action='play', language=IDIOMA))
        elif scrapedurl.find("pi7.php") > 0:
            logger.info("Caso 2")
            source_data = get_source(scrapedurl)
            source_regex = 'post\( "(.*?)", { acc: "(.*?)", id: \'(.*?)\', tk: \'(.*?)\' }'
            source_matches = re.compile(source_regex, re.DOTALL).findall(source_data)
            for source_page, source_acc, source_id, source_tk in source_matches:
                source_url = scrapedurl[0:scrapedurl.find("pi7.php")] + source_page
                source_result = httptools.downloadpage(source_url, 'acc=' + source_acc + '&id=' + 
                                                       source_id + '&tk=' + source_tk, source_headers)
                if source_result.code == 200:
                    source_json = jsontools.load(source_result.data)
                    itemlist.append(Item(channel=item.channel, title=option, url=source_json['urlremoto'], action='play', language=IDIOMA))
        elif scrapedurl.find("reproducir120.php") > 0:
            logger.info("Caso 3")
            source_data = get_source(scrapedurl)

            videoidn = scrapertools.find_single_match(source_data, 'var videoidn = \'(.*?)\';')
            tokensn = scrapertools.find_single_match(source_data, 'var tokensn = \'(.*?)\';')
            
            source_regex = 'post\( "(.*?)", { acc: "(.*?)"'
            source_matches = re.compile(source_regex, re.DOTALL).findall(source_data)
            for source_page, source_acc in source_matches:
                source_url = scrapedurl[0:scrapedurl.find("reproducir120.php")] + source_page
                source_result = httptools.downloadpage(source_url, 'acc=' + source_acc + '&id=' + 
                                                       videoidn + '&tk=' + tokensn, source_headers)
                if source_result.code == 200:
                    source_json = jsontools.load(source_result.data)
                    urlremoto_regex = "file:'(.*?)'"
                    urlremoto_matches = re.compile(urlremoto_regex, re.DOTALL).findall(source_json['urlremoto'])
                    if len(urlremoto_matches) == 1:
                        itemlist.append(Item(channel=item.channel, title=option, url=urlremoto_matches[0], action='play', language=IDIOMA))
        elif scrapedurl.find("reproducir14.php") > 0:
            logger.info("Caso 4")
            source_data = get_source(scrapedurl)
            
            source_regex = '<div id="player-contenido" vid="(.*?)" name="(.*?)"'
            source_matches = re.compile(source_regex, re.DOTALL).findall(source_data)
            videoidn = source_matches[0][0]
            tokensn = source_matches[0][1]
            
            source_regex = 'post\( "(.*?)", { acc: "(.*?)"'
            source_matches = re.compile(source_regex, re.DOTALL).findall(source_data)
            for source_page, source_acc in source_matches:
                source_url = scrapedurl[0:scrapedurl.find("reproducir14.php")] + source_page
                source_result = httptools.downloadpage(source_url, 'acc=' + source_acc + '&id=' + 
                                                       videoidn + '&tk=' + tokensn, source_headers)
                if source_result.code == 200:
                    source_json = jsontools.load(source_result.data)
                    itemlist.append(Item(channel=item.channel, title=option, url=source_json['urlremoto'], action='play', language=IDIOMA))
        else:
            logger.info("Caso nuevo")      

    itemlist = servertools.get_servers_itemlist(itemlist)

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

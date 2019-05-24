# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Filmi Gratis
# ------------------------------------------------------------
import re

from core import scrapertools, servertools, httptools, tmdb, support
from core.item import Item
from platformcode import logger, config
from specials import autoplay

channel = 'filmigratis'

host = 'https://filmigratis.net'

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['openload', 'streamango', 'vidoza', 'okru']
list_quality = ['1080p', '720p', '480p', '360']

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'filmigratis')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'filmigratis')

headers = [['Referer', host]]

#-----------------------------------------------------------------------------------------------------------------------

def mainlist(item):

    # Main options
    itemlist = []
    support.menu(itemlist, 'Al Cinema bold', 'carousel', host, contentType='movie')
    support.menu(itemlist, 'Film alta definizione bold', 'peliculas', host, contentType='movie', args='film')
    support.menu(itemlist, 'Categorie Film bold', 'categorias_film', host , contentType='movie', args='film')
    support.menu(itemlist, 'Categorie Serie bold', 'categorias_serie', host, contentType='episode', args='serie')
    support.menu(itemlist, '[COLOR blue]Cerca Film...[/COLOR] bold', 'search', host, contentType='movie', args='film')
    support.menu(itemlist, '[COLOR blue]Cerca Serie...[/COLOR] bold', 'search', host, contentType='episode', args='serie')

    autoplay.init(item.channel, list_servers, list_quality)
    autoplay.show_option(item.channel, itemlist)

    return itemlist

#-----------------------------------------------------------------------------------------------------------------------

def carousel(item):
    logger.info('[filmigratis.py] carousel')
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    blocco = scrapertools.find_single_match(data, r'<div class="owl-carousel" id="postCarousel">(.*?)<section class="main-content">')

    patron = r'background-image: url\((.*?)\).*?<h3.*?>(.*?)<.*?<a.*?<a href="(.*?)"'
    matches = re.compile(patron, re.DOTALL).findall(blocco)

    for scrapedthumb, scrapedtitle, scrapedurl, in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action = "findvideos",
                 contentType = item.contentType,
                 title = scrapedtitle,
                 fulltitle = scrapedtitle,
                 url = scrapedurl,
                 thumbnail = scrapedthumb,
                 args=item.args,
                 show = scrapedtitle,))
    return itemlist

#-----------------------------------------------------------------------------------------------------------------------

def peliculas(item):
    logger.info('[filmigratis.py] peliculas')
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    blocco = scrapertools.find_single_match(data, r'<h1>Film streaming ita in alta definizione</h1>(.*?)<div class="content-sidebar">')

    patron = r'<div class="timeline-left-wrapper">.*?<a href="(.*?)".*?src="(.*?)".*?<h3.*?>(.*?)<'
    matches = re.compile(patron, re.DOTALL).findall(blocco)

    for scrapedurl, scrapedthumb, scrapedtitle,  in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action = "findvideos",
                 contentType = item.contentType,
                 title = scrapedtitle,
                 fulltitle = scrapedtitle,
                 url = scrapedurl,
                 thumbnail = scrapedthumb,
                 args=item.args,
                 show = scrapedtitle))

        patron = r'class="nextpostslink".*?href="(.*?)"'
        next_page = scrapertools.find_single_match(data, patron)

        if next_page != "":
            itemlist.append(
                Item(channel=item.channel,
                     action="peliculas",
                     title="[B]" + config.get_localized_string(30992) + "[/B]",
                     args=item.args,
                     url=next_page))

    return itemlist

#-----------------------------------------------------------------------------------------------------------------------

def categorias_film(item):
    logger.info("[filmigratis.py] categorias_film")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    bloque = scrapertools.find_single_match(data, 'CATEGORIES.*?<ul>(.*?)</ul>')

    patron = '<a href="(.*?)">(.*?)<'
    matches = re.compile(patron, re.DOTALL).findall(bloque)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(
            Item(channel=channel,
                 action="peliculas_categorias",
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 args=item.args,
                 thumbnail=""))

    return itemlist
#-----------------------------------------------------------------------------------------------------------------------

def categorias_serie(item):
    logger.info("[filmigratis.py] categorias_serie")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    bloque = scrapertools.find_single_match(data, 'class="material-button submenu-toggle"> SERIE TV.*?<ul>.*?</li>(.*?)</ul>')

    patron = '<a href="(.*?)">(.*?)<'
    matches = re.compile(patron, re.DOTALL).findall(bloque)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(
            Item(channel=channel,
                 contentType='episode',
                 action="peliculas_serie",
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 args=item.args,
                 thumbnail=""))

    return itemlist

#-----------------------------------------------------------------------------------------------------------------------

def peliculas_categorias(item):
    logger.info("[filmigratis.py] peliculas_categorias")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    patron = r'<div class="cnt">.*?src="(.*?)".*?title="([A-Z|0-9].*?)".*?<a href="(.*?)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumb, scrapedtitle, scrapedurl in matches:
        if scrapedtitle == "":
            scrapedtitle = scrapertools.find_single_match(data, r'<small>.*?([A-Z|0-9].*?)		<')
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        scrapedtitle = scrapedtitle.replace ("Ãˆ","È")
        scrapedtitle = scrapedtitle.replace("â€“", "-")
        scrapedtitle = scrapedtitle.replace("â€™", "'")
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentType=item.contentType,
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumb,
                 args=item.args,
                 show=scrapedtitle))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

#-----------------------------------------------------------------------------------------------------------------------

def peliculas_serie(item):
    logger.info("[filmigratis.py] peliculas_serie")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    patron = r'div class="cnt">.*?src="(.*?)".*?title="([A-Z|0-9].*?)".*?<a href="(.*?)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumb, scrapedtitle, scrapedurl in matches:
        if scrapedtitle == "":
            scrapedtitle = scrapertools.find_single_match(data, r'<small>.*?([A-Z|0-9].*?)		<')
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        scrapedtitle = scrapedtitle.replace ("Ãˆ","È")
        scrapedtitle = scrapedtitle.replace("â€“", "-")
        scrapedtitle = scrapedtitle.replace("â€™", "'")
        scrapedtitle = scrapedtitle.replace("		", "")
        itemlist.append(
            Item(channel=item.channel,
                 action="episodios",
                 contentType='episode',
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumb,
                 args=item.args,
                 show=scrapedtitle))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

#-----------------------------------------------------------------------------------------------------------------------

def episodios(item):
    logger.info("[filmigratis.py] episodios")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    block = scrapertools.find_single_match(data, r'<div class="row">(.*?)<section class="main-content">')

    patron = r'href="(.*?)".*?(S[^<]+)												<'
    matches = re.compile(patron, re.DOTALL).findall(block)

    for scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        scrapedtitle = scrapedtitle.replace ("S0", "")
        scrapedtitle = scrapedtitle.replace(" - EP ", "x")
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentType='episode',
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=item.thumb,
                 args=item.args,
                 show=item.title))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    support.videolibrary(itemlist, item, 'color kod')
    return itemlist

#-----------------------------------------------------------------------------------------------------------------------

def search(item, texto):
    logger.info('[filmigratis.py] search')

    item.url = host + '/search/?s=' + texto

    if item.args == 'serie':
        try:
            return peliculas_serie(item)

        except:
            import sys
            for line in sys.exc_info():
                logger.error('%s' % line)
            return []

    else:
        try:
            return peliculas_categorias(item)

        except:
            import sys
            for line in sys.exc_info():
                logger.error('%s' % line)
            return []

#-----------------------------------------------------------------------------------------------------------------------

def findvideos(item):
    logger.info('[filmigratis.py] findvideos')

    data = httptools.downloadpage(item.url, headers=headers).data

    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.title + '[COLOR green][B] - ' + videoitem.title + '[/B][/COLOR]'
        videoitem.fulltitle = item.fulltitle
        videoitem.show = item.show
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
        videoitem.contentType = item.content

    if item.args == "film":
        support.videolibrary(itemlist, item, 'color kod')

    autoplay.start(itemlist, item)

    return itemlist

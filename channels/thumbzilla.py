# -*- coding: utf-8 -*-

import re

import urlparse

from channelselector import get_thumb
from core import channeltools
from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import config, logger

__channel__ = "thumbzilla"

host = 'https://www.thumbzilla.com'
try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
    __perfil__ = int(config.get_setting('perfil', __channel__))
except:
    __modo_grafico__ = True
    __perfil__ = 0

# Fijar perfil de color
perfil = [['0xFF6E2802', '0xFFFAA171', '0xFFE9D7940'],
          ['0xFFA5F6AF', '0xFF5FDA6D', '0xFF11811E'],
          ['0xFF58D3F7', '0xFF2E64FE', '0xFF0404B4']]

if __perfil__ - 1 >= 0:
    color1, color2, color3 = perfil[__perfil__ - 1]
else:
    color1 = color2 = color3 = ""

headers = [['User-Agent', 'Mozilla/50.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'],
           ['Referer', host]]

parameters = channeltools.get_channel_parameters(__channel__)
fanart_host = parameters['fanart']
thumbnail_host = parameters['thumbnail']
thumbnail = 'https://raw.githubusercontent.com/Inter95/tvguia/master/thumbnails/adults/%s.png'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=__channel__, action="videos", title="Más Calientes", url=host,
                         viewmode="movie", thumbnail=get_thumb("channels_adult.png")))

    itemlist.append(Item(channel=__channel__, title="Nuevas", url=host + '/newest',
                         action="videos", viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=get_thumb("channels_adult.png")))

    itemlist.append(Item(channel=__channel__, title="Tendencias", url=host + '/tending',
                         action="videos", viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=get_thumb("channels_adult.png")))

    itemlist.append(Item(channel=__channel__, title="Mejores Videos", url=host + '/top',
                         action="videos", viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=get_thumb("channels_adult.png")))

    itemlist.append(Item(channel=__channel__, title="Populares", url=host + '/popular',
                         action="videos", viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=get_thumb("channels_adult.png")))

    itemlist.append(Item(channel=__channel__, title="Videos en HD", url=host + '/hd',
                         action="videos", viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=get_thumb("channels_adult.png")))

    itemlist.append(Item(channel=__channel__, title="Caseros", url=host + '/hd',
                         action="videos", viewmode="movie_with_plot", viewcontent='homemade',
                         thumbnail=get_thumb("channels_adult.png")))
 
    itemlist.append(Item(channel=__channel__, title="PornStar", action="catalogo",
                         url=host + '/pornstars/', viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=get_thumb("channels_adult.png")))
 
    itemlist.append(Item(channel=__channel__, title="Categorías", action="categorias",
                         url=host + '/categories/', viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=get_thumb("channels_adult.png")))

    itemlist.append(Item(channel=__channel__, title="Buscador", action="search", url=host,
                         thumbnail=get_thumb("channels_adult.png"), extra="buscar"))
    return itemlist


# REALMENTE PASA LA DIRECCION DE BUSQUEDA

def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = urlparse.urljoin(item.url, "video/search?q={0}".format(texto))
    # item.url = item.url % tecleado
    item.extra = "buscar"
    try:
        return videos(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []


def videos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<a class="[^"]+" href="([^"]+)">'  # url
    patron += '<img id="[^"]+".*?src="([^"]+)".*?'  # img
    patron += '<span class="title">([^<]+)</span>.*?'  # title
    patron += '<span class="duration"(.*?)</a>'  # time
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedtime in matches:
        time = scrapertools.find_single_match(scrapedtime, '>([^<]+)</span>')
        title = "[%s] %s" % (time, scrapedtitle)
        if ">HD<" in scrapedtime:
            title = "[COLOR yellow]" + time + "[/COLOR] " + "[COLOR red]" + "HD" + "[/COLOR] " + scrapedtitle
        itemlist.append(Item(channel=item.channel, action='play', title=title, thumbnail=scrapedthumbnail,
                             url=host + scrapedurl, contentTile=scrapedtitle, fanart=scrapedthumbnail))
    paginacion = scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)" />').replace('amp;', '')
    if paginacion:
        itemlist.append(Item(channel=item.channel, action="videos",
                             thumbnail=thumbnail % 'rarrow',
                             title="\xc2\xbb Siguiente \xc2\xbb", url=paginacion))
    return itemlist


def catalogo(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<li class="pornstars">.*?<a href="([^"]+)".*?'
    patron += '<img src="([^"]+)" alt="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        url = urlparse.urljoin(item.url, scrapedurl)
        itemlist.append(Item(channel=item.channel, action="videos", url=url, title=scrapedtitle, fanart=scrapedthumbnail,
                             thumbnail=scrapedthumbnail, viewmode="movie_with_plot"))
    paginacion = scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)" />').replace('amp;', '')
    if paginacion:
        itemlist.append(Item(channel=item.channel, action="catalogo",
                             thumbnail=thumbnail % 'rarrow',
                             title="\xc2\xbb Siguiente \xc2\xbb", url=paginacion))
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    # logger.info(data)
    patron = 'class="checkHomepage"><a href="([^"]+)".*?'  # url
    patron += '<span class="count">([^<]+)</span>'  # title, vids
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, vids in matches:
        scrapedtitle = scrapedurl.replace('/categories/', '').replace('-', ' ').title()
        title = "%s (%s)" % (scrapedtitle, vids.title())
        thumbnail = item.thumbnail
        url = urlparse.urljoin(item.url, scrapedurl)
        itemlist.append(Item(channel=item.channel, action="videos", fanart=thumbnail,
                             title=title, url=url, thumbnail=thumbnail,
                             viewmode="movie_with_plot", folder=True))
    return itemlist


def play(item):
    itemlist = []
    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(data, '"quality":"[^"]+","videoUrl":"([^"]+)"').replace('\\', '')
    itemlist.append(item.clone(url=url, title=item.contentTile))
    return itemlist


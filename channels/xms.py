# -*- coding: utf-8 -*-

import re

import urlparse

from core import channeltools
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger

__channel__ = "xms"

host = 'https://xtheatre.org'
host1 = 'https://www.cam4.com/'
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

    itemlist.append(Item(channel=__channel__, title="Últimas", url=host + '?filtre=date&cat=0',
                         action="peliculas", viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=thumbnail % '1'))

    itemlist.append(Item(channel=__channel__, title="Más Vistas", url=host + '?display=extract&filtre=views',
                         action="peliculas", viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=thumbnail % '2'))

    itemlist.append(Item(channel=__channel__, title="Mejor Valoradas", url=host + '?display=extract&filtre=rate',
                         action="peliculas", viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=thumbnail % '3'))

    itemlist.append(Item(channel=__channel__, title="Categorías", action="categorias",
                         url=host + 'categories/', viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=thumbnail % '4'))

    itemlist.append(Item(channel=__channel__, title="WebCam", action="webcamenu",
                         viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail='https://ae01.alicdn.com/kf/HTB1LDoiaHsrBKNjSZFpq6AXhFXa9/-.jpg'))

    itemlist.append(Item(channel=__channel__, title="Buscador", action="search", url=host, thumbnail=thumbnail % '5'))

    return itemlist


def webcamenu(item):
    logger.info()
    itemlist = [item.clone(title="Trending Cams", action="webcam", text_blod=True, url=host1,
                           viewcontent='movies', viewmode="movie_with_plot"),
                item.clone(title="Females", action="webcam", text_blod=True,
                           viewcontent='movies', url=host1 + 'female', viewmode="movie_with_plot"),
                item.clone(title="Males", action="webcam", text_blod=True,
                           viewcontent='movies', url=host1 + 'male', viewmode="movie_with_plot"),
                item.clone(title="Couples", action="webcam", text_blod=True,
                           viewcontent='movies', url=host1 + 'couple', viewmode="movie_with_plot"),
                item.clone(title="Trans", action="webcam", text_blod=True, extra="Películas Por año",
                           viewcontent='movies', url=host1 + 'transgender', viewmode="movie_with_plot")]
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|#038;", "", data)
    patron = 'src="([^"]+)" class="attachment-thumb_site.*?'  # img
    patron += '<a href="([^"]+)" title="([^"]+)".*?'          # url, title
    patron += '<div class="right"><p>([^<]+)</p>'             # plot
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedurl, scrapedtitle, plot in matches:
        plot = scrapertools.decodeHtmlentities(plot)

        itemlist.append(item.clone(channel=__channel__, action="findvideos", title=scrapedtitle.capitalize(),
                                   url=scrapedurl, thumbnail=scrapedthumbnail, infoLabels={"plot": plot},
                                   fanart=scrapedthumbnail,viewmode="movie_with_plot",
                                   folder=True, contentTitle=scrapedtitle))
    # Extrae el paginador
    paginacion = scrapertools.find_single_match(data, '<a href="([^"]+)">Next &rsaquo;</a></li><li>')
    paginacion = urlparse.urljoin(item.url, paginacion)

    if paginacion:
        itemlist.append(Item(channel=__channel__, action="peliculas",
                             thumbnail=thumbnail % 'rarrow',
                             title="\xc2\xbb Siguiente \xc2\xbb", url=paginacion))

    return itemlist


def webcam(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|#038;", "", data)
    patron = '<div class="profileBox">.*?<a href="/([^"]+)".*?'  # url
    patron += 'data-hls-preview-url="([^"]+)">.*?'               # video_url
    patron += 'data-username="([^"]+)".*?'                       # username
    patron += 'title="([^"]+)".*?'                               # title
    patron += 'data-profile="([^"]+)"'                        # img
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, video_url, username, scrapedtitle, scrapedthumbnail in matches:
        scrapedtitle = scrapedtitle.replace(' Chat gratis con webcam.', '')

        itemlist.append(item.clone(channel=__channel__, action="play", title=username,
                                   url=video_url, thumbnail=scrapedthumbnail, fanart=scrapedthumbnail,
                                   viewmode="movie_with_plot", folder=True, contentTitle=scrapedtitle))
    # Extrae el paginador
    paginacion = scrapertools.find_single_match(data, '<span id="pagerSpan">\d+</span> <a href="([^"]+)"')
    paginacion = urlparse.urljoin(item.url, paginacion)

    if paginacion:
        itemlist.append(Item(channel=__channel__, action="webcam",
                             thumbnail=thumbnail % 'rarrow',
                             title="\xc2\xbb Siguiente \xc2\xbb", url=paginacion))

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = 'data-lazy-src="([^"]+)".*?'                            # img
    patron += '</noscript><a href="([^"]+)".*?'                      # url
    patron += '<span>([^<]+)</span></a>.*?'                          # title
    patron += '<span class="nb_cat border-radius-5">([^<]+)</span>'  # num_vids
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedurl, scrapedtitle, vids in matches:
        title = "%s (%s)" % (scrapedtitle, vids.title())
        itemlist.append(item.clone(channel=__channel__, action="peliculas", fanart=scrapedthumbnail,
                                   title=title, url=scrapedurl, thumbnail=scrapedthumbnail,
                                   viewmode="movie_with_plot", folder=True))

    return itemlist


def search(item, texto):
    logger.info()

    texto = texto.replace(" ", "+")
    item.url = urlparse.urljoin(item.url, "?s={0}".format(texto))

    try:
        return sub_search(item)

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []


def sub_search(item):
    logger.info()

    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = 'data-lazy-src="([^"]+)".*?'          # img
    patron += 'title="([^"]+)" />.*?'              # title
    patron += '</noscript><a href="([^"]+)".*?'    # url
    patron += '<div class="right"><p>([^<]+)</p>'  # plot
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedtitle, scrapedurl, plot in matches:
        itemlist.append(item.clone(title=scrapedtitle, url=scrapedurl, plot=plot, fanart=scrapedthumbnail,
                                   action="findvideos", thumbnail=scrapedthumbnail))

    paginacion = scrapertools.find_single_match(
        data, "<a href='([^']+)' class=\"inactive\">\d+</a>")

    if paginacion:
        itemlist.append(item.clone(channel=__channel__, action="sub_search",
                                   title="\xc2\xbb Siguiente \xc2\xbb", url=paginacion))

    return itemlist


def findvideos(item):
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|amp;|\s{2}|&nbsp;", "", data)
    patron = '<iframe src="[^"]+".*?<iframe src="([^"]+)" scrolling="no" frameborder="0"'
    matches = scrapertools.find_multiple_matches(data, patron)

    for url in matches:
        server = servertools.get_server_from_url(url)
        title = "Ver en: [COLOR yellow](%s)[/COLOR]" % server.title()

        itemlist.append(item.clone(action='play', title=title, server=server, url=url))

    return itemlist

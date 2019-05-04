# -*- coding: UTF-8 -*-

import re
import urlparse

from channelselector import get_thumb
from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger

IDIOMAS = {'Hindi': 'Hindi'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['verystream', 'openload', 'netutv']

host = "http://www.cinehindi.com/"


def mainlist(item):
    logger.info()
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = list()
    itemlist.append(Item(channel=item.channel, action="genero", title="Generos", url=host, thumbnail = get_thumb("genres", auto = True)))
    itemlist.append(Item(channel=item.channel, action="lista", title="Novedades", url=host, thumbnail = get_thumb("newest", auto = True)))
    #itemlist.append(Item(channel=item.channel, action="proximas", title="Próximas Películas",
    #                     url=urlparse.urljoin(host, "proximamente")))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=urlparse.urljoin(host, "?s="), thumbnail = get_thumb("search", auto = True)))
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def genero(item):
    logger.info()
    itemlist = list()
    data = httptools.downloadpage(host).data
    patron  = '<option class=.*? value=([^<]+)>'
    patron += '([^<]+)<\/option>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle in matches:
        if 'Próximas Películas' in scrapedtitle:
            continue
        itemlist.append(item.clone(action='lista', title=scrapedtitle, cat=scrapedurl))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    if texto != '':
        return lista(item)


def proximas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)  # Eliminamos tabuladores, dobles espacios saltos de linea, etc...
    patron = 'class="item">.*?'  # Todos los items de peliculas (en esta web) empiezan con esto
    patron += '<a href="([^"]+).*?'  # scrapedurl
    patron += '<img src="([^"]+).*?'  # scrapedthumbnail
    patron += 'alt="([^"]+).*?'  # scrapedtitle
    patron += '<span class="player">.+?<span class="year">([^"]+)<\/span>'  # scrapedyear
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedyear in matches:
        if "ver" in scrapedurl:
            scrapedtitle = scrapedtitle + " [" + scrapedyear + "]"
        else:
            scrapedtitle = scrapedtitle + " [" + scrapedyear + "]" + '(Proximamente)'
        itemlist.append(item.clone(title=scrapedtitle, url=scrapedurl, action="findvideos", extra=scrapedtitle,
                                   show=scrapedtitle, thumbnail=scrapedthumbnail, contentType="movie",
                                   context=["buscar_trailer"]))
    # Paginacion
    patron_pag = '<a rel=.+?nofollow.+? class=.+?page larger.+? href=.+?(.+?)proximamente.+?>([^"]+)<\/a>'
    pagina = scrapertools.find_multiple_matches(data, patron_pag)
    for next_page_url, i in pagina:
        if int(i) == 2:
            item.url = next_page_url + 'proximamente/page/' + str(i) + '/'
            itemlist.append(Item(channel=item.channel, action="proximas", title=">> Página siguiente", url=item.url,
                                 thumbnail='https://s32.postimg.cc/4zppxf5j9/siguiente.png'))
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    if not item.cat:
        data = httptools.downloadpage(item.url).data
    else:
        url = httptools.downloadpage("%s?cat=%s" %(host, item.cat), follow_redirects=False, only_headers=True).headers.get("location", "")
        data = httptools.downloadpage(url).data
    bloque = data#scrapertools.find_single_match(data, """class="item_1 items.*?id="paginador">""")
    patron = '<div id=mt.+?>'  # Todos los items de peliculas (en esta web) empiezan con esto
    patron += '<a href=([^"]+)\/><div class=image>'  # scrapedurl
    patron += '<img src=([^"]+) alt=.*?'  # scrapedthumbnail
    patron += '<span class=tt>([^"]+)<\/span>' # scrapedtitle
    patron += '<span class=ttx>([^"]+)<div class=degradado>.*?'  # scrapedplot
    patron += '<span class=year>([^"]+)<\/span><\/div><\/div>'  # scrapedfixyear
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedplot, scrapedyear in matches:
        #patron = '<span class="year">([^<]+)'  # scrapedyear
        #scrapedyear = scrapertools.find_single_match(scrapedfixyear, patron)
        scrapedtitle = scrapedtitle.replace(scrapertools.find_single_match(scrapedtitle,'\(\d{4}\)'),'').strip()
        title = scrapedtitle
        if scrapedyear:
            title += ' (%s)' % (scrapedyear)
            item.infoLabels['year'] = int(scrapedyear)
        patron = '<span class="calidad2">([^<]+).*?'  # scrapedquality
        #scrapedquality = scrapertools.find_single_match(scrapedfixyear, patron)
        #if scrapedquality:
        #    title += ' [%s]' % (scrapedquality)
        itemlist.append(
            item.clone(title=title, url=scrapedurl, action="findvideos", extra=scrapedtitle,
                       contentTitle=scrapedtitle, thumbnail=scrapedthumbnail, plot=scrapedplot, contentType="movie", context=["buscar_trailer"]))
    tmdb.set_infoLabels(itemlist)
    # Paginacion
    patron = 'rel="next" href="([^"]+)'
    next_page_url = scrapertools.find_single_match(data, patron)
    if next_page_url != "":
        item.url = next_page_url
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR cyan]Página Siguiente >>[/COLOR]", url=next_page_url,
                             thumbnail='https://s32.postimg.cc/4zppxf5j9/siguiente.png'))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    itemlist1 = []
    data = httptools.downloadpage(item.url).data
    itemlist1.extend(servertools.find_video_items(data=data))
    patron_show = '<div class="data"><h1 itemprop="name">([^<]+)<\/h1>'
    show = scrapertools.find_single_match(data, patron_show)
    for videoitem in itemlist1:
        videoitem.channel = item.channel
        videoitem.infoLabels = item.infoLabels
    for i in range(len(itemlist1)):
        if not 'youtube' in itemlist1[i].title:
            itemlist.append(itemlist1[i])
    tmdb.set_infoLabels(itemlist, True)
    # Requerido para FilterTools
    # itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.contentChannel!='videolibrary':
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]', url=item.url,
                 action="add_pelicula_to_library", extra="findvideos", contentTitle=show))
    return itemlist


def play(item):
    logger.info()
    item.thumbnail = item.contentThumbnail
    return [item]

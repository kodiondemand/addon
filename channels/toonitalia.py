# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per ToonItalia
# ------------------------------------------------------------

import re
import urlparse

from channels import autoplay, filtertools, support
from core import scrapertools, scrapertoolsV2, httptools, tmdb, servertools
from core.item import Item
from platformcode import logger, config

channel = "toonitalia"
host = "https://toonitalia.org"
headers = [['Referer', host]]

list_servers = ['wstream', 'openload', 'streamango']
list_quality = ['HD', 'default']

def mainlist(item):

    # Main options
    itemlist = []
    support.menu(itemlist, 'Ultimi aggiornamenti', 'news', host, contentType='episode')
    support.menu(itemlist, 'Più visti', 'most_view', host, contentType='episode', args="Anime popolari")
    support.menu(itemlist, 'Anime', 'anime_list', host + '/lista-anime-2/', contentType='episode', args="Anime per Lettera")
    support.menu(itemlist, 'Sub-Ita submenu', 'anime_list', host + '/lista-anime-sub-ita/', contentType='episode')
    support.menu(itemlist, 'Serie TV bold', 'anime_list', host + '/lista-serie-tv/', contentType='episode')
    support.menu(itemlist, '[COLOR blue]Cerca anime e serie...[/COLOR] bold', 'search', host + '/serietv/', contentType='episode', args='serie')

    autoplay.init(item.channel, list_servers, list_quality)
    autoplay.show_option(item.channel, itemlist)

    return itemlist

#----------------------------------------------------------------------------------------------------------------------------------------------

def search(item, texto):
    logger.info("[toonitalia.py] " + item.url + " search " + texto)
    item.url = host + "/?s=" + texto
    try:
        return peliculas_search(item)

    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

#----------------------------------------------------------------------------------------------------------------------------------------------

def peliculas_search(item):
    logger.info("[toonitalia.py] peliculas_search")
    itemlist = []
    minpage = 14

    p = 1
    if '{}' in item.url:
        item.url, p = item.url.split('{}')
        p = int(p)

    data = httptools.downloadpage(item.url, headers=headers).data

    patron = r'<h2 class="entry-title"><a href="([^"]+)" rel="bookmark">([^<]+)</a></h2>.*?'
    patron += r'<p>(.*?)</p>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for i, (scrapedurl, scrapedtitle, scrapedplot) in enumerate(matches):
        if (p - 1) * minpage > i: continue
        if i >= p * minpage: break
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)

        itemlist.append(
            Item(channel=channel,
                 action="episodios",
                 contentType="episode",
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 show=scrapedtitle,
                 extra="tv",
                 plot=scrapedplot))

    if len(matches) >= p * minpage:
        scrapedurl = item.url + '{}' + str(p + 1)
        itemlist.append(
            Item(channel=channel,
                 extra=item.extra,
                 action="peliculas_search",
                 title="[COLOR blue][B]Successivo >[/B][/COLOR]",
                 url=scrapedurl))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

#----------------------------------------------------------------------------------------------------------------------------------------------

def most_view(item):
    logger.info("[toonitalia.py] most_view")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    blocco = r'I piu visti</h2>(.*?)</ul>'
    matches = re.compile(blocco, re.DOTALL).findall(data)
    for scrapedurl in matches:
        blocco = scrapedurl

    patron = r'<a href="([^"]+)" title="[^"]+" class="wpp-post-title" target="_self">([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(blocco)

    for scrapedurl, scrapedtitle in matches:
        scrapedthumbnail = ""
        scrapedplot = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(
            Item(channel=channel,
                 action="peliculas_server",
                 contentType="tv",
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 show=scrapedtitle,
                 extra="tv",
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot))

    return itemlist

#----------------------------------------------------------------------------------------------------------------------------------------------

def news(item):
    logger.info("[toonitalia.py] news")
    itemlist = []
    minpage = 14

    p = 1
    if '{}' in item.url:
        item.url, p = item.url.split('{}')
        p = int(p)

    data = httptools.downloadpage(item.url, headers=headers).data

    patron = r'<h2 class="entry-title"><a href="([^"]+)" rel="bookmark">([^<]+)</a></h2>.*?'
    patron += r'<p class[^>]+><a href="[^"]+"><img width[^>]+src="([^"]+)" class[^>]+>.*?'
    patron += r'<p>(.*?)<\/p>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for i, (scrapedurl, scrapedtitle, scrapedthumbnail, scrapedplot) in enumerate(matches):
        if (p - 1) * minpage > i: continue
        if i >= p * minpage: break
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)

        itemlist.append(
            Item(channel=channel,
                 action="peliculas_server",
                 contentType="tv",
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 show=scrapedtitle,
                 extra="tv",
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 folder=True))

    if len(matches) >= p * minpage:
        scrapedurl = item.url + '{}' + str(p + 1)
        itemlist.append(
            Item(channel=channel,
                 extra=item.extra,
                 action="news",
                 title="[COLOR blue][B]Successivo >[/B][/COLOR]",
                 url=scrapedurl,
                 thumbnail="thumb_next.png",
                 folder=True))

    return itemlist

#----------------------------------------------------------------------------------------------------------------------------------------------

def anime_list(item):
    logger.info("[toonitalia.py] anime_list")
    itemlist = []
    minpage = 14

    p = 1
    if '{}' in item.url:
        item.url, p = item.url.split('{}')
        p = int(p)

    data = httptools.downloadpage(item.url, headers=headers).data

    patron = r'<li ><a href="([^"]+)" title="[^>]+">([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for i, (scrapedurl, scrapedtitle) in enumerate(matches):
        if (p - 1) * minpage > i: continue
        if i >= p * minpage: break
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        scrapedthumbnail = ""
        scrapedplot = ""
        itemlist.append(
            Item(channel=channel,
                 action="peliculas_server",
                 contentType="tv",
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 show=scrapedtitle,
                 extra="tv",
                 plot=scrapedplot,
                 thumbnail=scrapedthumbnail,
                 folder=True))

    if len(matches) >= p * minpage:
        scrapedurl = item.url + '{}' + str(p + 1)
        itemlist.append(
            Item(channel=channel,
                 extra=item.extra,
                 action="anime_list",
                 title="[COLOR blue][B]Successivo >[/B][/COLOR]",
                 url=scrapedurl,
                 folder=True))

    return itemlist

#----------------------------------------------------------------------------------------------------------------------------------------------

def episodios(item):
    logger.info("[toonitalia.py] episodios")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    patron = r'<br /> <a href="([^"]+)"\s*target="_blank"\s*rel[^>]+>([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        if 'Wikipedia' not in scrapedurl:
            scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).replace("×", "x")
            scrapedtitle = scrapedtitle.replace("_", " ")
            scrapedtitle = scrapedtitle.replace(".mp4", "")
            itemlist.append(
                Item(channel=channel,
                     action="findvideos",
                     contentType="tv",
                     title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                     thumbnail=item.thumbnail,
                     fulltitle=scrapedtitle,
                     url=scrapedurl,
                     show=item.show,
                     plot=item.plot,
                     extra="tv"))

    patron = r'<a href="([^"]+)"\s*target="_blank"[^>]+>[^>]+>[^>]+>[^>]+>\s*[^>]+>([^<]+)[^>]+>'
    matches = re.compile(patron, re.DOTALL).findall(item.url)

    for scrapedurl, scrapedtitle in matches:
        if 'Wikipedia' not in scrapedurl:
            scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).replace("×", "x")
            scrapedtitle = scrapedtitle.replace("_", " ")
            scrapedtitle = scrapedtitle.replace(".mp4", "")
            itemlist.append(
                Item(channel=channel,
                     action="findvideos",
                     contentType="tv",
                     title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                     fulltitle=scrapedtitle,
                     url=scrapedurl,
                     extra="tv",
                     show=item.show,
                     plot=item.plot,
                     thumbnail=item.thumbnail,
                     folder=True))

    support.videolibrary(itemlist, item, 'color kod')

    return itemlist

#----------------------------------------------------------------------------------------------------------------------------------------------

def findvideos(item):
    logger.info("[toonitalia.py] findvideos")
    itemlist = servertools.find_video_items(data=item.url)

    for videoitem in itemlist:
        videoitem.channel = channel
        server = re.sub(r'[-\[\]\s]+', '', videoitem.title)
        videoitem.title = "".join(['[COLOR blue] ' + "[[B]" + server + "[/B]] " + item.title + '[/COLOR]'])
        videoitem.thumbnail = item.thumbnail
        videoitem.plot = item.plot
        videoitem.fulltitle = item.fulltitle
        videoitem.show = item.show

    autoplay.start(itemlist, item)

    return itemlist
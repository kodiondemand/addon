# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per ToonItalia
# ------------------------------------------------------------

import re
import urlparse

from channels import autoplay, filtertools, support
from core import scrapertools, scrapertoolsV2, httptools, servertools
from core.item import Item
from platformcode import logger, config

__channel__ = "toonitalia"
host = "https://toonitalia.org"
headers = [['Referer', host]]

list_servers = ['openload', 'streamango', 'wstream']
list_quality = ['HD', 'default']

def mainlist(item):
    autoplay.init(item.channel, list_servers, list_quality)

    # Main options
    itemlist = []
    support.menu(itemlist, 'Anime bold', 'peliculas_popular', host, contentType='episode')
    support.menu(itemlist, 'Popolari submenu', 'peliculas_new', host, contentType='episode', args="Anime popolari")
    support.menu(itemlist, 'Per Lettera submenu', 'lista_animation', host + '/lista-anime-2/', contentType='episode', args="Anime per Lettera")
    support.menu(itemlist, 'Sub-Ita submenu', 'lista_animation', host + '/lista-anime-sub-ita/', contentType='episode')
    support.menu(itemlist, 'Serie TV bold', 'lista_animation', host + '/lista-serie-tv/', contentType='episode')
    support.menu(itemlist, 'Cerca serie... submenu', 'search', host + '/serietv/', contentType='episode', args='serie')

    autoplay.show_option(item.channel, itemlist)

    return itemlist

def search(item, texto):
    logger.info("[toonitalia] " + item.url + " search " + texto)
    item.url = host + "/?s=" + texto
    try:
        return peliculas_src(item)

    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

def peliculas_popular(item):
    logger.info("[toonitalia] peliculas_popular")
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
            Item(channel=__channel__,
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

    return itemlist

def peliculas_src(item):
    logger.info("[toonitalia] peliculas_src")
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
        scrapedthumbnail = ""

        itemlist.append(
            Item(channel=__channel__,
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
            Item(channel=__channel__,
                 extra=item.extra,
                 action="peliculas_src",
                 title="[COLOR blue][B]Successivo >[/B][/COLOR]",
                 url=scrapedurl,
                 folder=True))

    return itemlist

def peliculas_new(item):
    logger.info("[toonitalia] peliculas_new")
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
            Item(channel=__channel__,
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
            Item(channel=__channel__,
                 extra=item.extra,
                 action="peliculas_new",
                 title="[COLOR blue][B]Successivo >[/B][/COLOR]",
                 url=scrapedurl,
                 thumbnail="thumb_next.png",
                 folder=True))

    return itemlist

def lista_animation(item):
    logger.info("[toonitalia] lista_animation")
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
            Item(channel=__channel__,
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
            Item(channel=__channel__,
                 extra=item.extra,
                 action="lista_animation",
                 title="[COLOR blue][B]Successivo >[/B][/COLOR]",
                 url=scrapedurl,
                 folder=True))

    return itemlist

def peliculas_server(item):
    logger.info("[toonitalia] peliculas_server")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    patron = r'style=".*?">([^<]+)</span><br />(.*?)<span'
    list = scrapertools.find_multiple_matches(data, patron)
    if not len(list) > 0:
        patron = r'<span style="[^"]+">Link\s*([^<]+)</span><br />(.*?)<\/p>'
        list = scrapertools.find_multiple_matches(data, patron)
    for scrapedtitle, link in list:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        scrapedtitle = scrapedtitle.replace("0", "[COLOR yellow] - [/COLOR]")
        if "wiki" in scrapedtitle or "Scegli" in scrapedtitle \
                or "ep." in scrapedtitle or "Special" in scrapedtitle:
            continue
        scrapedtitle = scrapedtitle.replace("Link", "Riproduci con")
        itemlist.append(
            Item(channel=__channel__,
                 action="episodes",
                 title="[COLOR blue]" + scrapedtitle + "[/COLOR]",
                 url=link,
                 extra=scrapedtitle,
                 plot=item.plot,
                 thumbnail=item.thumbnail,
                 folder=True))

    return itemlist

def episodes(item):
    logger.info("[toonitalia] episodes")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    patron = r'<a href="([^"]+)"\s*target="_blank"\s*rel[^>]+>([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(item.url)

    for scrapedurl, scrapedtitle in matches:
        if 'Wikipedia' not in scrapedurl:
            scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).replace("×", "x")
            scrapedtitle = scrapedtitle.replace("_", " ")
            scrapedtitle = scrapedtitle.replace(".mp4", "")
            itemlist.append(
                Item(channel=__channel__,
                     action="findvideos",
                     contentType="tv",
                     title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                     thumbnail=item.thumbnail,
                     fulltitle=scrapedtitle,
                     url=scrapedurl,
                     show=item.show,
                     plot=item.plot,
                     extra="tv",
                     folder=True))

    patron = r'<a href="([^"]+)"\s*target="_blank"[^>]+>[^>]+>[^>]+>[^>]+>\s*[^>]+>([^<]+)[^>]+>'
    matches = re.compile(patron, re.DOTALL).findall(item.url)

    for scrapedurl, scrapedtitle in matches:
        if 'Wikipedia' not in scrapedurl:
            scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).replace("×", "x")
            scrapedtitle = scrapedtitle.replace("_", " ")
            scrapedtitle = scrapedtitle.replace(".mp4", "")
            itemlist.append(
                Item(channel=__channel__,
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

    return itemlist

def findvideos(item):
    logger.info("[toonitalia] findvideos")
    itemlist = servertools.find_video_items(data=item.url)

    for videoitem in itemlist:
        videoitem.channel = __channel__
        server = re.sub(r'[-\[\]\s]+', '', videoitem.title)
        videoitem.title = "".join(['[COLOR blue] ' + "[[B]" + server + "[/B]] " + item.title + '[/COLOR]'])
        videoitem.thumbnail = item.thumbnail
        videoitem.plot = item.plot
        videoitem.fulltitle = item.fulltitle
        videoitem.show = item.show

    return itemlist
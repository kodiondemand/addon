# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per ToonItalia
# ------------------------------------------------------------

import re

from core import scrapertools, httptools, tmdb, support, servertools
from core.item import Item
from platformcode import logger
from specials import autoplay

channel = "toonitalia"
host = "https://toonitalia.org"
headers = [['Referer', host]]

list_servers = ['wstream', 'openload', 'streamango']
list_quality = ['HD', 'default']

def mainlist(item):

    # Main options
    itemlist = []
    support.menu(itemlist, 'Ultimi episodi inseriti bold', 'insert', host, contentType='episode')
    support.menu(itemlist, 'Ultime novità bold', 'updates', host, contentType='episode')
    support.menu(itemlist, 'Episodi più visti bold', 'most_view', host, contentType='episode')
    support.menu(itemlist, 'Anime', 'list', host + '/lista-anime-2/', contentType='episode')
    support.menu(itemlist, 'Sub-Ita submenu', 'list', host + '/lista-anime-sub-ita/', contentType='episode')
    support.menu(itemlist, 'Serie TV bold', 'list', host + '/lista-serie-tv/', contentType='episode')
    support.menu(itemlist, 'Film Animazione bold', 'list', host + '/lista-film-animazione/', contentType="episode", args="film")
    support.menu(itemlist, '[COLOR blue]Cerca anime e serie...[/COLOR] bold', 'search', host, contentType='episode')

    autoplay.init(item.channel, list_servers, list_quality)
    autoplay.show_option(item.channel, itemlist)

    return itemlist

#----------------------------------------------------------------------------------------------------------------------------------------------

def insert(item):
    logger.info("[toonitalia.py] insert")
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
                 action="episodios",
                 contentType="episode",
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 show=scrapedtitle,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 folder=True))

    if len(matches) >= p * minpage:
        scrapedurl = item.url + '{}' + str(p + 1)
        itemlist.append(
            Item(channel=channel,
                 args=item.args,
                 action="insert",
                 title="[COLOR blue][B]Successivo >[/B][/COLOR]",
                 url=scrapedurl,
                 thumbnail="thumb_next.png",
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist

#----------------------------------------------------------------------------------------------------------------------------------------------

def updates(item):
    logger.info("[toonitalia.py] updates")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    blocco = r'Aggiornamenti</h2>(.*?)</ul>'
    matches = re.compile(blocco, re.DOTALL).findall(data)
    for scrapedurl in matches:
        blocco = scrapedurl

    patron = r'<a href="(.*?)">(.*?)</a>'
    matches = re.compile(patron, re.DOTALL).findall(blocco)

    for scrapedurl, scrapedtitle in matches:
        scrapedplot = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(
            Item(channel=channel,
                 action="episodios",
                 contentType="episode",
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 show=scrapedtitle,
                 plot=scrapedplot))

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
        scrapedplot = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(
            Item(channel=channel,
                 action="episodios",
                 contentType="episode",
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 show=scrapedtitle,
                 plot=scrapedplot))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

#----------------------------------------------------------------------------------------------------------------------------------------------

def list(item):
    logger.info("[toonitalia.py] list")
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
        if 'Film Animazione disponibili' not in scrapedtitle:
            scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
            scrapedplot = ""
            itemlist.append(
                Item(channel=channel,
                     action = 'episodios' if not 'film' in item.args else 'findvideos',
                     contentType=item.contentType,
                     title=scrapedtitle,
                     fulltitle=scrapedtitle,
                     url=scrapedurl,
                     show=scrapedtitle,
                     args=item.args,
                     plot=scrapedplot))

    if len(matches) >= p * minpage:
        scrapedurl = item.url + '{}' + str(p + 1)
        itemlist.append(
            Item(channel=channel,
                 args=item.args,
                 contentType=item.contentType,
                 action="list",
                 title="[COLOR blue][B]Successivo >[/B][/COLOR]",
                 url=scrapedurl))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

#----------------------------------------------------------------------------------------------------------------------------------------------

def peliculas(item):
    logger.info("[toonitalia] peliculas")
    itemlist = []
    minpage = 14

    p = 1
    if '{}' in item.url:
        item.url, p = item.url.split('{}')
        p = int(p)

    data = httptools.downloadpage(item.url, headers=headers).data

    patron = r'<h2 class="entry-title"><a href="([^"]+)" rel="bookmark">([^<]+)</a></h2>.*?<p>([^<]+)</p>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    print data

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
                 plot=scrapedplot))

    if len(matches) >= p * minpage:
        scrapedurl = item.url + '{}' + str(p + 1)
        itemlist.append(
            Item(channel=channel,
                 extra=item.extra,
                 action="peliculas",
                 title="[COLOR blue][B]Successivo >[/B][/COLOR]",
                 url=scrapedurl))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

#----------------------------------------------------------------------------------------------------------------------------------------------

def episodios(item):
    logger.info("[toonitalia.py] episodios")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    patron = r'<br /> <a href="([^"]+)"\s*target="_blank"\s*rel[^>]+>([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    if "https://vcrypt.net" in data:
        patron = r'(?:<p>|<br />)([^<]+)<a href="([^"]+)'
        matches = re.compile(patron, re.DOTALL).findall(data)

        for scrapedtitle, scrapedurl in matches:
            if 'Wikipedia' not in scrapedurl:
                scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).replace("×", "x")
                scrapedtitle = scrapedtitle.replace("_", " ")
                scrapedtitle = scrapedtitle.replace(".mp4", "")
                puntata = scrapedtitle
                for i in itemlist:
                    if i.args == puntata:  # è già stata aggiunta
                        i.url += " " + scrapedurl
                        break

                else:
                    itemlist.append(
                        Item(channel=channel,
                             action="findvideos",
                             contentType=item.contentType,
                             title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                             thumbnail=item.thumbnail,
                             fulltitle=scrapedtitle,
                             url=scrapedurl,
                             args=puntata,
                             show=item.show,
                             plot=item.plot))
    else:
        for scrapedurl, scrapedtitle in matches:
            if 'Wikipedia' not in scrapedurl:
                scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).replace("×", "x")
                scrapedtitle = scrapedtitle.replace("_", " ")
                scrapedtitle = scrapedtitle.replace(".mp4", "")
                # puntata = scrapertools.find_single_match(scrapedtitle, '[0-9]+x[0-9]+')
                puntata = scrapedtitle
                for i in itemlist:
                    if i.args == puntata: #è già stata aggiunta
                        i.url +=  " " + scrapedurl
                        break

                else:
                    itemlist.append(
                        Item(channel=channel,
                            action="findvideos",
                            contentType=item.contentType,
                            title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                            thumbnail=item.thumbnail,
                            fulltitle=scrapedtitle,
                            url=scrapedurl,
                            args = puntata,
                            show=item.show,
                            plot=item.plot))

    support.videolibrary(itemlist, item, 'color kod')

    return itemlist

#----------------------------------------------------------------------------------------------------------------------------------------------

def search(item, texto):
    logger.info("[toonitalia.py] " + item.url + " search " + texto)
    item.url = host + "/?s=" + texto
    try:
        return peliculas(item)

    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

#----------------------------------------------------------------------------------------------------------------------------------------------

def findvideos(item):
    logger.info("[toonitalia.py] findvideos")

    if item.args == 'film':
        data = httptools.downloadpage(item.url, headers=headers).data
        itemlist = servertools.find_video_items(data=data)

        for videoitem in itemlist:
            videoitem.channel = channel
            server = re.sub(r'[-\[\]\s]+', '', videoitem.title)
            videoitem.title = "".join(['[COLOR blue] ' + "[[B]" + server + "[/B]][/COLOR] " + item.title])
            videoitem.thumbnail = item.thumbnail
            videoitem.plot = item.plot
            videoitem.fulltitle = item.fulltitle
            videoitem.show = item.show

    else:
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

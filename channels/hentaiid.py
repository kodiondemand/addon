# -*- coding: utf-8 -*-

import re

import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger

CHANNEL_HOST = "http://hentai-id.tv/"


def mainlist(item):
    logger.info()

    itemlist = list()
    itemlist.append(Item(channel=item.channel, action="series", title="Novedades",
                         url=urlparse.urljoin(CHANNEL_HOST, "archivos/h2/"), extra="novedades"))
    itemlist.append(Item(channel=item.channel, action="generos", title="Por géneros", url=CHANNEL_HOST))
    itemlist.append(Item(channel=item.channel, action="series", title="Sin Censura",
                         url=urlparse.urljoin(CHANNEL_HOST, "archivos/sin-censura/")))
    itemlist.append(Item(channel=item.channel, action="series", title="High Definition",
                         url=urlparse.urljoin(CHANNEL_HOST, "archivos/high-definition/")))
    itemlist.append(Item(channel=item.channel, action="series", title="Mejores Hentais",
                         url=urlparse.urljoin(CHANNEL_HOST, "archivos/ranking-hentai/")))

    return itemlist


def generos(item):
    logger.info()

    itemlist = []
    data = re.sub(r"\n|\r|\t|\s{2}", "", httptools.downloadpage(item.url).data)

    pattern = 'id="hentai2"><div[^>]+>(.*?)</div></div>'
    data = scrapertools.find_single_match(data, pattern)

    patron = 'href="([^"]+)"[^>]+>(.*?)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, title in matches:
        # logger.debug("title=[{0}], url=[{1}]".format(title, url))
        itemlist.append(Item(channel=item.channel, action="series", title=title, url=url))

    return itemlist


def series(item):
    logger.info()

    data = re.sub(r"\n|\r|\t|\s{2}", "", httptools.downloadpage(item.url).data)

    pattern = "<div class='wp-pagenavi'>(.*?)</div>"
    pagination = scrapertools.find_single_match(data, pattern)

    pattern = '<div class="col-xs-12 col-md-12 col-lg-9px-3"><ul>(.*?)</ul><div class="clearfix">'
    data = scrapertools.find_single_match(data, pattern)

    pattern = '<a href="([^"]+)".*?<img src="([^"]+)" title="([^"]+)"'
    matches = re.compile(pattern, re.DOTALL).findall(data)
    itemlist = []

    if item.extra == "novedades":
        action = "findvideos"
    else:
        action = "episodios"

    for url, thumbnail, title in matches:
        fulltitle = title
        show = title
        # logger.debug("title=[{0}], url=[{1}], thumbnail=[{2}]".format(title, url, thumbnail))
        itemlist.append(Item(channel=item.channel, action=action, title=title, url=url, thumbnail=thumbnail,
                             show=show, fulltitle=fulltitle, fanart=thumbnail, folder=True))

    if pagination:
        page = scrapertools.find_single_match(pagination, '>(?:Page|Página)\s*(\d+)\s*(?:of|de)\s*\d+<')
        pattern = 'href="([^"]+)">%s<' % (int(page) + 1)
        url_page = scrapertools.find_single_match(pagination, pattern)

        if url_page:
            itemlist.append(Item(channel=item.channel, action="series", title=">> Página Siguiente", url=url_page))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    data = re.sub(r"\n|\r|\t|\s{2}", "", httptools.downloadpage(item.url).data)
    pattern = '<div class="box-entry-title text-center">Lista de Capítulos</div>(.*?)</div></div>'

    data = scrapertools.find_single_match(data, pattern)
    patron = '<a href="([^"]+)"[^>]+>([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        title = scrapertools.unescape(scrapedtitle)
        url = urlparse.urljoin(item.url, scrapedurl)
        thumbnail = item.thumbnail
        plot = item.plot

        # logger.debug("title=[{0}], url=[{1}], thumbnail=[{2}]".format(title, url, thumbnail))
        itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url,
                             thumbnail=thumbnail, plot=plot, show=item.show, fulltitle="%s %s" % (item.show, title),
                             fanart=thumbnail))

    return itemlist


def findvideos(item):
    logger.info()

    data = httptools.downloadpage(item.url).data

    patron = '<(?:iframe)?(?:IFRAME)?\s*(?:src)?(?:SRC)?="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for url in matches:
        if 'goo.gl' in url:
            video = httptools.downloadpage(url, follow_redirects=False, only_headers=True).headers["location"]
            matches.remove(url)
            matches.append(video)

    from core import servertools
    itemlist = servertools.find_video_items(data=",".join(matches))
    for videoitem in itemlist:
        videoitem.fulltitle = item.fulltitle
        videoitem.channel = item.channel
        videoitem.thumbnail = item.thumbnail

    return itemlist

# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per vedohd
# ------------------------------------------------------------

from core import scrapertoolsV2, httptools, support
from core.item import Item
from platformcode import logger
from specials import autoplay
from platformcode import config

headers = ""
host = ""


def findhost():
    permUrl = httptools.downloadpage('https://www.cb01.uno/', follow_redirects=False).headers
    cb01Url = 'https://www.'+permUrl['location'].replace('https://www.google.it/search?q=site:', '')
    data = httptools.downloadpage(cb01Url).data
    global host, headers

    host = scrapertoolsV2.find_single_match(data, r'class="?mega-menu-link"? href="?(https://vedohd[^/"]+)"?')+'/'

    if 'https' not in host:  # in caso cb01 cambi, si spera di riuscire ad accedere da questo URL
        host = "https://vedohd.pw/"
    headers = [['Referer', host]]


IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['verystream', 'openload', 'streamango', 'wstream']
list_quality = ['HD', 'SD']

#esclusione degli articoli 'di servizio'
blacklist = ['CB01.UNO &#x25b6; TROVA L&#8217;INDIRIZZO UFFICIALE ', 'AVVISO IMPORTANTE – CB01.UNO', 'GUIDA VEDOHD']


def mainlist(item):
    logger.info("[vedohd.py] mainlist")
    findhost()

    autoplay.init(item.channel, list_servers, list_quality)

    # Main options
    itemlist = []
    support.menu(itemlist, 'Film', "peliculas", host+"film-hd")
    support.menu(itemlist, 'I più votati', "peliculas", host+"ratings/?get=movies")
    support.menu(itemlist, 'I più popolari', "peliculas", host+"trending/?get=movies")
    support.menu(itemlist, 'Generi', "generos", host)
    support.menu(itemlist, 'Anno', "year", host)
    support.menu(itemlist, 'Cerca', "search", host)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def search(item, text):
    logger.info("[vedohd.py] " + item.url + " search " + text)
    item.url = item.url + "/?s=" + text

    return support.dooplay_search(item, blacklist)


def peliculas(item):
    logger.info("[vedohd.py] video")

    return support.dooplay_films(item, blacklist)


def findvideos(item):
    findhost()
    itemlist = []
    for link in support.dooplay_get_links(item, host):
        if link['title'] != 'Trailer':
            logger.info(link['title'])
            server, quality = scrapertoolsV2.find_single_match(link['title'], '([^ ]+) ?(HD|3D)?')
            if quality:
                title = server + " [COLOR blue][" + quality + "][/COLOR]"
            else:
                title = server
            itemlist.append(
                Item(channel=item.channel,
                     action="play",
                     title=title,
                     url=link['url'],
                     server=server,
                     fulltitle=item.fulltitle,
                     thumbnail=item.thumbnail,
                     show=item.show,
                     quality=quality,
                     contentType=item.contentType,
                     folder=False))

    autoplay.start(itemlist, item)

    return itemlist


def generos(item):
    findhost()
    patron = '<a href="([^"#]+)">([a-zA-Z]+)'
    return support.scrape(item, patron, ['url', 'title'], patronBlock='<a href="#">Genere</a><ul class="sub-menu">.*?</ul>', action='peliculas')


def year(item):
    findhost()
    patron = r'<a href="([^"#]+)">(\d+)'
    return support.scrape(item, patron, ['url', 'title'], patronBlock='<a href="#">Anno</a><ul class="sub-menu">.*?</ul>', action='peliculas')


def play(item):
    logger.info("[vedohd.py] play")

    data = support.swzz_get_url(item)

    return support.server(item, data, headers=headers)

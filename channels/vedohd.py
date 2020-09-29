# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per vedohd
# ------------------------------------------------------------

from core import scrapertools, support, autoplay
from platformcode import logger, config

host = config.get_channel_url()
headers = ""

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()



#esclusione degli articoli 'di servizio'
blacklist = ['CB01.UNO &#x25b6; TROVA L&#8217;INDIRIZZO UFFICIALE ', 'AVVISO IMPORTANTE – CB01.UNO', 'GUIDA VEDOHD']

@support.menu
def mainlist(item):

    film = [
        ('I più votati', ["ratings/?get=movies", 'peliculas']),
        ('I più popolari', ["trending/?get=movies", 'peliculas']),
        ('Generi', ['ratings/?get=movies', 'menu', 'genres']),
        ('Anno', ["", 'menu', 'releases']),
    ]
    return locals()


def search(item, text):
    logger.info("[vedohd.py] " + item.url + " search " + text)
    item.url = item.url + "/?s=" + text

    return support.dooplay_search(item, blacklist)


def peliculas(item):
    return support.dooplay_peliculas(item, False, blacklist)


def findvideos(item):
    itemlist = []
    for link in support.dooplay_get_links(item, host):
        if link['title'] != 'Trailer':
            logger.info(link['title'])
            server, quality = scrapertools.find_single_match(link['title'], '([^ ]+) ?(HD|3D)?')
            if quality:
                title = server + " [COLOR blue][" + quality + "][/COLOR]"
            else:
                title = server
            itemlist.append(item.clone(action="play", title=title, url=link['url'], server=server, quality=quality,))

    autoplay.start(itemlist, item)

    return itemlist


@support.scrape
def menu(item):
    return support.dooplay_menu(item, item.args)


def play(item):
    logger.info("[vedohd.py] play")

    data = support.swzz_get_url(item)

    return support.server(item, data, headers=headers)

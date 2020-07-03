# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per netfreex
# ------------------------------------------------------------

from core import support
from core.item import Item
from platformcode import logger, config

# def findhost():
#     return 'https://' + support.match('https://netfreex.uno/', patron='value="site:([^"]+)"').match

host = config.get_channel_url()
headers = ""

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()




@support.menu
def mainlist(item):

    film = ['/film',
        ('Generi', ['', 'menu', 'genres'])
    ]
    tvshow = ['/serietv']
    anime = ['/genere/anime']
    return locals()


def search(item, text):
    logger.info()
    item.url = item.url + "/?s=" + text
    try:
        return support.dooplay_search(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def peliculas(item):
    if 'anime' in item.url:
        return support.dooplay_peliculas(item, True)
    else:
        return support.dooplay_peliculas(item, False)


def episodios(item):
    return support.dooplay_get_episodes(item)


def findvideos(item):
    itemlist = []
    for link in support.dooplay_get_links(item, host):
        if link['title'] != 'Guarda il trailer':
            logger.info(link['title'])
            itemlist.append(
                item.clone(action="play", url=link['url'], quality=link['title']))
    return support.server(item, itemlist=itemlist)


@support.scrape
def menu(item):
    action = 'peliculas'
    data = support.match(item, patron=r'<a href="#">Genere<(.*?)</ul').match
    patronMenu= r'<a href="(?P<url>[^"]+)"[^>]*>(?P<title>[^<]+)<'
    return locals()

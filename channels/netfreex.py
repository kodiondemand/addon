# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per netfreex
# ------------------------------------------------------------

from core import support
from core.item import Item
from platformcode import logger, config

# def findhost(url):
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
    logger.info('search', text)
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
    from core import jsontools
    itemlist = []
    matches = support.match(item, patron=r'<li id="player-option-[0-9]".*?data-type="([^"]+)" data-post="([^"]+)" data-nume="([^"]+)".*?<span class="title".*?>([^<>]+)</span>(?:<span class="server">([^<>]+))?').matches
    for Type, Post, Nume, Quality, Server in matches:
        dataAdmin = support.match(host + '/wp-json/dooplayer/v1/post/%s?type=%s&source=%s' %(Post, Type, Nume)).data
        js = jsontools.load(dataAdmin)
        link = js['embed_url'] if 'embed_url' in js else ''
        itemlist.append( item.clone(server=Server, quality=Quality, url=link, action='play'))
    return support.server(item, itemlist=itemlist)


@support.scrape
def menu(item):
    action = 'peliculas'
    data = support.match(item, patron=r'<a href="#">Genere<(.*?)</ul').match
    patronMenu= r'<a href="(?P<url>[^"]+)"[^>]*>(?P<title>[^<]+)<'
    return locals()

# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Streaming Altadefinizione
# ------------------------------------------------------------

from core import support
from core.item import Item
from specials import autoplay

host = 'https://www.streamingaltadefinizione.space'

list_servers = ['verystream', 'openload', 'wstream']
list_quality = ['1080p', 'HD', 'DVDRIP', 'SD', 'CAM']

def mainlist(item):
    support.log()
    itemlist = []

    support.menu(itemlist, 'Film', 'peliculas', host + "/film/")
    support.menu(itemlist, 'Film Anime', 'peliculas', host + "/genere/anime/")
    support.menu(itemlist, 'Film per genere', 'generos', host)
    support.menu(itemlist, 'Serie TV', 'peliculas', host + "/serietv/", contentType='tvshow')
    support.menu(itemlist, 'Anime', 'peliculas', host + "/genere/anime/", contentType='tvshow')
    support.menu(itemlist, 'Cerca film', 'search', host)
    support.menu(itemlist, 'Cerca serie tv', 'search', host, contentType='tvshow')

    autoplay.init(item.channel, list_servers, list_quality)
    autoplay.show_option(item.channel, itemlist)

    return itemlist


def search(item, text):
    support.log("[streamingaltadefinizione.py] " + item.url + " search " + text)
    item.url = item.url + "/?s=" + text

    return support.dooplay_search(item)


def generos(item):
    patron = '<a href="([^"#]+)">([a-zA-Z]+)'
    return support.scrape(item, patron, ['url', 'title'], patron_block='<a href="#">Genere</a><ul class="sub-menu">.*?</ul>', action='peliculas')


def peliculas(item):
    support.log("[streamingaltadefinizione.py] video")

    return support.dooplay_films(item)


def episodios(item):
    return support.dooplay_get_episodes(item)


def findvideos(item):
    itemlist = []
    for link in support.dooplay_get_links(item, host):
        server = link['server'][:link['server'].find(".")]
        itemlist.append(
            Item(channel=item.channel,
                 action="play",
                 title=server + " [COLOR blue][" + link['title'] + "][/COLOR]",
                 url=link['url'],
                 server=server,
                 fulltitle=item.fulltitle,
                 thumbnail=item.thumbnail,
                 show=item.show,
                 quality=link['title'],
                 contentType=item.contentType,
                 folder=False))

    autoplay.start(itemlist, item)

    return itemlist
# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Popcorn Stream
# ------------------------------------------------------------

from core import support, httptools
from core.item import Item
from platformcode import config
import sys
if sys.version_info[0] >= 3:
    from urllib.parse import unquote
else:
    from urllib import unquote


list_servers = ['verystream', 'openload', 'wstream']
list_quality = ['1080p', 'HD', 'DVDRIP', 'SD', 'CAM']

def findhost():
    data = httptools.downloadpage('https://www.popcornstream-nuovo-indirizzo.online/').data
    return support.scrapertools.find_single_match(data, '<a href="([^"]+)')

host = config.get_channel_url(findhost)
headers = [['Referer', host]]

@support.menu
def mainlist(item):

    film = ["/film/"]
    anime = ["/genere/anime/"]
    tvshow = ["/serietv/"]
    top = [('Generi',['', 'genre'])]

    return locals()


def search(item, text):
    support.log("[streamingaltadefinizione.py] " + item.url + " search " + text)
    item.url = item.url + "/?s=" + text
    try:
        return support.dooplay_search(item)
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
        return []


@support.scrape
def genre(item):
    patronMenu = '<a href="(?P<url>[^"#]+)">(?P<title>[a-zA-Z]+)'
    patronBlock='<a href="#">Genere</a><ul class="sub-menu">(?P<block>.*?)</ul>'
    action='peliculas'

    return locals()


def peliculas(item):
    return support.dooplay_peliculas(item, True if "/genere/" in item.url else False)


def episodios(item):
    return support.dooplay_get_episodes(item)


def findvideos(item):
    itemlist = []
    matches = support.match(item, patron=r'<a href="([^"]+)[^>]+>Download[^>]+>[^>]+>[^>]+><strong class="quality">([^<]+)<').matches
    for url, quality in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action="play",
                 url=unquote(support.match(url, patron=[r'dest=([^"]+)"',r'/(http[^"]+)">Click']).match),
                 fulltitle=item.fulltitle,
                 thumbnail=item.thumbnail,
                 show=item.show,
                 quality=quality,
                 contentType=item.contentType,
                 folder=False))

    return support.server(item, itemlist=itemlist)

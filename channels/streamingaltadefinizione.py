# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Popcorn Stream
# ------------------------------------------------------------

from core import support, httptools
from platformcode import config, logger
import sys
if sys.version_info[0] >= 3:
    from urllib.parse import unquote
else:
    from urllib import unquote


def findhost(url):
    data = httptools.downloadpage(url).data
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
    logger.debug(text)
    item.url = item.url + "/?s=" + text
    try:
        return support.dooplay_search(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


@support.scrape
def genre(item):
    patronMenu = '<a href="(?P<url>[^"#]+)">(?P<title>[a-zA-Z]+)'
    patronBlock='<a href="#">Genere</a><ul class="sub-menu">(?P<block>.*?)</ul>'
    action='movies'

    return locals()


def movies(item):
    return support.dooplay_movies(item, True if "/genere/" in item.url else False)


def episodes(item):
    return support.dooplay_get_episodes(item)


def findvideos(item):
    itemlist = []
    matches = support.match(item, patron=r'<a href="([^"]+)[^>]+>Download[^>]+>[^>]+>[^>]+><strong class="quality">([^<]+)<').matches
    for url, quality in matches:
        itemlist.append(
            item.clone(caction="play",
                       url=unquote(support.match(url, patron=[r'dest=([^"]+)"',r'/(http[^"]+)">Click']).match),
                       quality=quality))

    return support.server(item, itemlist=itemlist)

# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per filmstreaming
# ------------------------------------------------------------

from core import support
from core.item import Item
from platformcode import config, logger

host = config.get_channel_url()
headers = [['Referer', host]]


@support.menu
def mainlist(item):

    film = ['/film',
            ('Al Cinema', ['/cinema', 'peliculas']),
            ('Ultimi Inseriti', ['', 'peliculas', 'last']),
            ('Generi', ['', 'genres', 'genres']),
            ('Anno', ['', 'genres', 'years'])]

    return locals()


def search(item, text):
    logger.debug('search', text)
    itemlist = []
    text = text.replace(" ", "+")
    item.url = f'{host}/index.php?do=search&subaction=search&story={text}'

    try:
        return peliculas(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("search except: %s" % line)
        return []


def newest(categoria):
    logger.debug(categoria)

    itemlist = []
    item = Item()
    try:
        if categoria == "peliculas":
            item.url = host
            item.action = "peliculas"
            item.contentType = 'movie'
            item.args = 'last'
            itemlist = peliculas(item)
            if itemlist[-1].action == "peliculas":
                itemlist.pop()
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


@support.scrape
def peliculas(item):
    if item.args == 'last':
        patronBlock = r'inseriti:(?P<block>.*?)<div class="block-showmore'
    patron = r'item-movie">[^>]+><a href="(?P<url>[^"]+)[^>]+><img data-src="(?P<thumb>[^"]+)(?:[^>]+>){6}(?P<title>[^<]+)(?:[^>]+>){6}(?P<quality>[^<]+)'
    patronNext = r'<a href="([^"]+)">&rarr'
    return locals()


@support.scrape
def genres(item):
    action = "peliculas"
    _type ={'years':'Anno', 'genres':'Categorie'}

    patronBlock = f'{_type[item.args]}(?:[^>]+>){{4}}(?P<block>.*?)</ul>'
    patronMenu = '<li><a href="(?P<url>[^"]+)">(?P<title>.*?)</a>'

    return locals()


def findvideos(item):
    url = support.match(item.url, patron='<iframe [^>]+src="([^"]+)').match
    data = support.match(url).data
    return support.server(item, data)

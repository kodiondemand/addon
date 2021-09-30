# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per piratestreaming
# ----------------------------------------------------------


from core import support
from core.support import config
from platformcode import logger

host = config.get_channel_url()
headers = [['Referer', host]]


@support.menu
def mainlist(item):

    film = ['/category/films']
    tvshow = ['/category/serie']
    anime = ['/category/anime-cartoni-animati']
    search = ''

    return locals()


def search(item, texto):
    logger.debug(texto)
    item.url = host + "/search/" + texto
    try:
        return movies(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(category):
    logger.debug(category)
    itemlist = []
    item = support.Item()
    try:
        if category == "movie":
            item.url = host + '/category/films'
            item.contentType = 'movies'
            return movies(item)
        if category == 'tvshow':
            item.url = host + '/category/serie'
            item.contentType = 'tvshow'
            return movies(item)
        if category == "anime":
            item.url = host + '/category/anime-cartoni-animati'
            item.contentType = 'tvshow'
            return movies(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


@support.scrape
def movies(item):
    patron = r'data-placement="bottom" title="(?P<title>[^"]+)" alt=[^=]+="(?P<url>[^"]+)"> <img class="[^"]+" title="[^"]+(?P<type>film|serie)[^"]+" alt="[^"]+" src="(?P<thumb>[^"]+)"'
    patronNext = r'<a\s*class="nextpostslink" rel="next" href="([^"]+)">Avanti'

    typeActionDict = {'findvideos': ['film'], 'episodes': ['serie']}
    typeContentDict = {'movie': ['film'], 'tvshow': ['serie']}
    # debug = True
    return locals()


@support.scrape
def episodes(item):
    if item.data: data = item.data
    # debug= True
    title = item.fulltitle
    patron = r'link-episode">(?:\s*<strong>)?\s*(?P<episode>\d+.\d+(?:.\d+)?)(?:\s*\((?P<lang>[?P<lang>A-Za-z-]+)[^>]+>)?(?:\s*(?P<title>[^-<]+))[^>]+</span>\s*(?P<url>.*?)</div>'
    def itemHook(item):
        if 'Episodio' in item.title:
            item.title = support.re.sub(r'Episodio [0-9.-]+', title, item.title)
        return item
    return locals()


def findvideos(item):
    if item.contentType == 'episode':
        data = item.url
    else:
        data = support.match(item).data
        if 'link-episode' in data:
            item.data = data
            return episodes(item)
    return support.server(item, data=data)

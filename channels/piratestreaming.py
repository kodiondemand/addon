# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per piratestreaming
# ----------------------------------------------------------


from core import support
from core.support import config, info

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
    info(texto)
    item.url = host + "/?s=" + texto
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
        return []


def newest(categoria):
    support.info(categoria)
    itemlist = []
    item = support.Item()
    try:
        if categoria == "peliculas":
            item.url = host + '/category/films'
            item.contentType = 'movies'
            return peliculas(item)
        if categoria == "series":
            item.url = host + '/category/serie'
            item.contentType = 'tvshow'
            return peliculas(item)
        if categoria == "anime":
            item.url = host + '/category/anime-cartoni-animati'
            item.contentType = 'tvshow'
            return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("{0}".format(line))
        return []

    return itemlist


@support.scrape
def peliculas(item):
    patron = r'data-placement="bottom" title="(?P<title>[^"]+)" alt=[^=]+="(?P<url>[^"]+)"> <img class="[^"]+" title="[^"]+(?P<type>film|serie)[^"]+" alt="[^"]+" src="(?P<thumb>[^"]+)"'
    patronNext = r'<a\s*class="nextpostslink" rel="next" href="([^"]+)">Avanti'

    typeActionDict = {'findvideos': ['film'], 'episodios': ['serie']}
    typeContentDict = {'movie': ['film'], 'tvshow': ['serie']}
    # debug = True
    return locals()


@support.scrape
def episodios(item):
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
            return episodios(item)
    return support.server(item, data=data)

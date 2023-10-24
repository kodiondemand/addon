# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per altadefinizione
# ------------------------------------------------------------


from core import httptools, support
from platformcode import config, logger


def findhost(url):
    host = support.match(url, patron=r'<h2[^>]+><a href="([^"]+)').match.rstrip('/')
    return host


host = config.get_channel_url(findhost)
headers = [['Referer', host]]


@support.menu
def mainlist(item):

    film = ['/category/film/',
            ('Al Cinema', ['/prime-visioni/', 'peliculas']),
            ('Generi', ['', 'genres']),
            # ('Sub-ITA', ['/sub-ita/', 'peliculas'])
            ]

    tvshow = ['/category/serie-tv/',
             ('Aggiornamenti Serie TV', ['/aggiornamenti-serie-tv/', 'peliculas']),]

    search = ''

    return locals()


@support.scrape
def genres(item):
    action = 'peliculas'
    blacklist = ['Scegli il Genere', 'Film', 'Serie TV', 'Sub-Ita', 'Anime']
    patronMenu = r'<a href="(?P<url>[^"]+)" class="category-button">(?P<title>[^<]+)'
    '<a href="https://altadefinizione.archi/category/film/animazione/" class="category-button">Animazione</a>'

    def itemlistHook(itemlist):
        itl = []
        for item in itemlist:
            if len(item.fulltitle) != 3:
                itl.append(item)
        return itl
    return locals()


def search(item, text):
    logger.debug(text)
    item.url = "{}/search/{}/feed/rss2/".format(host, text)
    # item.url = "{}/s={}".format(host, text)
    item.args = 'search'

    try:
        return peliculas(item)

    except:
        import sys
        for line in sys.exc_info():
            logger.error("search except: %s" % line)
        return []


@support.scrape
def peliculas(item):
    item.contentType = "undefined"
    action = 'check'
    patron = r'src="(?P<poster>http[^"]+)(?:[^>]+>){5}\s*<a href="(?P<url>[^"]+)[^>]+>\s*(?P<title>[^\[\(\<]+)(?:\[(?P<quality>[^\]]+)\])?\s*(?:\((?P<lang>[a-zA-z-]+)\))?\s*(?:\((?P<year>\d+)\))?\s*</a>\s*</h1>'
    # if item.args == 'search':
    #     patron = r'<item>\s*<title>(?P<title>[^\[\(\<]+)(?:\[(?P<quality>[^\]]+)\])?\s*(?:\((?P<lang>[a-zA-z-]+)\))?\s*(?:\((?P<year>\d+)\))?\s*[^>]+>\s*<link>(?P<url>[^<]+)'
    patronNext = r'href="([^"]+)[^>]+>Successivo'
    # debug = True
    return locals()


@support.scrape
def episodios(item):
    item.quality = ''
    data = item.data
    action='findvideos'
    # debugBlock=True
    patronBlock = r'<h2>[Ss]tagione: (?P<season>\d+)(?P<block>.*?)</ul>'
    patron = r'<a href="(?P<url>[^"]+).*?[Ee]pisodio N°: (?P<episode>\d+)'
    return locals()


def check(item):
    item.data = httptools.downloadpage(item.url).data
    if 'stagione' in item.data.lower():
        item.contentType = 'tvshow'
        return episodios(item)
    else:
        return findvideos(item)


def findvideos(item):
    logger.debug()
    # support.dbg()
    if not item.data:
        item.data = httptools.downloadpage(item.url).data
    data = item.data
    if item.contentType == 'movie' and isinstance(item.data, str):
        data = support.match(support.match(item.data, patron=r'iframe src="([^"]+)').match).data
    item.data = ''
    return support.server(item, data)

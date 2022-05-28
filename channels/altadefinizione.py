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

    film = ['/genere/film/',
            ('Al Cinema', ['/al-cinema/', 'peliculas']),
            ('Generi', ['', 'genres']),
            ('Sub-ITA', ['/sub-ita/', 'peliculas'])]

    tvshow = ['/genere/serie-tv/']

    search = ''

    return locals()


@support.scrape
def genres(item):
    action = 'peliculas'
    blacklist = ['Scegli il Genere', 'Film', 'Serie TV', 'Sub-Ita', 'Anime']
    patronMenu = r'<option value="(?P<url>[^"]+)">(?P<title>[^<]+)'
    return locals()


def search(item, text):
    logger.debug(text)
    item.url = "{}/?s={}".format(host, text)

    try:
        return peliculas(item)

    except:
        import sys
        for line in sys.exc_info():
            logger.error("search except: %s" % line)
        return []


@support.scrape
def peliculas(item):
    n = '22' if '/?s=' in item.url else '8'
    item.contentType = "undefined"
    action = 'check'
    # patron = r'data-src="(?P<thumb>http[^"]+)(?:[^>]+>){' + n + r'}\s*<a href="(?P<url>[^"]+)[^>]+>\s*(?P<title>[^\[\(\<]+)(?:\[(?P<quality>[^\]]+)\])?\s*(?:\((?P<lang>[a-zA-z-]+)\))?\s*(?:\((?P<year>\d+)\))?\s*</a>\s*</h2>'
    patron = r'data-src="(?P<poster>http[^"]+)(?:[^>]+>){7,18}\s*<a href="(?P<url>[^"]+)[^>]+>\s*(?P<title>[^\[\(\<]+)(?:\[(?P<quality>[^\]]+)\])?\s*(?:\((?P<lang>[a-zA-z-]+)\))?\s*(?:\((?P<year>\d+)\))?\s*</a>\s*</h2>'
    patronNext = r'href="([^"]+)[^>]+>»'
    return locals()


@support.scrape
def episodios(item):
    item.quality = ''
    data = item.data
    action='findvideos'
    # patronBlock = r'[Ss]tagione.*?\s(?P<lang>(?:[Ss][Uu][Bb][-]?)?[Ii][Tt][Aa])(?: in )?(?P<quality>[^<]*)?(?:[^>]+>){4}(?P<block>.*?)/p>'
    patronBlock = r'<strong>\s*\w+\s*[Ss]tagione.*?(?P<lang>(?:[Ss][Uu][Bb][-]?)?[Ii][Tt][Aa])(?: in )?(?P<quality>[^<]*)?(?:[^>]+>){4}(?P<block>.*?)/p>'
    patron = r'(?P<season>\d+)&[^:]+;(?P<episode>\d+)(?P<data>.*?)(?:<br|$)'
    return locals()


def check(item):
    item.data = httptools.downloadpage(item.url).data
    if 'rel="tag">Serie TV' in item.data:
        item.contentType = 'tvshow'
        return episodios(item)
    else:
        return findvideos(item)


def findvideos(item):
    logger.debug()
    if item.contentType == 'movie':
        item.data = support.match(item.data, patron=r'data-id="([^"]+)').matches
    return support.server(item, item.data)

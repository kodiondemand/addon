# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per altadefinizione01
# ------------------------------------------------------------

from core import support

host = 'https://metalvideo.com'
headers = {'X-Requested-With': 'XMLHttpRequest'}


@support.menu
def mainlist(item):
    menu = [('Generi',['', 'genres']),
           ('Ultimi Video',['/videos/latest', 'peliculas']),
           ('Top Video',['/videos/top', 'peliculas']),
           ('Cerca...',['','search',])]
    return locals()


@support.scrape
def genres(item):
    item.url = host
    action = 'peliculas'
    patronBlock = r'<div class="swiper-slide">(?P<block>.*?)<button'
    patron = r'class="" href="(?P<url>[^"]+)[^>]+>(?P<title>[^<]+)<'
    def itemHook(item):
        item.thumbnail = support.thumb('music')
        item.contentType = 'music'
        return item
    return locals()

@support.scrape
def peliculas(item):
    # debug=True
    action = 'findvideos'
    patron= r'<a href="(?P<url>[^"]+)"[^>]+>\s*<img src="(?P<thumb>[^"]+)" alt="(?P<title>[^"]+)"[^>]*>'
    patronNext = r'<a href="([^"]+)" data-load="[^"]+" class="[^"]+" title="Next'
    typeContentDict = {'': 'music'}
    def itemHook(item):
        item.contentType = 'music'
        item.thumbnail = item.thumbnail.replace('https:','http:')
        return item
    return locals()


def findvideos(item):
    data = support.match(item, patron=r'<source src="[^"]+').match
    return support.server(item, Videolibrary=False, data=data)


def search(item, text):
    support.info(text)
    item.url = host + '/search?keyword=' + text
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
        return []

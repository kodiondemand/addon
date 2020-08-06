# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per filmpertutti.py
# ------------------------------------------------------------

import re

from core import scrapertools, httptools, support
from core.item import Item
from platformcode import config

def findhost():
    page = httptools.downloadpage("https://filmpertutti.nuovo.live/").data
    url = scrapertools.find_single_match(page, 'Il nuovo indirizzo di FILMPERTUTTI è <a href="([^"]+)')
    return url

host = config.get_channel_url(findhost)
headers = [['Referer', host]]



@support.menu
def mainlist(item):

    film = ['/category/film/',
            ('Generi', ['/category/film/', 'genres', 'lettersF'])
           ]

    tvshow = ['/category/serie-tv/',
              ('Aggiornamenti', ['/aggiornamenti-serie-tv/', 'peliculas', 'newest']),
              ('Per Lettera', ['/category/serie-tv/', 'genres', 'lettersS'])
             ]

    search = ''
    return locals()

@support.scrape
def peliculas(item):
    support.log()

    if item.args != 'newest':
        patronBlock = r'<ul class="posts">(?P<block>.*)<\/ul>'
        patron = r'<li><a href="(?P<url>[^"]+)" data-thumbnail="(?P<thumb>[^"]+)">.*?<div class="title">(?P<title>.+?)(?:\[(?P<lang>Sub-ITA)\])?(?:[ ]\[?(?P<quality>[HD]+)?\])?(?:[ ]\((?P<year>\d+)\)?)?<\/div>'
        patronNext = r'<a href="([^"]+)" >Pagina'

    else:
        patronBlock = r'<ul class="posts">(?P<block>.*)<div class="clear">'
        patron = r'<li>\s?<a href="(?P<url>[^"]+)" data-thumbnail="(?P<thumb>[^"]+)">.*?<div class="title">(?P<title>.+?)(?:\s\[(?P<quality>HD)\])?<\/div>[^>]+>(?:[\dx]+)\s?(?:[ ]\((?P<lang>[a-zA-Z\-]+)\))?.+?</div>'
        pagination = ''

    if item.args == 'search':
        action = 'select'
    elif item.contentType == 'tvshow':
        action = 'episodios'
    elif item.contentType == 'movie':
        action ='findvideos'
    else:
        action = 'select'

    def itemHook(item):
        item.title = item.title.replace(r'-', ' ')
        return item

    return locals()

@support.scrape
def episodios(item):
    # debug = True
    data = support.match(item.url, headers=headers).data
    if 'accordion-item' in data:
        patronBlock = r'<span class="season[^>]*>\d+[^>]+>[^>]+>[^>]+>[^>]+>\D*(?:STAGIONE|Stagione)[ -]+(?P<lang>[a-zA-Z\- ]+)[^<]*</span>(?P<block>.*?)<div id="(?:season|disqus)'
        patron = r'<img src="(?P<thumb>[^"]+)">.*?<li class="season-no">(?P<season>\d+)(?:&#215;|×|x)(?P<episode>\d+)[^<0-9]*<\/li>(?P<url>.*?javascript:;">(?P<title>[^<]+).*?</tbody>)'
    else:
        patronBlock = r'(?:STAGIONE|Stagione)(?:<[^>]+>)?\s*(?:(?P<lang>[A-Za-z- ]+))?(?P<block>.*?)(?:&nbsp;|<strong>|<div class="addtoany)'
        patron = r'(?:/>|p>)\s*(?P<season>\d+)(?:&#215;|×|x)(?P<episode>\d+)[^<]+(?P<url>.*?)(?:<br|</p)'
    def itemHook(item):
        item.title.replace('&#215;','x')
        if not item.contentLanguage:
            item.contentLanguage = 'ITA'
            return item
    return locals()


@support.scrape
def genres(item):

    if item.args == 'lettersF':
        item.contentType = 'movie'
    else:
        item.contentType = 'tvshow'

    action = 'peliculas'
    patronBlock = r'<select class="cats">(?P<block>.*?)<\/select>'
    patronMenu = r'<option data-src="(?P<url>[^"]+)">(?P<title>[^<]+)<\/option>'

    return locals()


def select(item):
    support.log()
    patron=r'class="taxonomy category" ><span property="name">([^>]+)</span></a><meta property="position" content="2">'
    block = support.match(item.url, patron=patron,headers=headers).match
    if block.lower() != 'film':
        support.log('select = ### è una serie ###')
        item.contentType='tvshow'
        return episodios(item)
    else:
        support.log('select = ### è un movie ###')
        item.contentType='movie'
        return findvideos(item)


def search(item, texto):
    support.log()
    item.url = host + "/?s=" + texto
    item.contentType = 'episode'
    item.args = 'search'
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.log("%s" % line)
        return []


def newest(categoria):
    support.log()
    itemlist = []
    item = Item()
    try:
        if categoria == "peliculas":
            item.url = host + "/category/film/"
            item.action = "peliculas"
            item.extra = "movie"
            item.contentType = 'movie'
            itemlist = peliculas(item)
        else:
            item.url = host + "/aggiornamenti-serie-tv/"
            item.action = "peliculas"
            item.args = "newest"
            item.contentType = 'tvshow'
            itemlist = peliculas(item)

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.log("{0}".format(line))
        return []

    return itemlist


def findvideos(item):
    if item.contentType == 'movie':
        data = httptools.downloadpage(item.url).data
        return support.server(item, data=data, patronTag='Versione: <[^>]+>([^<]+)')
    else:
        return support.server(item, item.url)

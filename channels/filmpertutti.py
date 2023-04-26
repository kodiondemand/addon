# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per filmpertutti.py
# ------------------------------------------------------------

from core import httptools, support
from core.item import Item
from platformcode import config

def findhost(url):
    page = httptools.downloadpage(url).data
    url = support.scrapertools.find_single_match(page, 'Il nuovo indirizzo di FILMPERTUTTI è ?<a href="([^"]+)')
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
    support.info()
    # debug = True
    #debugBlock = True
    # support.dbg()

    if item.args != 'newest':
        patronBlock = r'<ul class="posts">(?P<block>.*)<\/ul>'
        patron = r'<li><a href="(?P<url>[^"]+)" data-thumbnail="(?P<thumb>[^"]+)">.*?<div class="title[^"]*">(?P<title>.+?)(?:\[(?P<lang>Sub-ITA)\])?(?:[ ]\[?(?P<quality>[HD]+)?\])?(?:[ ]\((?P<year>\d+)\)?)?<\/div>'
        patronNext = r'<a href="([^"]+)[^>]+>Pagina'
    else:
        patronBlock = r'<ul class="posts">(?P<block>.*)<div class="clear[^"]*">'
        patron = r'<li>\s?<a href="(?P<url>[^"]+)" data-thumbnail="(?P<thumb>[^"]+)">.*?<div class="title[^"]*">(?P<title>[^<]+?)(?:\s\[(?P<quality>HD)\])?(?:\s\((?P<year>[0-9]{4})\))?<\/div>.*?<div class="episode[^"]*"[^>]+>(?P<episode>[^<(]+)(?:\((?P<lang>[a-zA-Z\-]+)\))?'

    if item.args == 'search':
        action = 'check'
    elif item.contentType == 'tvshow':
        action = 'episodios'
    elif item.contentType == 'movie':
        action ='findvideos'
    else:
        action = 'check'

    def itemHook(item):
        item.title = item.title.replace(' - La Serie', '')
        return item

    return locals()

@support.scrape
def episodios(item):
    # debug = True
    data = support.match(item.url, headers=headers).data
    if 'accordion-item' in data:
        patronBlock = r'<span class="season[^>]*>\d+[^>]+>[^>]+>[^>]+>[^>]+>\D*[Ss][Tt][Aa][Gg][Ii][Oo][Nn][Ee][ -]+(?P<lang>[a-zA-Z\- ]+)[^<]*</span>(?P<block>.*?)<div id="(?:season|disqus)'
        patron = r'<img src="(?P<thumb>[^"]+)"(?:[^>]*>){3,4}\s*<li class="season-no">(?P<season>\d+)(?:&#215;|×|x)(?P<episode>\d+)[^<0-9]*<\/li>(?P<data>.*?javascript:;">(?P<title>[^<]+).*?</tbody>)'
    else:
        patronBlock = r'[Ss][Tt][Aa][Gg][Ii][Oo][Nn][Ee](?:<[^>]+>)?\s*(?:(?P<lang>[A-Za-z- ]+))?(?P<block>.*?)(?:&nbsp;|<strong>|<div class="addtoany)'
        patron = r'(?:/>|p>)\s*(?P<season>\d+)(?:&#215;|×|x)(?P<episode>\d+)[^<]+(?P<data>.*?)(?:<br|</p)'

    def itemHook(i):
        i.url = item.url
        i.title.replace('&#215;','x')
        if not i.contentLanguage:
            i.contentLanguage = 'ITA'
        return i
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


def check(item):
    support.info()
    patron=r'class="taxonomy category"\s*><span property="name">([^>]+)</span></a><meta property="position" content="2">'
    block = support.match(item.url, patron=patron,headers=headers).match
    if block.lower() != 'film':
        support.info('select = ### è una serie ###')
        item.contentType='tvshow'
        return episodios(item)
    else:
        support.info('select = ### è un movie ###')
        item.contentType='movie'
        return findvideos(item)


def search(item, texto):
    support.info()
    item.url = host + "/search/" + texto
    item.args = 'search'
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.info("%s" % line)
        return []


def newest(categoria):
    support.info()
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
            support.info("{0}".format(line))
        return []

    return itemlist


def findvideos(item):
    if item.contentType == 'movie':
        data = support.match(item.url, patron=r'<a target="_blank" rel="nofollow" href="([^"]+)">').matches
        return support.server(item, data=data, patronTag='Versione: <[^>]+>([^<]+)')
    else:
        return support.server(item, item.data)

# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per AnimeUnity
# ------------------------------------------------------------

from core import support

host = support.config.get_channel_url()
headers = [['Referer', host]]


@support.menu
def mainlist(item):
    anime = ['/anime.php?c=archive&page=*',
            ('In Corso',['/anime.php?c=onair', 'peliculas']),
            ('Ultimi Episodi', ['', 'peliculas', 'news']),
            ('Ultimi Aggiunti', ['', 'peliculas', 'last'])
    ]
    return locals()


@support.scrape
def menu(item):
    action = 'peliculas'
    patronBlock = item.args + r' Categorie</a>\s*<ul(?P<block>.*?)</ul>'
    patronMenu = r'<a href="(?P<url>[^"]+)"[^>]+>(?P<title>[^>]+)<'
    return locals()


def search(item, text):
    support.log('search', item)
    item.url = host + '/anime.php?c=archive&page=*'
    item.search = text
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.log('search log:', line)
        return []


def newest(categoria):
    support.log(categoria)
    itemlist = []
    item = support.Item()
    item.url = host
    item.args = 'news'
    item.action = 'peliculas'
    try:
        itemlist = peliculas(item)

        if itemlist[-1].action == 'peliculas':
            itemlist.pop()
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.log(line)
        return []

    return itemlist


@support.scrape
def peliculas(item):
    # debug = True
    pagination = 20
    anime = True
    if item.args == 'news':
        patron = r'col-lg-3 col-md-6 col-sm-6 col-xs-6 mobile-col">\s*<a href="(?P<url>[^"]+)">[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s*<img class="[^"]+" src="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>[^-]+)\D+Episodio\s*(?P<episode>\d+)'
        patronNext = r'page-link" href="([^"]+)">'
    elif item.args == 'last':
        patronBlock = r'ULTIME AGGIUNTE[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<block>.*?)<div class="row"'
        patron = r'<img class="[^"]+" src="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+>\s*<a class="[^"]+" href="(?P<url>[^"]+)"\s*>(?P<title>[^<]+)</a>'
    else:
        search = item.search
        patron = r'<div class="card-img-top archive-card-img"> <a href="(?P<url>[^"]+)"> <img class="[^"]+" src="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>[^<\(]+)(?:\((?P<lang>[^\)]+)\))?'
    return locals()


@support.scrape
def episodios(item):
    # debug = True
    data = item.data
    anime = True
    pagination = 50
    patron = r'<a href="(?P<url>[^"]+)" class="\D+ep-button">(?P<episode>\d+)'
    def itemHook(item):
        item.title = item.title + support.typo(item.fulltitle,'-- bold')
        return item
    return locals()


def findvideos(item):
    support.log()
    html = support.match(item, patron=r'TIPO:\s*</b>\s*([A-Za-z]+)')
    if html.match == 'TV' and item.contentType != 'episode':
        item.contentType = 'tvshow'
        item.data = html.data
        return episodios(item)
    else:
        itemlist = []
        if item.contentType != 'episode': item.contentType = 'movie'
        video = support.match(html.data, patron=r'<source src="([^"]+)"').match
        itemlist.append(item.clone(action="play", title='Diretto', url=video, server='directo'))
    return support.server(item, itemlist=itemlist)

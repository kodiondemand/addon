# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per PufiMovies
# ------------------------------------------------------------

from core import support
from platformcode import logger

host = support.config.get_channel_url()




headers = [['Referer', host]]


@support.menu
def mainlist(item):
    film = [
        ('Generi', ['', 'menu', 'Film']),
        ('Più Visti', ['','movies', 'most'])
    ]

    tvshow = ['',
        ('Generi', ['', 'menu', 'Serie Tv']),
        ('Ultimi Episodi', ['','movies', 'last'])
    ]

    search = ''
    return locals()


@support.scrape
def menu(item):
    action = 'movies'
    patronBlock = item.args + r' Categorie</a>\s*<ul(?P<block>.*?)</ul>'
    patronMenu = r'<a href="(?P<url>[^"]+)"[^>]+>(?P<title>[^>]+)<'
    return locals()


def search(item, text):
    logger.debug('search', item)
    itemlist = []
    text = text.replace(' ', '+')
    item.url = host + '/search/keyword/' + text
    try:
        item.args = 'search'
        itemlist = movies(item)
        if itemlist[-1].action == 'movies':
            itemlist.pop()
        return itemlist
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error('search log:', line)
        return []


def newest(category):
    logger.debug(category)
    itemlist = []
    item = support.Item()
    item.url = host
    item.action = 'movies'
    try:
        if category == 'movie':
            item.contentType = 'movie'
            itemlist = movies(item)
        else:
            item.args = 'last'
            item.contentType = 'tvshow'
            itemlist = movies(item)

        if itemlist[-1].action == 'movies':
            itemlist.pop()
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

    return itemlist


@support.scrape
def movies(item):
    if item.contentType == 'tvshow' and not item.args:
        action = 'episodes'
        patron = r'<div class="movie-box">\s*<a href="(?P<url>[^"]+)">[^>]+>[^>]+>\D+Streaming\s(?P<lang>[^"]+)[^>]+>[^>]+>[^>]+>(?P<quality>[^<]+)[^>]+>[^>]+>[^>]+>\s*<img src="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>(?P<rating>[^<]+)<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>[^<]+)[^>]+>[^>]+>[^>]+>\s*(?P<year>\d+)'
    elif item.contentType == 'movie' and not item.args:
        patron = r'<div class="existing_item col-6 col-lg-3 col-sm-4 col-xl-4">\s*<div class="movie-box">\s*<a href="(?P<url>(?:http(?:s)://[^/]+)?/(?P<type>[^/]+)/[^"]+)">[^>]+>[^>]+>\D+Streaming\s*(?P<lang>[^"]+)">[^>]+>[^>]+>(?P<quality>[^<]+)<[^>]+>[^>]+>[^>]+>\s*<img src="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>(?P<rating>[^<]+)<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>[^<]+)[^>]+>[^>]+>[^>]+>\s*(?:(?P<year>\d+))?[^>]+>[^>]+>[^>]+>[^>]+>(?P<plot>[^<]*)<'
    elif item.args == 'last':
        patron = r'<div class="episode-box">[^>]+>[^>]+>[^>]+>\D+Streaming\s(?P<lang>[^"]+)">[^>]+>[^>]+>(?P<quality>[^<]+)<[^>]+>[^>]+>[^>]+>[^^>]+>[^>]+>\s*<img src="(?P<thumb>[^"]+)"[^[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s*<a href="(?P<url>[^"]+)"[^>]+>[^>]+>(?P<title>[^<]+)<[^>]+>[^>]+>[^>]+>\D*(?P<season>\d+)[^>]+>\D*(?P<episode>\d+)'
    elif item.args == 'most':
        patron =r'div class="sm-113 item">\s*<a href="(?P<url>[^"]+)">[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s<img src="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s*(?P<title>[^<]+)'
    else:
        patron = r'<div class="movie-box">\s*<a href="(?P<url>(?:http(?:s)://[^/]+)?/(?P<type>[^/]+)/[^"]+)">[^>]+>[^>]+>\D+Streaming\s*(?P<lang>[^"]+)">[^>]+>[^>]+>(?P<quality>[^<]+)<[^>]+>[^>]+>[^>]+>\s*<img src="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>(?P<rating>[^<]+)<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>[^<]+)[^>]+>[^>]+>[^>]+>\s*(?:(?P<year>\d+))?[^>]+>[^>]+>[^>]+>[^>]+>(?P<plot>[^<]*)<'
        typeActionDict = {'findvideos':['movie'], 'episodes':['tvshow']}
        typeContentDict = {'movie':['movie'], 'tvshow':['tvshow']}
    patronNext = r'<a href="([^"]+)"[^>]+>&raquo;'
    return locals()


@support.scrape
def episodes(item):
    patron = r'<div class="episode-box">[^>]+>[^>]+>[^>]+>\D+Streaming\s(?P<lang>[^"]+)">[^>]+>[^>]+>(?P<quality>[^<]+)<[^>]+>[^>]+>[^>]+>\s*<img src="(?P<thumb>[^"]+)"[^[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s*<a href="(?P<url>[^"]+)"[^>]+>[^>]+>(?P<title>[^<]+)<[^>]+>[^>]+>[^>]+>\D*(?P<season>\d+)[^>]+>\D*(?P<episode>\d+)'
    return locals()


def findvideos(item):
    logger.debug()
    # match = support.match(item, patron='wstream', debug=True)
    return support.server(item)

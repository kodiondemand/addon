# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Filmi Gratis
# ------------------------------------------------------------
"""
    La voce "Al cinema" si riferisce ai titoli che scorrono nella home page

    Problemi:
        - Nessuno noto

    Novità, il canale, è presente in:
       - FILM
"""
import re

from core import httptools, support
from core.item import Item
from platformcode import config

host = config.get_channel_url()

list_servers = ['verystream', 'openload', 'streamango', 'vidoza', 'okru']
list_quality = ['1080p', '720p', '480p', '360']

headers = [['Referer', host]]


@support.menu
def mainlist(item):
    film = [
        ('Al Cinema ', ['', 'peliculas', 'cinema']),
        ('Categorie', ['', 'genres', 'genres']),
    ]

    tvshow = ['/serie/ALL',
        ('Generi', ['', 'genres', 'genres'])
    ]

    search = ''
    return locals()

@support.scrape
def peliculas(item):
    support.log()

    if item.args == 'search':
        action = ''
        patron = r'<div class="cnt">.*?src="([^"]+)"[^>]+>[^>]+>[^>]+>\s+(?P<title>.+?)(?:\[(?P<lang>Sub-ITA|SUB-ITA|SUB)\])?\s?(?:\[?(?P<quality>HD).+\]?)?\s?(?:\(?(?P<year>\d+)?\)?)?\s+<[^>]+>[^>]+>[^>]+>\s<a href="(?P<url>[^"]+)"[^<]+<'
        patronBlock = r'<div class="container">(?P<block>.*?)</main>'
    elif item.contentType == 'movie':
        if not item.args:
            # voce menu: Film
            patronBlock = r'<h1>Film streaming ita in alta definizione</h1>(?P<block>.*?)<div class="content-sidebar">'
            patron = r'<div class="timeline-right">[^>]+>\s<a href="(?P<url>.*?)".*?src="(?P<thumb>.*?)".*?<h3 class="timeline-post-title">(?:(?P<title>.+?)\s\[?(?P<lang>Sub-ITA)?\]?\s?\[?(?P<quality>HD)?\]?\s?\(?(?P<year>\d+)?\)?)<'
            patronNext = r'<a class="page-link" href="([^"]+)">>'
        elif item.args == 'cinema':
            patronBlock = r'<div class="owl-carousel" id="postCarousel">(?P<block>.*?)<section class="main-content">'
            patron = r'background-image: url\((?P<thumb>.*?)\).*?<h3.*?>(?:(?P<title>.+?)\s\[?(?P<lang>Sub-ITA)?\]?\s?\[?(?P<quality>HD)?\]?\s?\(?(?P<year>\d+)?\)?)<.+?<a.+?<a href="(?P<url>[^"]+)"[^>]+>'
        elif item.args == 'genres':
            # ci sono dei titoli dove ' viene sostituito con " da support
            data = httptools.downloadpage(item.url, headers=headers, ignore_response_code=True).data
            data = re.sub('\n|\t', ' ', data)
            patron = r'<div class="cnt">\s.*?src="([^"]+)".+?title="((?P<title>.+?)(?:[ ]\[(?P<lang>Sub-ITA|SUB-ITA)\])?(?:[ ]\[(?P<quality>.*?)\])?(?:[ ]\((?P<year>\d+)\))?)"\s*[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s+<a href="(?P<url>[^"]+)"'
            patronBlock = r'<div class="container">(?P<block>.*?)</main>'
            pagination = ''

        patronNext = '<a class="page-link" href="([^"]+)">>>'
    else:
        action = 'episodios'
        patron = r'<div class="cnt">\s.*?src="([^"]+)".+?title="((?P<title>.+?)(?:[ ]\[(?P<lang>Sub-ITA|SUB-ITA)\])?(?:[ ]\[(?P<quality>.*?)\])?(?:[ ]\((?P<year>\d+)\))?)"\s*[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s+<a href="(?P<url>[^"]+)"'
##        if item.args == 'search':
##            patron = r'<div class="cnt">.*?src="([^"]+)".+?[^>]+>[^>]+>[^>]+>\s+((?P<title>.+?)(?:[ ]\[(?P<lang>Sub-ITA|SUB-ITA)\])?(?:[ ]\[(?P<quality>.*?)\])?(?:[ ]\((?P<year>\d+)\))?)\s+<[^>]+>[^>]+>[^>]+>[ ]<a href="(?P<url>[^"]+)"'
        patronBlock = r'<div class="container">(?P<block>.*?)</main>'

    def itemHook(item):
        if item.args == 'search':
            if 'series' in item.url:
                item.action = 'episodios'
                item.contentType = 'tvshow'
            else:
                item.action = 'findvideos'
                item.contentType = 'movie'
        return item

    #debug = True
    return locals()


@support.scrape
def episodios(item):
    support.log()

    action = 'findvideos'
    patronBlock = r'<div class="row">(?P<block>.*?)<section class="main-content">'
    patron = r'href="(?P<url>.*?)">(?:.+?)?\s+S(?P<season>\d+)\s\-\sEP\s(?P<episode>\d+)[^<]+<'

    return locals()

@support.scrape
def genres(item):
    support.log()

    if item.contentType == 'movie':
        action = 'peliculas'
        patron = r'<a href="(?P<url>.*?)">(?P<title>.*?)<'
        patronBlock = r'CATEGORIES.*?<ul>(?P<block>.*?)</ul>'
    else:
        item.contentType = 'tvshow'
        action = 'peliculas'
        blacklist = ['Al-Cinema']
        patron = r'<a href="(?P<url>.*?)">(?P<title>.*?)<'
        patronBlock = r'class="material-button submenu-toggle"> SERIE TV.*?<ul>.*?</li>(?P<block>.*?)</ul>'

    return locals()


def search(item, text):
    support.log('search', item)

    text = text.replace(' ', '+')
    item.url = host + '/search/?s=' + text
    try:
        item.args = 'search'
        return peliculas(item)
    # Se captura la excepcion, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            support.log('search log:', line)
        return []

def newest(categoria):
    support.log('newest ->', categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = host
            item.contentType = 'movie'
            item.action = 'peliculas'
            itemlist = peliculas(item)

            if itemlist[-1].action == 'peliculas':
                itemlist.pop()
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.log({0}.format(line))
        return []

    return itemlist

def findvideos(item):
    support.log()
    return support.server(item)

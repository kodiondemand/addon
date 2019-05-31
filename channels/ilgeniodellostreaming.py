# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per ilgeniodellostreaming
# ------------------------------------------------------------
import re

from platformcode import  logger
from core import scrapertoolsV2, httptools, tmdb, support
from core.support import log, menu, aplay
from core.item import Item

host = "https://ilgeniodellostreaming.pw"

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['verystream', 'openload', 'streamango']
list_quality = ['default']

headers = [['Referer', host]]

PERPAGE = 10

def mainlist(item):
    log()
    itemlist = []
    menu(itemlist, 'Film', 'peliculas', host + '/film/')
    menu(itemlist, 'Film Per Categoria', 'category', host, args='genres')
    menu(itemlist, 'Film Per Anno', 'category', host, args='year')
    menu(itemlist, 'Serie TV', 'peliculas', host + '/serie/', 'episode')
    menu(itemlist, 'Nuovi Episodi Serie TV submenu', 'newep', host + '/aggiornamenti-serie/', 'episode')
    menu(itemlist, 'Anime', 'peliculas', host + '/anime/', 'episode')
    menu(itemlist, 'TV Show', 'peliculas', host + '/tv-show/', 'episode')
    menu(itemlist, 'Cerca...', 'search', contentType='search')
    aplay(item, itemlist, list_servers, list_quality)
    return itemlist


def newest(categoria):
    log(categoria)
    itemlist = []
    item = Item()

    try:
        if categoria == 'peliculas':
            item.contentType = 'movie'
            item.url = host + '/film/'
        elif categoria == "series":
            item.contentType = 'episode'
            item.url = host + '/serie/'
        elif categoria == "anime":
            item.contentType = 'episode'
            item.url = host + '/anime/'

        item.action = "peliculas"
        itemlist = peliculas(item)

        if itemlist[-1].action == "peliculas":
            itemlist.pop()
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def category(item):
    return support.scrape(item, r'<li.*?><a href="(.*?)"[^>]+>(.*?)<\/a>' ,['url', 'title'], action='peliculas', patron_block= r'<ul class="' + item.args + r' scrolling">(.*?)<\/ul>')


def search(item, texto):
    log(texto)
    item.url = host + "/?s=" + texto

    try:
        return peliculas(item)

    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)

    return []


def peliculas_src(item):
    patron = r'<div class="thumbnail animation-2"><a href="([^"]+)"><img src="([^"]+)" alt="[^"]+" \/>[^>]+>([^<]+)<\/span>.*?<a href.*?>([^<]+)<\/a>[^>]+>[^>]+>(?:<span class="rating">IMDb\s*([0-9.]+)<\/span>)?.*?(?:<span class="year">([0-9]+)<\/span>)?[^>]+>[^>]+><p>(.*?)<\/p>'
    return support.scrape(item, patron, ['url', 'thumb', 'type', 'title', 'lang' 'rating', 'year', 'plot'], headers, type_content_dict={'movie':['Film'], 'episode':['TV']}, type_action_dict={'findvideos':['Film'], 'episodios':['TV']})
    

def peliculas(item):
    if item.contentType == 'movie':
        patron = r'<div class="poster">\s*<a href="([^"]+)"><img src="([^"]+)" alt="[^"]+"><\/a>[^>]+>[^>]+>[^>]+>\s*([0-9.]+)<\/div><span class="quality">([^<]+)<\/span>[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)<\/a>[^>]+>[^>]+>([^<]+)<\/span>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)<div'
        return support.scrape(item, patron, ['url', 'thumb', 'rating', 'quality', 'title', 'year', 'plot'], headers, patronNext='<span class="current">[^<]+<[^>]+><a href="([^"]+)"')
    elif item.contentType == 'episode':
        patron = r'<div class="poster">\s*<a href="([^"]+)"><img src="([^"]+)" alt="[^"]+"><\/a>[^>]+>[^>]+>[^>]+> ([0-9.]+)<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)<[^>]+>[^>]+>[^>]+>([^<]+)<.*?<div class="texto">([^<]+)'
        return support.scrape(item, patron, ['url', 'thumb', 'rating', 'title', 'year', 'plot'], headers, action='episodios', patronNext='<span class="current">[^<]+<[^>]+><a href="([^"]+)"')
    else:
        patron = r'<div class="thumbnail animation-2"><a href="([^"]+)"><img src="([^"]+)" alt="[^"]+" \/>[^>]+>([^<]+)<\/span>.*?<a href.*?>([^<]+)<\/a>[^>]+>[^>]+>(?:<span class="rating">IMDb\s*([0-9.]+)<\/span>)?.*?(?:<span class="year">([0-9]+)<\/span>)?[^>]+>[^>]+><p>(.*?)<\/p>'
        return support.scrape(item, patron, ['url', 'thumb', 'type', 'title', 'lang' 'rating', 'year', 'plot'], headers, type_content_dict={'movie':['Film'], 'episode':['TV']}, type_action_dict={'findvideos':['Film'], 'episodios':['TV']})

def newep(item):
    log()
    itemlist = []

    page = 1
    if item.page:
        page = item.page

    matches = support.match(item, r'<div class="poster"><img src="([^"]+)" alt="([^"]+)">[^>]+><a href="([^"]+)">')[0]

    for i, (thumb, title, url) in enumerate(matches):
        if (page - 1) * PERPAGE > i: continue
        if i >= page * PERPAGE: break
        title = scrapertoolsV2.decodeHtmlentities(title)
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 fulltitle=title,
                 show=title,
                 title= support.typo(title,'bold'),
                 url=url,
                 thumbnail=thumb))
    support.pagination(itemlist, item, page, PERPAGE)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

def episodios(item):
    return support.scrape(item, r'<a href="([^"]+)"><img src="([^"]+)">.*?<div class="numerando">([^<]+).*?<div class="episodiotitle">[^>]+>([^<]+)<\/a>',['url', 'thumb', 'episode', 'title'], patron_block='<div id="seasons">(.*?)<div class="sbox')

def findvideos(item):
    log()
    itemlist =[]
    matches, data = support.match(item, '<iframe class="metaframe rptss" src="([^"]+)"[^>]+>',headers=headers)
    for url in matches:
        html = httptools.downloadpage(url, headers=headers).data
        data += str(scrapertoolsV2.find_multiple_matches(html, '<meta name="og:url" content="([^"]+)">'))
    itemlist = support.server(item, data)
    return itemlist


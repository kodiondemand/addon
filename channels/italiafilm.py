# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per 'italifilm'
# ------------------------------------------------------------

from core import support, httptools
from platformcode import config

host = config.get_channel_url()
headers = [['Referer', host]]


@support.menu
def mainlist(item):
    menu = [
            ('Film', ['/film/', 'list', 'film']),
            ('Per Genere', ['', 'list', 'genere']),
            ('Al Cinema', ['/cinema/', 'list', 'film']),
            ('Sub-ITA', ['/sub-ita/', 'list', 'film']),
            ('Top del Mese', ['/top-del-mese.html', 'list', 'film'])
           ]
    search = ''

    return locals()


@support.scrape
def list(item):
    actLike = 'peliculas'
    if item.args == 'genere':
        patronBlock = r'<ul class="sub-menu">(?P<block>.*?)</ul>'
        patronMenu = r'<li><a href="(?P<url>[^"]+)">(?P<title>[^<]+)'
        action = 'peliculas'
    elif item.args == 'film':
        patron = r'<div class="entry-summary.*?<a href="(?P<url>[^"]+)" title="(?P<title>[^\("]+)(?:\((?P<year>\d+)\))" class="[^"]+"><img class="lazyload" data-src="(?P<thumb>[^"]+)" alt="[^"]+".*?></a>'
        patronNext = r'<a href="([^"]+)">(?:&rarr|→)'

    return locals()


@support.scrape
def peliculas(item):
    patronBlock = r'<div class="entry-summary">(?P<block>.*?)</div>'
    patron = r'<a href="(?P<url>[^"]+)" title="(?P<title>[^\("]+)(?:\((?P<year>\d+)\)).*?class="[^"]+"><img class="lazyload" data-src="(?P<thumb>[^"]+)" alt="[^"]+".*?></a>'
    patronNext = r'<a href="([^"]+)">(?:&rarr|→)'
    return locals()


@support.scrape
def search(item, text):
    actLike = 'peliculas'
    support.info('search', text)
    data = httptools.downloadpage(item.url, post={"story": text,"do": "search","subaction": "search"}).data
    patron = r'<div class="entry-summary.*?<a href="(?P<url>[^"]+)" title="(?P<title>[^"]+)(?:\((?P<year>\d+)\))" class="[^"]+"><img class="lazyload" data-src="(?P<thumb>[^"]+)" alt="[^"]+".*?></a>'

    return locals()


#action di default
def findvideos(item):

    support.info('findvideos')
    urls = []
    data = support.match(item).data
    matches = support.match(data, patron=r'<iframe.*?src="([^"]+)').matches

    for m in matches:
        if 'youtube' not in m and not m.endswith('.js'):
            urls += support.match(m, patron=r'data-link="([^"]+)').matches
    return support.server(item, urls)

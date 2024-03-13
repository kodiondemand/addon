# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per 'italifilm'
# ------------------------------------------------------------

from core import support, httptools, scrapertools, tmdb
from platformcode import config, logger

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

def peliculas(item):
    data = httptools.downloadpage(item.url).data
    itemlist = []
    for it in support.match(data, patron=[r'<div class="entry-summary.*?<a href="(?P<url>[^"]+)" title="(?P<title>[^"]+)(?:\((?P<year>\d+)\))" class="[^"]+"><img class="lazyload" data-src="(?P<thumb>[^"]+)" alt="[^"]+".*?></a>']).matches:
        infoLabels = dict()
        infoLabels['title'] = it[1]
        infoLabels['mediatype'] = 'movie'
        infoLabels['year'] = it[2]
        itemlist.append(item.clone(action='findvideos', thumbnail = host + it[3].replace(' ','%20'), title = support.cleantitle(it[1]), url= it[0], infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    if item.args == 'search':
        next = support.match(data, patron=['<a name="nextlink".*list_submit\((\d+)\);.*(?:&rarr|→)']).matches
    else:
        next = support.match(data, patron=['<a href="([^"]+)">(?:&rarr|→)']).matches

    if next:
        if item.args == 'search':
            item.url = "{}/?{}".format(host, support.urlencode({"story": item.search_text,"do": "search","subaction": "search", "search_start": next[0]}))
        else: 
            item.url = next[0]
        support.nextPage(itemlist = itemlist, item = item, next_page=item.url)

    return itemlist


def search(item, text):
    item.args = 'search'
    item.url = "{}/?{}".format(host, support.urlencode({"story": text,"do": "search","subaction": "search", "search_start": item.page}))
    item.search_text = text
    try:
        return peliculas(item)

    except:
        import sys
        for line in sys.exc_info():
            logger.error("search except: %s" % line)
        return []

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

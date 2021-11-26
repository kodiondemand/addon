# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per AnimeForce
# ------------------------------------------------------------

from core import scrapertools, support
from platformcode import logger

host = support.config.get_channel_url()
headers = [['Referer', host]]


@support.menu
def mainlist(item):
    anime = ['/lista-anime/',
             ('In Corso',['/anime/anime-status/in-corso/', 'movies', 'status']),
             ('Completi',['/anime/anime-status/completo/', 'movies', 'status']),
             ('Genere',['/anime', 'submenu', 'genre']),
             ('Anno',['/anime', 'submenu', 'anime-year']),
             ('Tipologia',['/anime', 'submenu', 'anime-type']),
             ('Stagione',['/anime', 'submenu', 'anime-season']),
             ('Ultime Serie',['/category/anime/articoli-principali/','movies','last'])
            ]
    return locals()


@support.scrape
def submenu(item):
    action = 'movies'
    patronBlock = r'data-taxonomy="' + item.args + r'"(?P<block>.*?)</select'
    patronMenu = r'<option class="level-\d+ (?P<u>[^"]+)"[^>]+>(?P<title>[^(]+)[^\(]+\((?P<num>\d+)'
    if 'genre' in item.args:
        patronGenreMenu = patronMenu
    def itemHook(item):
        item.url += host + '/anime/' + item.args + '/' + item.u
        # item.title = support.typo(item.t, 'bold')
        return item
    return locals()


def newest(category):
    logger.debug(category)
    itemlist = []
    item = support.Item()
    try:
        if category == "anime":
            item.contentType = 'tvshow'
            item.url = host
            item.args = 'newest'
            return movies(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist

def search(item, text):
    logger.debug(text)
    item.search = text
    item.url = host + '/lista-anime/'
    item.contentType = 'tvshow'
    try:
        return movies(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


@support.scrape
def movies(item):
    search = item.search
    numerationEnabled = True
    if 'movie' in item.url:
        action = 'findvideos'
    else:
        action = 'check'

    if not item.args:
        pagination = True
        patron = r'<a\s*href="(?P<url>[^"]+)"\s*title="(?P<title>[^"]+)">'
    else:
        patron = r'<a href="(?P<url>[^"]+)"[^>]+>\s*<img src="(?P<thumb>[^"]+)" alt="(?P<title>.*?)(?: Sub| sub| SUB|")'

    if item.args == 'newest': item.action = 'findvideos'

    def itemHook(item):
        if 'sub-ita' in item.url:
            item.contentLanguage = 'Sub-ITA'
        return item

    return locals()


def check(item):
    m = support.match(item, headers=headers, patron=r'Tipologia[^>]+><a href="([^"]+)"')
    item.data = m.data
    if 'movie' in m.match:
        item.contentType = 'movie'
        return findvideos(item)
    else:
        return episodes(item)

def episodes(item):
    @support.scrape
    def _episodes(item):
        actLike = 'episodes'
        disableAll = True
        data = item.data

        if '<h6>Streaming</h6>' in data:
            patron = r'<td style[^>]+>\s*.*?(?:<span[^>]+)?<strong>(?P<episode>[^<]+)<\/strong>.*?<td style[^>]+>\s*<a href="(?P<url>[^"]+)"[^>]+>'
        else:
            patron = r'<a\s*href="(?P<url>[^"]+)"[^>]+>(?P<episode>\d+)[<-](?P<episode2>\d+)?'

        def itemHook(item):
            if item.url.startswith('//'): item.url= 'https:' + item.url
            elif item.url.startswith('/'): item.url= 'https:/' + item.url
            return item
        action = 'findvideos'
        return locals()

    itemlist = support.itemlistdb() if item.itemlist else []
    groups = support.match(item.data, patron=[r'"tabpanel">.*?</div', r'Special-tab">.*?</div']).matches
    for group in groups:
        item.data = group
        if 'Special' in group:
            item.contentSeason = 0
        itemlist.extend(_episodes(item))

    from platformcode.autorenumber import start
    start(itemlist, item)
    itemlist = support.season_pagination(itemlist, item, function_level='episodes')
    return itemlist




def findvideos(item):
    logger.debug()
    itemlist = []

    if 'adf.ly' in item.url:
        from servers.decrypters import adfly
        url = adfly.get_long_url(item.url)

    elif 'bit.ly' in item.url:
        url = support.httptools.downloadpage(item.url, only_headers=True, follow_redirects=False).headers.get("location")

    else:
        url = host
        for u in item.url.split('/'):
            if u and 'animeforce' not in u and 'http' not in u:
                url += '/' + u

        if 'php?' in url:
            url = support.httptools.downloadpage(url, only_headers=True, follow_redirects=False).headers.get("location")
            url = support.match(url, patron=r'class="button"><a href=(?:")?([^" ]+)', headers=headers).match
        else:
            if item.data: url = item.data
            url = support.match(url, patron=r'data-href="([^"]+)" target').match
            if not url: url = support.match(url, patron=[r'<source src=(?:")?([^" ]+)',r'name="_wp_http_referer" value="([^"]+)"']).match
        if url.startswith('//'): url = 'https:' + url
        elif url.startswith('/'): url = 'https:/' + url
        if 'vvvvid' in url: itemlist.append(item.clone(action="play", title='VVVVID', url=url, server='vvvvid'))
        else: itemlist.append(item.clone(action="play", title=support.config.getLocalizedString(30137), url=url, server='directo'))

    return support.server(item, itemlist=itemlist)

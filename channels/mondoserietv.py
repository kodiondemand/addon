# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per mondoserietv
# ----------------------------------------------------------

from core import support
from platformcode import logger

host = support.config.get_channel_url()
headers = {'Referer': host}


@support.menu
def mainlist(item):

    film = ['/lista-film',
            ('Ultimi Film Aggiunti', ['/ultimi-film-aggiunti', 'movies' , 'last'])]

    tvshow = ['/lista-serie-tv',
              ('HD {TV}', ['/lista-serie-tv-in-altadefinizione']),
              ('Anni 50 60 70 80 {TV}',['/lista-serie-tv-anni-60-70-80']),
              ('Serie Italiane',['/lista-serie-tv-italiane'])]

    anime = ['/lista-cartoni-animati-e-anime']

    docu = [('Documentari {bullet bold}',['/lista-documentari', 'movies', '', 'tvshow'])]

    search = ''

    return locals()


def search(item, text):
    logger.debug(text)
    if item.contentType == 'movie' or item.extra == 'movie':
        action = 'findvideos'
    else:
        action = 'episodes'
    item.args = 'search'
    item.url = host + "?a=b&s=" + text
    try:
        return movies(item)
    # Continua la ricerca in caso di errore .
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(category):
    logger.debug(category)
    item = support.Item()
    try:
        if category == 'tvshow':
            item.contentType= 'tvshow'
            item.url = host + '/ultimi-episodi-aggiunti'
            item.args = "lastep"
        if category == "movie":
            item.contentType= 'movie'
            item.url = host + '/ultimi-film-aggiunti'
            item.args = "last"
        return movies(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []


@support.scrape
def movies(item):
    pagination = True
    numerationEnabled = True
    patronNext = r'href="([^"]+)" title="[^"]+" class="lcp_nextlink"'
    action = 'findvideos'
    # debug=True
    if item.args == 'last':
        patronBlock = r'<table>(?P<block>.*?)</table>'
        patron = r'<tr><td><a href="(?P<url>[^"]+)">\s*[^>]+>(?P<title>.*?)(?:\s(?P<year>\d{4}))?\s*(?:Streaming|</b>)'
    elif item.args == 'lastep':
        patronBlock = r'<table>(?P<block>.*?)</table>'
        patron = r'<td>\s*<a href="[^>]+>(?P<title>.*?)(?:\s(?P<year>\d{4}))?\s(?:(?P<episode>(?:\d+x\d+|\d+)))\s*(?P<title2>[^<]+)(?P<url>.*?)<tr>'
    elif item.args == 'search':
        patronBlock = r'<div class="movies">(?P<block>.*?)<div id="paginador"'
        patron = r'class="item">\s*<a href="(?P<url>[^"]+)">\s*<div class="image">\s*<img src="(?P<thumb>[^"]+)" alt="(?P<title>.+?)(?:"| \d{4}).*?<span class="ttx">(?P<plot>[^<]+)<div class="degradado">[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s*(?:<span class="imdbs">(?P<rating>[^<]+))?(?:[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<year>\d+))?'
        def itemHook(item):
            if '/film/' in item.url:
                item.contentType = 'movie'
                item.action = 'findvideos'
            else:
                item.contentType = 'tvshow'
                item.action = 'episodes'
            return item
    else:
        patronBlock = r'<div class="entry-content pagess">(?P<block>.*?)</ul>'
        patron = r'<li\s*><a href="(?P<url>[^"]+)" title="(?P<title>.*?)(?:\s(?P<year>\d{4}))?"[^>]*>'
    if item.contentType == 'tvshow':
        action = 'episodes'
        numerationEnabled = True
    return locals()


@support.scrape
def episodes(item):
    numerationEnabled = True
    pagination = True
    patronBlock = r'<table>(?P<block>.*?)</table>'
    patron = r'<tr><td><b>(?P<title>(?:\d+)?.*?)\s*(?:(?P<episode>(?:\d+x\d+|\d+)))\s*(?P<title2>[^<]+)(?P<data>.*?)<tr>'
    def itemHook(item):
        clear = support.re.sub(r'\[[^\]]+\]', '', item.title)
        if clear.isdigit():
            item.title = support. typo('Episodio ' + clear, 'bold')
        return item
    return locals()

def findvideos(item):
    if item.contentType == 'movie': return support.server(item)
    else: return support.server(item, item.data)

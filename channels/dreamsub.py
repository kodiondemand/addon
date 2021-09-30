# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per 'dreamsub'
# ------------------------------------------------------------

from core import support
from platformcode import logger

host = support.config.get_channel_url()
headers = [['Referer', host]]

@support.menu
def mainlist(item):
    anime = ['/search?typeY=tv',
            ('Movie', ['/search?typeY=movie', 'movies', '', 'movie']),
            ('OAV', ['/search?typeY=oav', 'movies', '', 'tvshow']),
            ('Spinoff', ['/search?typeY=spinoff', 'movies', '', 'tvshow']),
            ('Generi', ['','menu','Generi']),
            ('Stato', ['','menu','Stato']),
            ('Ultimi Episodi', ['', 'movies', ['last', 'episodiRecenti']]),
            ('Ultimi Aggiornamenti', ['', 'movies', ['last', 'episodiNuovi']])
             ]

    return locals()


@support.scrape
def menu(item):
    item.contentType = ''
    action = 'movies'

    patronBlock = r'<div class="filter-header"><b>%s</b>(?P<block>.*?)<div class="filter-box">' % item.args
    patronMenu = r'<a class="[^"]+" data-state="[^"]+" (?P<other>[^>]+)>[^>]+></i>[^>]+></i>[^>]+></i>(?P<title>[^>]+)</a>'

    if 'generi' in item.args.lower():
        patronGenreMenu = patronMenu

    def itemHook(item):
        for Type, ID in support.match(item.other, patron=r'data-type="([^"]+)" data-id="([^"]+)"').matches:
            item.url = host + '/search?' + Type + 'Y=' + ID
        return item
    return locals()


def search(item, text):
    logger.debug(text)

    text = text.replace(' ', '+')
    item.url = host + '/search/' + text
    item.args = 'search'
    try:
        return movies(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error('search log:', line)
        return []


def newest(category):
    logger.debug(category)
    item = support.Item()
    try:
        if category == "anime":
            item.url = host
            item.args = ['last', 'episodiNuovi']
            return movies(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []



@support.scrape
def movies(item):
    # debug = True
    numerationEnabled = True
    if 'movie' in item.url:
        item.contentType = 'movie'
        action = 'findvideos'
    else:
        item.contentType = 'tvshow'
        action = 'episodes'

    if len(item.args) > 1 and item.args[0] == 'last':
        patronBlock = r'<div id="%s"[^>]+>(?P<block>.*?)<div class="vistaDettagliata"' % item.args[1]
        patron = r'<li>\s*<a href="(?P<url>[^"]+)" title="(?P<title>[^"]+)" class="thumb">[^>]+>[^>]+>[^>]+>\s*[EePp]+\s*(?P<episode>\d+)[^>]+>\s<img src="(?P<thumb>[^"]+)"'
    else:
        patron = r'<div class="showStreaming">\s*<b>(?P<title>[^<]+)[^>]+>[^>]+>\s*<span>Lingua:\s*(?:DUB|JAP)?\s*(?P<lang>(?:SUB )?ITA)[^>]+>[<>br\s]+a href="(?P<url>[^"]+)"[^>]+>.*?--image-url:url\(/*(?P<thumb>[^\)]+).*?Anno di inizio</b>:\s*(?P<year>[0-9]{4})'
        patronNext = '<li class="currentPage">[^>]+><li[^<]+<a href="([^"]+)">'

    def itemHook(item):
        if item.thumbnail and not item.thumbinail.startswith('http'):
            item.thumbnail = 'http://' + item.thumbnail
        return item

    return locals()


@support.scrape
def episodes(item):
    numerationEnabled = True
    pagination = True

    if item.data:
        data = item.data

    patron = r'<div class="sli-name">\s*<a href="(?P<url>[^"]+)"[^>]+>(?P<title>[^<]+)<'

    return locals()


def findvideos(item):
    itemlist = []
    logger.debug()

    matches = support.match(item, patron=r'href="([^"]+)"', patronBlock=r'<div style="white-space: (.*?)<div id="main-content"')

    if not matches.matches and item.contentType != 'episode':
        item.data = matches.data
        item.contentType = 'tvshow'
        return episodes(item)

    if 'vvvvid' in matches.data:
        itemlist.append(item.clone(action="play", title='VVVVID', url=support.match(matches.data, patron=r'(http://www.vvvvid[^"]+)').match, server='vvvvid'))
    else:
        logger.debug('VIDEO')
        for url in matches.matches:
            lang = url.split('/')[-2]
            if 'ita' in lang.lower():
                language = 'ITA'
            if 'sub' in lang.lower():
                language = 'Sub-' + language
            quality = url.split('/')[-1].split('?')[0]
            url += '|User-Agent=' + support.httptools.get_user_agent() + '&Referer=' + url

            itemlist.append(item.clone(action="play", title='', url=url, contentLanguage = language, quality = quality, order = quality.replace('p','').zfill(4), server='directo',))
    return support.server(item, itemlist=itemlist)


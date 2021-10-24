# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per 'dreamsub'
# ------------------------------------------------------------

from core import support

host = support.config.get_channel_url()
headers = [['Referer', host]]

@support.menu
def mainlist(item):
    support.info(item)

    anime = ['/search?typeY=tv',
            ('Movie', ['/search?typeY=movie', 'peliculas', '', 'movie']),
            ('OAV', ['/search?typeY=oav', 'peliculas', '', 'tvshow']),
            ('Spinoff', ['/search?typeY=spinoff', 'peliculas', '', 'tvshow']),
            ('Generi', ['','menu','Generi']),
            ('Stato', ['','menu','Stato']),
            ('Ultimi Episodi', ['', 'peliculas', ['last', 'episodiRecenti']]),
            ('Ultimi Aggiornamenti', ['', 'peliculas', ['last', 'episodiNuovi']])
             ]

    return locals()


@support.scrape
def menu(item):
    item.contentType = ''
    action = 'peliculas'
    

    patronBlock = r'<div class="filter-header"><b>%s</b>(?P<block>.*?)<div class="filter-box">' % item.args
    patronMenu = r'<a class="[^"]+" data-state="[^"]+" (?P<other>[^>]+)>[^>]+></i>[^>]+></i>[^>]+></i>(?P<title>[^>]+)</a>'

    def itemHook(item):
        support.info(item.type)
        for Type, ID in support.match(item.other, patron=r'data-type="([^"]+)" data-id="([^"]+)"').matches:
            item.url = host + '/search?' + Type + 'Y=' + ID
        return item
    return locals()


def search(item, text):
    support.info(text)

    text = text.replace(' ', '+')
    item.url = host + '/search/' + text
    item.args = 'search'
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.info('search log:', line)
        return []


def newest(categoria):
    support.info(categoria)
    item = support.Item()
    try:
        if categoria == "anime":
            item.url = host
            item.args = ['last', 'episodiNuovi']
            return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("{0}".format(line))
        return []



@support.scrape
def peliculas(item):
    # debug = True
    anime = True
    if 'movie' in item.url:
        item.contentType = 'movie'
        action = 'findvideos'
    else:
        item.contentType = 'tvshow'
        action = 'episodios'

    if len(item.args) > 1 and item.args[0] == 'last':
        patronBlock = r'<div id="%s"[^>]+>(?P<block>.*?)<div class="vistaDettagliata"' % item.args[1]
        patron = r'<li>\s*<a href="(?P<url>[^"]+)" title="(?P<title>[^"]+)" class="thumb">[^>]+>[^>]+>[^>]+>\s*[EePp]+\s*(?P<episode>\d+)[^>]+>\s+<img src="(?P<thumb>[^"]+)"'
    else:
        patron = r'<div class="showStreaming">\s*<b>(?P<title>[^<]+)[^>]+>[^>]+>\s*<span>Lingua:\s*(?:DUB|JAP)?\s*(?P<lang>(?:SUB )?ITA)[^>]+>[<>br\s]+a href="(?P<url>[^"]+)"[^>]+>.*?--image-url:url\(/*(?P<thumb>[^\)]+).*?Anno di inizio</b>:\s*(?P<year>[0-9]{4})'
        patronNext = '<li class="currentPage">[^>]+><li[^<]+<a href="([^"]+)">'

    def itemHook(item):
        if item.thumbnail and not item.thumbinail.startswith('http'):
            item.thumbnail = 'http://' + item.thumbnail
        return item

    return locals()


@support.scrape
def episodios(item):
    anime = True
    # debug = True
    pagination = 100

    if item.data:
        data = item.data

    patron = r'<div class="sli-name">\s*<a\s+href="(?P<url>[^"]+)"[^>]+>(?P<title>[^<]+)<'

    return locals()


def findvideos(item):
    itemlist = []
    support.info()
    # support.dbg()

    matches = support.match(item, patron=r'href="([^"]+)"', patronBlock=r'<div style="white-space: (.*?)<div id="main-content"')

    if not matches.matches and item.contentType != 'episode':
        item.data = matches.data
        item.contentType = 'tvshow'
        return episodios(item)

    if 'vvvvid' in matches.data:
        itemlist.append(item.clone(action="play", title='VVVVID', url=support.match(matches.data, patron=r'(http://www.vvvvid[^"]+)').match, server='vvvvid'))
    else:
        support.info('VIDEO')
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


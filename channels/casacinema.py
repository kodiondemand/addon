# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per 'casacinema'
# ------------------------------------------------------------


from core import support

host = support.config.get_channel_url()
headers = [['Referer', host]]


@support.menu
def mainlist(item):
    film = ['/category/film',
        ('Generi', ['', 'genres', 'genres']),
        ]

    tvshow = ['/category/serie-tv',
        ('Novità', ['/aggiornamenti-serie-tv', 'peliculas', '']),
        ]

    search = ''

    return locals()


@support.scrape
def genres(item):
    action = 'peliculas'
    blacklist = ['PRIME VISIONI', 'ULTIME SERIE TV', 'ULTIMI FILM']
    patronMenu = r'<li><a href="(?P<url>[^"]+)">(?P<title>[^<>]+)</a></li>'
    patronBlock = r'<div class="container home-cats">(?P<block>.*?)<div class="clear">'
    return locals()


def check(item):
    item.data = support.match(item).data
    if 'episodi e stagioni' in item.data.lower():
        support.info('select = ### è una serie ###')
        item.contentType = 'tvshow'
        return episodios(item)
    else:
        support.info('select = ### è un film ###')
        item.contentType = 'movie'
        return findvideos(item)


def search(item, text):
    support.info(text)
    text = text.replace(' ', '+')
    item.url = host + '/?a=b&s=' + text
    item.args = 'search'
    try:
        return peliculas(item)

    except:
        import sys
        for line in sys.exc_info():
            support.info('search log:', line)
        return []


def newest(categoria):
    itemlist = []
    item = support.Item()
    item.args = 'newest'

    try:
        if categoria == 'series':
            item.contentType = 'tvshow'
            item.url = host+'/aggiornamenti-serie-tv'

        else:
            item.contentType = 'movie'
            item.url = host+'/category/film'

        item.action = 'peliculas'
        itemlist = peliculas(item)

        if itemlist[-1].action == 'peliculas':
            itemlist.pop()

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.info("%s" % line)
        return []

    return itemlist


@support.scrape
def peliculas(item):
    if item.contentType == 'movie':
        action = 'findvideos'
    elif item.contentType == 'tvshow':
        action = 'episodios'
        pagination = ''
    else:
        action = 'check'

    if item.args == 'newest':
        patron = r'<li><a href="(?P<url>[^"]+)"[^=]+="(?P<thumb>[^"]+)"><div>\s*?<div[^>]+>(?P<title>[^\(\[<]+)(?:\[(?P<quality1>HD)\])?[ ]?(?:\(|\[)?(?P<lang>[sS]ub-[iI][tT][aA])?(?:\)|\])?[ ]?(?:\[(?P<quality>.+?)\])?[ ]?(?:\((?P<year>\d+)\))?<(?:[^>]+>.+?(?:title="Nuovi episodi">(?P<episode>\d+x\d+)[ ]?(?P<lang2>Sub-Ita)?|title="IMDb">(?P<rating>[^<]+)))?'
    else:
        patron = r'<li><a href="(?P<url>[^"]+)"[^=]+="(?P<thumb>[^"]+)"><div>\s*?<div[^>]+>(?P<title>[^\(\[<]+)(?P<title2>\([\D*]+\))?(?:\[(?P<quality1>HD)\])?\s?(?:[\(\[])?(?P<lang>[sS]ub-[iI][tT][aA])?(?:[\)\]])?\s?(?:\[(?P<quality>.+?)\])?\s?(?:\((?P<year>\d+)\))?(?:\(\D{2}\s\d{4}\))?<'

    patronNext = r'<a href="([^"]+)"\s*>Pagina'


    def itemHook(item):
        if item.quality1:
            item.quality = item.quality1
            item.title += support.typo(item.quality, '_ [] color kod')
        if item.lang2:
            item.contentLanguage = item.lang2
            item.title += support.typo(item.lang2, '_ [] color kod')
        if item.args == 'novita':
            item.title = item.title

        return item
    return locals()


@support.scrape
def episodios(item):
    if item.data:
        data = item.data
    action = 'findvideos'
    item.contentType = 'tvshow'
    blacklist = ['']
    patron = r'"season-no">(?P<season>\d+)x(?P<episode>\d+)(?:[^>]+>){5}\s*(?P<title>[^<]+)(?P<data>.*?)</table>'
    patronBlock = r'<span>(?:.+?Stagione*.+?(?P<lang>[Ii][Tt][Aa]|[Ss][Uu][Bb][\-]?[iI][tT][aA]))?.*?</span>.*?class="content(?P<block>.*?)(?:"accordion-item|<script>)'
    return locals()


def findvideos(item):
    if item.contentType != 'movie':
        links = support.match(item.data, patron=r'href="([^"]+)"').matches
    else:
        matchData = item.data if item.data else support.match(item.url, headers=headers).data
        links = support.match(matchData, patron=r'data-id="([^"]+)"').matches

    return support.server(item, links)

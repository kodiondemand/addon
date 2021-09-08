# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per fastsubita.py
# ------------------------------------------------------------
"""

    Su questo canale, nella categoria 'Ricerca Globale'
    non saranno presenti le voci 'Aggiungi alla Videoteca'
    e 'Scarica Film'/'Scarica Serie', dunque,
    la loro assenza, nel Test, NON dovrà essere segnalata come ERRORE.

    Novità. Indicare in quale/i sezione/i è presente il canale:
       - serie

    Ulteriori info:
        - SOLO SUB-ITA

"""
from core import support, httptools
from core.item import Item
from platformcode import config, logger

host = config.get_channel_url()
headers = [['Referer', host]]


@support.menu
def mainlist(item):

    Tvshow = [
        ('Aggiornamenti', ['', 'peliculas', 'update']),
        ('Cerca... {bold}{TV}', ['', 'search'])
    ]

    # search = ''

    return locals()


@support.scrape
def peliculas(item):
    # support.dbg()
    deflang = 'Sub-ITA'

    # è una singola pagina con tutti gli episodi
    if item.grouped and not support.scrapertools.find_single_match(item.url, '-[0-9]+x[0-9]+-'):
        item.grouped = False
        return episodios_args(item)

    # ogni puntata è un articolo a se
    if item.fulltitle:
        item.url = host + '?s=' + item.fulltitle
        actLike = 'episodios'

    action = 'findvideos'
    blacklist = ['']
    if item.args == 'genres':
        patronBlock = r'<h4 id="mctm1-.">'+item.fulltitle+'</h4>(?P<block>.+?)</div>'
        patron = r'[^>]+>[^>]+>.+?href="(?P<url>[^"]+)[^>]>(?P<title>[^<]+)\s<'
        action = 'episodios'
    elif item.args == 'search':
        group = True
        patronBlock = r'</header>(?P<block>.*?)</main>'
        patron = '(?:<img[^>]+src="(?P<thumb>[^"]+)".*?)?<a href="(?P<url>[^"]+)"[^>]+>(?P<title>[^<]+?)(?:(?P<episode>\d+&#215;\d+|\d+×\d+)|\[[sS](?P<season>[0-9]+)[^]]+\])\s?(?:(?P<lang>\([a-zA-Z\s]+\)) (?:[Ss]\d+[Ee]\d+)?\s?(?:[&#\d;|.{3}]+)(?P<title2>[^”[<]+)(?:&#\d)?)?'
    else:
        # è una singola pagina con tutti gli episodi
        if item.args != 'update' and not support.scrapertools.find_single_match(item.url, '-[0-9]+x[0-9]+-'):
            return episodios_args(item)
        patron = r'<div class="featured-thumb"> +<a href="(?P<url>[^"]+)" title="(?P<title>[^[]+)\[(?P<episode>\d+&#215;\d+)?'
        patronBlock = r'<main id="main"[^>]+>(?P<block>.*?)<div id="secondary'

    # def itemlistHook(itemlist):
    #     from core import scraper
    #     return scraper.sort_episode_list(itemlist)

    patronNext = '<a class="next page-numbers" href="(.*?)">Successivi'

    # debug = True
    return locals()


def episodios_args(item):
    actLike = 'episodios'
    # support.dbg()

    deflang = 'Sub-ITA'
    action = 'findvideos'
    patron = '(?P<episode>\d+&#215;\d+|\d+[Ã.]+\d+)(?:\s?\((?P<lang>[a-zA-Z ]+)\))?(?:\s[Ss]\d+[Ee]+\d+)? +(?:“|&#8220;)(?P<title2>.*?)(?:”|&#8221;).*?(?P<other>.*?)(?:/>|<p)'
    patronBlock = r'<main id="main" class="site-main" role="main">(?P<block>.*?)</main>'
    patronNext = '<a class="next page-numbers" href="(.*?)">Successivi'

    # debug = True
    return locals()


@support.scrape
def episodios(item):
    return episodios_args(item)


@support.scrape
def genres(item):
    logger.debug()
    #support.dbg()

    action = 'peliculas'
    patronBlock = r'<div id="mcTagMapNav">(?P<block>.+?)</div>'
    patron = r'<a href="(?P<url>[^"]+)">(?P<title>.+?)</a>'

    def itemHook(item):
        item.url = host+'/elenco-serie-tv/'
        item.contentType = 'tvshow'
        return item

    #debug = True
    return locals()


def search(item, text):
    logger.debug('search', text)
    text = text.replace(' ', '+')
    item.url = host + '?s=' + text
    try:
        item.args = 'search'
        item.contentType = 'tvshow'
        return peliculas(item)
    # Se captura la excepcion, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error('search log:', line)
        return []


def newest(categoria):
    logger.debug('newest ->', categoria)
    itemlist = []
    item = Item()
    if categoria == 'series':
        try:
            item.contentType = 'tvshow'
            item.args = 'newest'
            item.url = host
            item.action = 'peliculas'
            itemlist = peliculas(item)

            if itemlist[-1].action == 'peliculas':
                itemlist.pop()
        # Continua la ricerca in caso di errore
        except:
            import sys
            for line in sys.exc_info():
                logger.error('newest log: ', line)
            return []

    return itemlist


def findvideos(item):
    logger.debug('findvideos ->', item)
    patron = r'<a href="([^"]+)">'

    itemlist = []
    if item.other.startswith('http'):
        resp = httptools.downloadpage(item.url, follow_redirects=False)
        data = resp.headers.get("location", "") + '\n'
    elif item.other:
        html = support.match(item.other, patron=patron, headers=headers)
        matches = html.matches
        data = html.data
        for scrapedurl in matches:
            if 'is.gd' in scrapedurl:
                resp = httptools.downloadpage(scrapedurl, follow_redirects=False)
                data += resp.headers.get("location", "") + '\n'
    elif not support.scrapertools.find_single_match(item.url, '-[0-9]+x[0-9]+-'):
        return episodios(item)
    else:
        patronBlock = '<div class="entry-content">(?P<block>.*)<footer class="entry-footer">'
        html = support.match(item, patron=patron, patronBlock=patronBlock, headers=headers)
        matches = html.matches
        data= html.data

        if item.args != 'episodios':
            item.infoLabels['mediatype'] = 'episode'
        for scrapedurl in matches:
            if 'is.gd' in scrapedurl:
                resp = httptools.downloadpage(scrapedurl, follow_redirects=False)
                data += resp.headers.get("location", "") + '\n'

    itemlist += support.server(item, data)

    # data = support.match(item.url).data
    # patron = r'>Posted in <a href="https?://fastsubita.com/serietv/([^/]+)/(?:[^"]+)?"'
    # series = scrapertools.find_single_match(data, patron)
    # titles = support.typo(series.upper().replace('-', ' '), 'bold color kod')
    # goseries = support.typo("Vai alla Serie:", ' bold color kod')
    # itemlist.append(
    #     item.clone(channel=item.channel,
    #                # title=goseries + titles,
    #                title=titles,
    #                fulltitle=titles,
    #                show=series,
    #                contentType='tvshow',
    #                contentSerieName=series,
    #                url=host+"/serietv/"+series,
    #                action='episodios',
    #                contentTitle=titles,
    #                plot = "Vai alla Serie " + titles + " con tutte le puntate",
    #                ))

    return itemlist

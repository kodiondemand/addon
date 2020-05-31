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
from core import support, httptools, scrapertools
from core.item import Item
from core.support import log
from platformcode import config

host = config.get_channel_url()
headers = [['Referer', host]]
list_servers = ['wstream', 'upstream', 'flashx', 'vidoza', 'vidtome']
list_quality = ['default']


@support.menu
def mainlist(item):

    Tvshow = [
        ('Aggiornamenti', ['', 'peliculas', '', 'update']),
        ('Per Lettera {TV}', ['/elenco-serie-tv/', 'genres', 'genres']),
        ('Cerca... {bold}{TV}', ['','search'])
    ]

    # search = ''

    return locals()


@support.scrape
def peliculas(item):
    support.log(item)
    # support.dbg()
    deflang = 'Sub-ITA'

    action = 'findvideos'
    blacklist = ['']
    if item.args == 'genres':
        patronBlock = r'<h4 id="mctm1-.">'+item.fulltitle+'</h4>(?P<block>.+?)</div>'
        patron = r'[^>]+>[^>]+>.+?href="(?P<url>[^"]+)[^>]>(?P<title>[^<]+)\s<'
        action = 'episodios'
    elif item.args == 'search':
        patronBlock = r'</h1> </header>(?P<block>.*?)</main>'
        patronMenu = r'(?:<img src="(?P<thumb>[^"]+)"[^>]+>)?[^>]+>[^>]+>[^>]+>[^>]+>[^>]+><a href="(?P<url>[^"]+)"[^>]+>(?:(?P<title>.+?)[ ](?P<episode>[\d&#;\d]+\d+|\d+..\d+)(?: \([a-zA-Z\s]+\) )(?:s\d+e\d+)?[ ]?(?:[&#\d;|.{3}]+)(?P<title2>[^&#\d;|^.{3}]+)(?:|.+?))<'
    else:
        patron = r'<div class="featured-thumb"> <a href="(?P<url>[^"]+)" title="(?:(?P<title>.+?)[ ]?(?P<episode>\d+&#215;\d+).+?&#8220;(?P<title2>.+?)&#8221;).+?">'
        patronBlock = r'<main id="main"[^>]+>(?P<block>.*?)<div id="secondary'

    patronNext = '<a class="next page-numbers" href="(.*?)">Successivi'

    #debug = True
    return locals()


@support.scrape
def episodios(item):
    support.log(item)
    #support.dbg()

    deflang = 'Sub-ITA'
    action = 'findvideos'
    blacklist = ['']
    patron = r'<div class="featured-thumb"> <a href="(?P<url>[^"]+)" title="(?:(?P<title>.+?)[ ]?(?P<episode>\d+&#215;\d+|\d+[Ã.]+\d+).+?&#8220;(?P<title2>.+?)&#8221;).+?">'
    patronBlock = r'<main id="main" class="site-main" role="main">(?P<block>.*?)</main>'
    patronNext = '<a class="next page-numbers" href="(.*?)">Successivi'

    #debug = True
    return locals()

@support.scrape
def genres(item):
    support.log()
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
    support.log('search', item)
    itemlist = []
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
            log('search log:', line)
        return []


def newest(categoria):
    support.log('newest ->', categoria)
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
                support.log('newest log: ', {0}.format(line))
            return []

    return itemlist


def findvideos(item):
    support.log('findvideos ->', item)
    itemlist = []
    patronBlock = '<div class="entry-content">(?P<block>.*)<footer class="entry-footer">'
    patron = r'<a href="([^"]+)">'
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

    data = support.match(item.url).data
    patron = r'>Posted in <a href="https?://fastsubita.com/serietv/([^/]+)/(?:[^"]+)?"'
    series = scrapertools.find_single_match(data, patron)
    titles = support.typo(series.upper().replace('-', ' '), 'bold color kod')
    goseries = support.typo("Vai alla Serie:", ' bold color kod')
    itemlist.append(
        Item(channel=item.channel,
                title=goseries + titles,
                fulltitle=titles,
                show=series,
                contentType='tvshow',
                contentSerieName=series,
                url=host+"/serietv/"+series,
                action='episodios',
                contentTitle=titles,
                plot = "Vai alla Serie " + titles + " con tutte le puntate",
                ))

    return itemlist

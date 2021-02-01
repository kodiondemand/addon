# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per 'cinemaLibero'
# ------------------------------------------------------------

import re

from core import httptools, support, scrapertools
from core.item import Item
from platformcode import config


# rimanda a .today che contiene tutti link a .plus
# def findhost(url):
#     permUrl = httptools.downloadpage('https://www.cinemalibero.online/', follow_redirects=False).headers
#     try:
#         import urlparse
#     except:
#         import urllib.parse as urlparse
#     p = list(urlparse.urlparse(permUrl['location'].replace('https://www.google.com/search?q=site:', '')))
#     if not p[0]:
#         p[0] = 'https'
#     return urlparse.urlunparse(p)

host = config.get_channel_url()
headers = [['Referer', host]]

@support.menu
def mainlist(item):

    film = ['/category/film/',
            ('Novità', ['', 'peliculas', 'update']),
            ('Generi', ['', 'genres'])]

    tvshow = ['/category/serie-tv/']

    anime = ['/category/anime-giapponesi/']

##    Sport = [(support.typo('Sport', 'bullet bold'), ['/category/sport/', 'peliculas', 'sport', 'tvshow'])]
    news = [('Ultimi episodi Serie/Anime', ['/aggiornamenti-serie-tv/', 'peliculas', 'update', 'tvshow'])]

    search = ''

    return locals()


@support.scrape
def peliculas(item):
    # debug = True
    action = 'check'
    patronBlock = r'<div class="container">.*?class="col-md-12[^"]*?">(?P<block>.*?)<div class=(?:"container"|"bg-dark ")>'
    if item.args == 'newest':
        patron = r'<div class="col-lg-3">[^>]+>[^>]+>\s<a href="(?P<url>[^"]+)".+?url\((?P<thumb>[^\)]+)\)">[^>]+>(?P<title>[^<]+)<[^>]+>[^>]+>(?:[^>]+>)?\s?(?P<rating>[\d\.]+)?[^>]+>.+?(?:[ ]\((?P<year>\d{4})\))?<[^>]+>[^>]+>(.?[\d\-x]+\s\(?(?P<lang>[sSuUbBiItTaA\-]+)?\)?\s?(?P<quality>[\w]+)?[|]?\s?(?:[fFiInNeE]+)?\s?\(?(?P<lang2>[sSuUbBiItTaA\-]+)?\)?)?'
        pagination = 25
    elif item.contentType == 'movie':
        patron = r'<a href="(?P<url>[^"]+)" title="(?P<title>.+?)(?:[ ]\[(?P<lang>[sSuUbB\-iItTaA]+)\])?(?:[ ]\((?P<year>\d{4})\))?"\s*alt="[^"]+"\s*class="[^"]+"(?: style="background-image: url\((?P<thumb>.+?)\)">)?\s*<div class="voto">[^>]+>[^>]+>.(?P<rating>[\d\.a-zA-Z\/]+)?[^>]+>[^>]+>[^>]+>(?:<div class="genere">(?P<quality>[^<]+)</div>)?'
        if item.args == 'update':
            patronBlock = r'<section id="slider">(?P<block>.*?)</section>'
            patron = r'<a href="(?P<url>(?:https:\/\/.+?\/(?P<title>[^\/]+[a-zA-Z0-9\-]+)(?P<year>\d{4})))/".+?url\((?P<thumb>[^\)]+)\)">'
    elif item.contentType == 'tvshow':
        if item.args == 'update':
            patron = r'<a href="(?P<url>[^"]+)"[^<]+?url\((?P<thumb>.+?)\)">\s+<div class="titolo">(?P<title>.+?)(?: &#8211; Serie TV)?(?:\([sSuUbBiItTaA\-]+\))?[ ]?(?P<year>\d{4})?</div>[ ](?:<div class="genere">)?(?:[\w]+?\.?\s?[\s|S]?[\dx\-S]+?\s\(?(?P<lang>[iItTaA]+|[sSuUbBiItTaA\-]+)\)?\s?(?P<quality>[HD]+)?|.+?\(?(?P<lang2>[sSuUbBiItTaA\-]+)?\)?</div>)'
            pagination = 25
        else:
            patron = r'<a href="(?P<url>[^"]+)"\s*title="(?P<title>[^"\(]+)(?:"|\()(?:(?P<year>\d+)[^"]+)?.*?url\((?P<thumb>[^\)]+)\)(?:.*?<div class="voto">[^>]+>[^>]+>\s*(?P<rating>[^<]+))?.*?<div class="titolo">[^>]+>(?:<div class="genere">[^ ]*(?:\s\d+)?\s*(?:\()?(?P<lang>[^\)< ]+))?'
    else:
        patron = r'<div class="col-lg-3">[^>]+>[^>]+>\s*<a href="(?P<url>[^"]+)".+?url\((?P<thumb>[^\)]+)\)">[^>]+>[^>]+>[^>]+>(?:[^>]+>)?\s?(?P<rating>[\d\.]+)?[^>]+>(?P<title>.+?)(?:[ ]\((?P<year>\d{4})\))?<[^>]+>[^>]+>(.?[\d\-x]+\s\(?(?P<lang>[sSuUbBiItTaA\-]+)?\)?\s?(?P<quality>[\w]+)?[|]?\s?(?:[fFiInNeE]+)?\s?\(?(?P<lang2>[sSuUbBiItTaA\-]+)?\)?)?'

    def itemHook(item):
        if 'sub' in item.contentLanguage.lower() and not 'ita' in item.contentLanguage.lower():
            item.contentLanguage= 'Sub-ITA'
            item.title = re.sub('[Ss]ub(?:-)?', item.contentLanguage, item.title)
        if item.lang2:
            if len(item.lang2)<3:
                item.lang2 = 'ITA'
            item.contentLanguage = item.lang2
            item.title += support.typo(item.lang2, '_ [] color kod')
        if item.args == 'update':
            item.title = item.title.replace('-', ' ')

        return item

    patronNext = r'<a class="next page-numbers".*?href="([^"]+)">'
    return locals()

@support.scrape
def episodios(item):
    data=item.data
    # debug=True
    if item.args == 'anime':
        support.info("Anime :", item)
        # blacklist = ['Clipwatching', 'Verystream', 'Easybytez', 'Flix555', 'Cloudvideo']
        patron = r'<a target=(?P<url>[^>]+>(?P<title>Episodio\s(?P<episode>\d+))(?::)?(?:(?P<title2>[^<]+))?.*?(?:<br|</p))'
        patronBlock = r'(?:Stagione (?P<season>\d+))?(?:</span><br />|</span></p>|strong></p>)(?P<block>.*?)(?:<div style="margin-left|<span class="txt_dow">)'
        item.contentType = 'tvshow'
    elif item.args == 'serie':
        support.info("Serie :", item)
        patron = r'(?:>| )(?P<episode>\d+(?:x|×|&#215;)\d+)[;]?[ ]?(?:(?P<title>[^<–-]+)(?P<data>.*?)|(\2[ ])(?:<(\3.*?)))(?:</a><br /|</a></p|$)'
        patronBlock = r'>(?:[^<]+[Ss]tagione\s|[Ss]tagione [Uu]nica)(?:(?P<lang>iTA|ITA|Sub-ITA|Sub-iTA))?.*?</strong>(?P<block>.+?)(?:<strong|<div class="at-below)'
        item.contentType = 'tvshow'
    else:
        patron = r'(?P<title>\s*[0-9]{2}/[0-9]{2}/[0-9]{4})(?P<data>.*?)(?:<br|</p)'

    def itemHook(item):
        if not scrapertools.find_single_match(item.title, r'(\d+x\d+)'):
            item.title = re.sub(r'(\d+) -', '1x\\1', item.title)
        return item

    return locals()


@support.scrape
def genres(item):

    action='peliculas'
    patron_block=r'<div id="bordobar" class="dropdown-menu(?P<block>.*?)</li>'
    patronMenu=r'<a class="dropdown-item" href="(?P<url>[^"]+)" title="(?P<title>[A-z]+)"'

    return locals()


def search(item, texto):
    support.info(item.url,texto)
    texto = texto.replace(' ', '+')
    item.url = host + "/?s=" + texto
    # item.contentType = 'tv'
    item.args = 'search'
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.info("%s" % line)
    return []

def newest(categoria):
    support.info('newest ->', categoria)
    itemlist = []
    item = Item()
    item.args = 'newest'
    try:
        if categoria == 'series' or categoria == 'anime':
            item.args = 'update'
            item.url = host+'/aggiornamenti-serie-tv/'
            item.contentType = 'tvshow'
        item.action = 'peliculas'
        itemlist = peliculas(item)
    except:
        import sys
        for line in sys.exc_info():
            support.info('newest log: ', (line))
        return []

    return itemlist


def check(item):
    support.info()
    data = support.match(item.url, headers=headers).data
    if data:
        ck = support.match(data, patron=r'Supportaci condividendo quest[oa] ([^:]+)').match.lower()

        if ck == 'serie tv':
            item.contentType = 'tvshow'
            item.args = 'serie'
            item.data = data
            return episodios(item)

        elif ck == 'anime':
            item.contentType = 'tvshow'
            item.args = 'anime'
            item.data = data
            return episodios(item)

        elif ck == 'film':
            item.contentType = 'movie'
            item.data = data
            return findvideos(item)

        else:
            item.contentType = 'tvshow'
            item.data = data
            itemlist = episodios(item)
            if not itemlist:
                item.contentType = 'movie'
                item.data = data
                return findvideos(item)
            return itemlist


def findvideos(item):
    support.info()
    item.data = item.data.replace('http://rapidcrypt.net/verys/', '').replace('http://rapidcrypt.net/open/', '') #blocca la ricerca
    return support.server(item, data=item.data)

# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Eurostreaming
# by Greko
# ------------------------------------------------------------

from core import support
from core.item import Item

# def findhost(url):
#     permUrl = httptools.downloadpage(url, follow_redirects=False, only_headers=True).headers
#     host = 'https://'+permUrl['location'].replace('https://www.google.it/search?q=site:', '')
#     return host

host = support.config.get_channel_url()
headers = [['Referer', host]]

@support.menu
def mainlist(item):
    support.info()
    tvshow = []
    anime = ['/category/anime-cartoni-animati/']
    mix = [('Aggiornamenti {bullet bold} {TV}', ['/aggiornamento-episodi-nuovi/', 'peliculas', 'newest']),
           ('Archivio {bullet bold} {TV}', ['/category/serie-tv-archive/', 'peliculas'])]
    search = ''

    return locals()


@support.scrape
def peliculas(item):
    # debug = True
    action = 'episodios'
    
    if item.args == 'newest':
        item.contentType = 'episode'
        patron = r'<span class="serieTitle" style="font-size:20px">(?P<title>[^<]+) –\s*<a href="(?P<url>[^"]+)"[^>]*>\s+?(?P<episode>\d+[×x]\d+-\d+|\d+[×x]\d+) (?P<title2>[^<\(]+)\s?\(?(?P<lang>SUB ITA)?\)?</a>'
        pagination = ''
    else:
        patron = r'<div class="post-thumb">.*?<img src="(?P<thumb>[^"]+)".*?><a href="(?P<url>[^"]+)"[^>]+>(?P<title>.+?)\s?(?: Serie Tv)?\s?\(?(?P<year>\d{4})?\)?<\/a><\/h2>'
        patronNext=r'a class="next page-numbers" href="?([^>"]+)">Avanti &raquo;</a>'

    return locals()


@support.scrape
def episodios(item):
    # debug = True
    data = support.match(item, headers=headers).data
    if 'clicca qui per aprire' in data.lower(): data = support.match(support.match(data, patron=r'"go_to":"([^"]+)"').match.replace('\\',''), headers=headers).data
    elif 'clicca qui</span>' in data.lower(): data = support.match(support.match(data, patron=r'<h2 style="text-align: center;"><a href="([^"]+)">').match, headers=headers).data
    patronBlock = r'</span>(?P<block>[a-zA-Z\s]+\d+(.+?)?(?:\()?(?P<lang>ITA|SUB ITA)(?:\))?.*?)</div></div>'
    patron = r'(?P<season>\d+)&#\d+;(?P<episode>\d+(?:-\d+)?)\s*(?:</strong>|<em>)?\s*(?P<title>.*?)(?:â|-.+?-|Ã¢ÂÂ.+?Ã¢ÂÂ|Ã¢ÂÂ|em|.)?(?:/em.*?)?(?:<a (?P<other>.*?))?<br />'

    def itemHook(i):
        i.url = item.url
        return i

    return locals()


def search(item, texto):
    support.info()

    item.url = "%s/?s=%s" % (host, texto)
    item.contentType = 'tvshow'

    try:
        return peliculas(item)

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.info(line)
        return []


def newest(categoria):
    support.info()

    itemlist = []
    item = Item()
    item.contentType = 'tvshow'
    item.args = 'newest'
    try:
        item.url = "%s/aggiornamento-episodi-nuovi/" % host
        item.action = "peliculas"
        itemlist = peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.info("{0}".format(line))
        return []

    return itemlist


def findvideos(item):
    support.info()
    itemlist = support.server(item, item.other)
    # testo che tutti i link siano stati risolti
    if support.logger.testMode:
        if len(itemlist) < len(support.match(item.other, patron='<a href="([^"]+)').matches):
            raise Exception('Manca qualche server')
    return itemlist


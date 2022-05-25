# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Eurostreaming.Actor
# by Napster32
# ------------------------------------------------------------

from core import support
from core.item import Item

host = support.config.get_channel_url()
headers = [['Referer', host]]

@support.menu
def mainlist(item):
    support.info()
    tvshow = []
    anime = ['/animazione/']
    mix = [('Aggiornamenti {bullet bold} {TV}', ['/aggiornamento-episodi/', 'peliculas', 'newest'])]
    search = ''

    return locals()


@support.scrape
def peliculas(item):
    action = 'episodios'

    if item.args == 'newest':
        item.contentType = 'episode'
        patron = r'<span class="serieTitle" style="font-size:20px">(?P<title>[^<]+) –\s*<a href="(?P<url>[^"]+)"[^>]*>(?P<episode>\d+[×x]\d+-\d+|\d+[×x]\d+) (?P<title2>[^<\(]+)\s?\(?(?P<lang>SUB ITA)?\)?</a>'
        pagination = r'class="next".*?"(.+?)"'
    else:
        patron = r'<div class="post-thumb">.*?<img src="(?P<thumb>[^"]+)".*?><a href="(?P<url>[^"]+)"[^>]+>(?P<title>.+?)\s?(?: Serie Tv)?\s?\(?(?P<year>\d{4})?\)?<\/a><\/h2>'
        patronNext=r'a class="next page-numbers" href="?([^>"]+)">Avanti &raquo;</a>'

    return locals()


@support.scrape
def episodios(item):
    data = support.match(item, headers=headers).data
    if 'clicca qui per aprire' in data.lower():
        data = support.match(support.match(data, patron=r'"go_to":"([^"]+)"').match.replace('\\',''), headers=headers).data

    elif 'clicca qui</span>' in data.lower():
        data = support.match(support.match(data, patron=r'<h2 style="text-align: center;"><a href="([^"]+)">').match, headers=headers).data

    patronBlock = r'</a></span>(?P<block>[a-zA-Z\s].*?)></div>'
    patron = r'data.num..(?P<season>\d+)x(?P<episode>\d+).*?>(?P<title>.*?)<.*?"(?P<url>.*?)"'

    return locals()


def search(item, texto):
    support.info()

    item.url = host + '/index.php?story=%s&do=search&subaction=search' % (texto)
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
        item.url = "%s/aggiornamento-episodi/" % host
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
    itemlist = support.server(item, item.url)
    return itemlist
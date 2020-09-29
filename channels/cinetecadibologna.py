# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per cinetecadibologna
# ------------------------------------------------------------
from core.item import Item

from core import support

host = support.config.get_channel_url()


headers = [['Referer', host]]
@support.menu
def mainlist(item):
    film = ['/video/alfabetico_completo',
            ('Anni',['/video/epoche', 'menu']),
            ('Registi',['/video/registi', 'menu']),
            ('Attori',['/video/attori', 'menu']),
            ('Percorsi Tematici',['/video/percorsi','menu'])]
    return locals()


@support.scrape
def menu(item):
    action = 'peliculas'
    if 'epoche' in item.url:
        patronMenu =r'<li>\s*<a href="(?P<url>[^"]+)">(?P<title>[^>]+)<'
    elif 'percorsi' in item.url:
        patron = r'<div class="cover_percorso">\s*<a href="(?P<url>[^"]+)">\s*<img src="(?P<thumb>[^"]+)"[^>]+>\s*[^>]+>(?P<title>.*?)<'
    else:
        patron = r'<h2>\s*<a href="(?P<url>[^,"]+),[^"]+"\s*>(?P<title>[^<]+)<'
        patronNext = r'<div class="dx">\s*<a href="(.*?)">pagina suc'
    return locals()


def search(item, text):
    support.info(text)
    item.args = 'noorder'
    item.url = host + '/ricerca/type_ALL/ricerca_' + text
    item.contentType = 'movie'
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
        return []



@support.scrape
def peliculas(item):
    if 'alfabetico' in item.url:
        patron = r'<img src="(?P<thumb>[^"]+)"[^>]+>\s*[^>]+>\s*<div[^>]+>\s*<div[^>]+>[^>]+>\s*<a href="(?P<url>[^"]+)"[^>]+>(?:\[)?(?P<title>[^\]<]+)(?:\]|<)'
    else:
        if 'type_ALL' in item.url: patronBlock = r'Video:(?P<block>.*?)(?:<div class=""|<!--)'
        elif not 'NomePersona' in item.url: patronBlock = r'<h3>Film</h3>(?P<block>.*?)<div class="list_wrapper'
        patron = r'<a href="(?P<url>[^"]+)"\s*class="[^"]+"\s*title="(?:\[)?(?P<title>[^\]"]+)(?:\])?"\s*rel="(?P<thumb>[^"]+)"'
    patronNext = r'<div class="dx">\s*<a href="(.*?)">pagina suc'
    return locals()


def findvideos(item):
    support.info()
    itemlist = []

    matches = support.match(item, patron=r'filename: "(.*?)"').matches

    for url in matches:
        itemlist.append(item.clone(action="play", title=support.config.get_localized_string(30137), server='directo', url=host + url))

    return support.server(item, itemlist=itemlist)


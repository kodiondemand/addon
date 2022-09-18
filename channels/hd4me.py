# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per HD4ME
# ------------------------------------------------------------

from core import support


host = support.config.get_channel_url()
headers = [['Referer', host]]


@support.menu
def mainlist(item):

    film = [('Genere', ['', 'genre'])]

    return locals()


@support.scrape
def peliculas(item):
    # debug = True
    if item.args == 'alternative':
        pagination = ''
        patron = r'<a title="(?P<title>[^\(]+)\(\s*(?P<year>\d+)\)\s\D+(?P<quality>\d+p).{3}(?P<lang>[^ ]+).*?[^"]+"\s*href="(?P<url>[^"]+)'
    else:
        patron = r'<a href="(?P<url>[^"]+)" (?:rel="?[0-9]+"?)? title="(?P<title>[^"]+)(?!\()\s*\((?P<year>\d+)\)\s(?:[^\]]+\])?\D+(?P<quality>\d+p).{3}(?P<lang>[^ ]+).*?<img id="?cov"?.*?src="(?P<thumb>[^"]+)'
        patronNext = r'current(?:[^>]*>){2}\s*<a class="[^"]+"\s* href="([^"]+)'
    return locals()


@support.scrape
def genre(item):
    action = 'peliculas'
    blacklist =['prova ']
    patronMenu = r'<a href="(?P<url>[^"]+)" class="menu-link\s*sub-menu-link">(?P<title>[^<]+)<'
    def itemHook(item):
        if item.fulltitle in ['Classici Disney', 'Studio Ghibli', 'Pixar']:
            item.args = 'alternative'
        return item
    return locals()


def search(item, text):
    support.info(text)
    item.url = host + '/?s=' + text
    try:
        return peliculas(item)
    # Cattura la eccezione così non interrompe la ricerca globle se il canale si rompe!
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("search except: %s" % line)
        return []


def findvideos(item):
    url = support.match(item, patron=r'<a class=["]?bot1["]? href="([^"]+)"').match
    url = support.httptools.downloadpage(url, followredirect=True).url
    return support.server(item, url)

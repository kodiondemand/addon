# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per guardaserieclick
# ------------------------------------------------------------

"""

    Avvisi per il test:
        - Le voci del menu le trovi in "lista serie" del sito, e Generi = Sfoglia
        - SE capita che entrando in una voce trovi "nessun elemento" torna indietro e rientra nella voce.
        - Tutte le voci, tranne: Anime/Cartoni, mostrano per ogni pagina, al max 25 titoli

    Presente in NOVITà:
        - Serietv
"""

from core import support
from core.item import Item
from platformcode import config
from core.support import info

host = config.get_channel_url()
headers = [['Referer', host]]


@support.menu
def mainlist(item):
    tvshow = ['',
              ('Aggiornamenti', ['', 'peliculas', 'update']),
              ('Generi', ['', 'genres', 'genres']),
              ('News Sub-ITA', ['', 'peliculas', 'ined']),
              ('Anime/Cartoni', ["/category/animazione/", 'peliculas', 'genres'])
              ]

    return locals()


##@support.scrape
##def peliculas(item):
####    import web_pdb; web_pdb.set_trace()
##    info('peliculas ->\n', item)
##
##    action = 'episodios'
##    block = r'(?P<block>.*?)<div\s+class="btn btn-lg btn-default btn-load-other-series">'
##
##    if item.args == 'ined':
##        deflang = 'SUB-ITA'
##        patronBlock = r'<span\s+class="label label-default label-title-typology">'+block
##        patron = r'<a href="(?P<url>[^"]+)".*?>\s<img\s.*?src="(?P<thumb>[^"]+)"\s/>[^>]+>[^>]+>\s[^>]+>\s(?P<year>\d{4})?\s.+?class="strongText">(?P<title>.+?)<'
##        pagination = 25
##    elif item.args == 'update':
##        patronBlock = r'<div\s+class="container-fluid greybg title-serie-lastep title-last-ep fixed-title-wrapper containerBottomBarTitle">'+block
##        patron = r'<a(?: rel="[^"]+")? href="(?P<url>[^"]+)"(?: class="[^"]+")?>[ ]<img class="[^"]+"[ ]title="[^"]+"[ ]alt="[^"]+"[ ]src="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<episode>\d+.\d+)[ ]\((?P<lang>[a-zA-Z\-]+)[^<]+<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>[^<]+)<'
##    elif item.args == 'genres':
##        patronBlock = r'<h2 style="color: white !important" class="title-typology">(?P<block>.+?)<div class="container-fluid whitebg" style="">'
##        patron = r'<a href="(?P<url>[^"]+)".*?>\s<img\s.*?src="(?P<thumb>[^"]+)"\s/>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>[^<]+)</p>'
##        patronNext = r'rel="next" href="([^"]+)">'
##        item.contentType = 'tvshow'
##    elif item.args == 'nolost':
##        patronBlock = r'<h2 class="title-typology styck-top" meta-class="title-serie-danonperd">'+block
##        patron = r'<a href="(?P<url>[^"]+)".*?>\s<img\s.*?src="(?P<thumb>[^"]+)"\s/>[^>]+>[^>]+>\s[^>]+>\s(?P<year>\d{4})?\s.+?class="strongText">(?P<title>.+?)<'
##        pagination = 25
##    elif item.args == 'classic':
##        patronBlock = r'<h2 class="title-typology  styck-top" meta-class="title-serie-classiche">'+block
##        patron = r'<a href="(?P<url>[^"]+)".*?>\s<img\s.*?src="(?P<thumb>[^"]+)"\s/>[^>]+>[^>]+>\s[^>]+>\s(?P<year>\d{4})?\s.+?class="strongText">(?P<title>.+?)<'
##        pagination = 25
##    else:
##        patronBlock = r'<div\s+class="container container-title-serie-new container-scheda" meta-slug="new">'+block
##        patron = r'<a href="(?P<url>[^"]+)".*?>\s<img\s.*?src="(?P<thumb>[^"]+)"\s/>[^>]+>[^>]+>\s[^>]+>\s(?P<year>\d{4})?\s.+?class="strongText">(?P<title>.+?)<'
##        pagination = 25
##
##    debug = True
##    return locals()

@support.scrape
def peliculas(item):
    ##    import web_pdb; web_pdb.set_trace()
    info('peliculas ->\n', item)

    action = 'episodios'
    blacklist = ['DMCA']

    if item.args == 'genres' or item.args == 'search':
        patronBlock = r'<h2 style="color:\s?white !important;?" class="title-typology">(?P<block>.+?)<div class="container-fluid whitebg" style="">'
        patron = r'<a href="(?P<url>[^"]+)".*?>\s<img\s.*?src="(?P<thumb>[^"]+)"\s/>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>[^<]+)</p>'
        patronNext = r'rel="next" href="([^"]+)">'
        item.contentType = 'tvshow'
    ##    elif item.args == 'search':
    ##        patronBlock = r'<h2 style="color:\s?white !important.?" class="title-typology">(?P<block>.*?)<div class="container-fluid whitebg" style="">'
    ##        patron = r'<a href="(?P<url>[^"]+)".*?>\s<img\s.*?src="(?P<thumb>[^"]+)"\s/>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>[^<]+)</p>'
    else:
        end_block = r'(?P<block>.*?)<div\s+class="btn btn-lg btn-default btn-load-other-series">'
        patron = r'<a href="(?P<url>[^"]+)".*?>\s<img\s.*?src="(?P<thumb>[^"]+)"\s/>[^>]+>[^>]+>\s[^>]+>\s(?P<year>\d{4})?\s.+?class="strongText">(?P<title>.+?)<'
        pagination = 25
        if item.args == 'ined':
            deflang = 'SUB-ITA'
            patronBlock = r'<span\s+class="label label-default label-title-typology">' + end_block
        ##            patron = r'<a href="(?P<url>[^"]+)".*?>\s<img\s.*?src="(?P<thumb>[^"]+)"\s/>[^>]+>[^>]+>\s[^>]+>\s(?P<year>\d{4})?\s.+?class="strongText">(?P<title>.+?)<'
        ##            pagination = 25
        elif item.args == 'update':
            patronBlock = r'<div\s+class="container-fluid greybg title-serie-lastep title-last-ep fixed-title-wrapper containerBottomBarTitle">' + end_block
            patron = r'href="(?P<url>[^"]+)".*?>\s<img\s.*?src="(?P<thumb>[^"]+)"\s/>[^>]+>[^>]+>\s[^>]+>.+?class="strongText">(?P<title>.+?)<'
        # elif item.args == 'nolost':
        #     patronBlock = r'<h2 class="title-typology styck-top" meta-class="title-serie-danonperd">' + end_block
        #            pagination = 25
        # elif item.args == 'classic':
        #     patronBlock = r'<h2 class="title-typology  styck-top" meta-class="title-serie-classiche">' + end_block
        ##            patron = r'<a href="(?P<url>[^"]+)".*?>\s<img\s.*?src="(?P<thumb>[^"]+)"\s/>[^>]+>[^>]+>\s[^>]+>\s(?P<year>\d{4})?\s.+?class="strongText">(?P<title>.+?)<'
        ##            pagination = 25
        ##        elif item.args == 'anime':
        ##
        else:
            patronBlock = r'<div\s+class="container container-title-serie-new container-scheda" meta-slug="new">' + end_block
    ##            patron = r'<a href="(?P<url>[^"]+)".*?>\s<img\s.*?src="(?P<thumb>[^"]+)"\s/>[^>]+>[^>]+>\s[^>]+>\s(?P<year>\d{4})?\s.+?class="strongText">(?P<title>.+?)<'
    ##            pagination = 25
    # support.regexDbg(item, patronBlock, headers)
    # debug = True
    return locals()


@support.scrape
def episodios(item):
    info()

    action = 'findvideos'
    patron = r'<div class="number-episodes-on-img">\s?\d+.\d+\s?(?:\((?P<lang>[a-zA-Z\-]+)\))?</div>.+?(?:<span class="pull-left bottom-year">(?P<title2>[^<]+)<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<plot>[^<]+)<[^>]+>[^>]+>[^>]+>\s?)?<span(?: meta-nextep="[^"]+")? class="[^"]+" meta-serie="(?P<title>[^"]+)" meta-stag="(?P<season>\d+)" meta-ep="(?P<episode>\d+)" meta-embed="(?P<url>[^>]+)">'
    patronBlock = r'<h2 class="title-typology">Episodi (?P<stagione>\d+).{1,3}Stagione</h2>(?P<block>.*?)<div class="container">'

    def itemHook(item):
        item.title = item.title.replace(item.fulltitle, '').replace('-', '', 1)
        return item

    # debug = True
    return locals()


@support.scrape
def genres(item):
    info()

    action = 'peliculas'
    patronMenu = r'<li>\s<a\shref="(?P<url>[^"]+)"[^>]+>(?P<title>[^<]+)</a></li>'
    patron_block = r'<ul\sclass="dropdown-menu category">(?P<block>.*?)</ul>'
    # debug = True
    return locals()


def search(item, text):
    info(text)
    item.url = host + "/?s=" + text
    item.contentType = 'tvshow'
    item.args = 'search'
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            info("%s" % line)
        return []


def newest(categoria):
    info()
    itemlist = []
    item = Item()
    item.contentType = 'tvshow'
    item.args = 'update'
    try:
        if categoria == "series":
            item.url = host
            item.action = "peliculas"
            itemlist = peliculas(item)

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            info("{0}".format(line))
        return []

    return itemlist


def findvideos(item):
    info('--->', item)
    return support.server(item, item.url)

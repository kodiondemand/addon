# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per 'casacinemaInfo'
# ------------------------------------------------------------
"""

    Problemi noti che non superano il test del canale:
       -

    Avvisi:
        - Sub-ita non è nel titolo, lascia il puntatore sulla locandina
        per visualizzare il titolo completo!

    Novità:
        - Film
    Ulteriori info:


"""

from core import support
from core.item import Item


# def findhost():
#     data = httptools.downloadpage('https://casacinema.nuovo.link').data
#     host = scrapertools.find_single_match(data, r'<div class="elementor-widget-container"><div class="elementor-button-wrapper"> <a href="([^"]+)"')
#     if host.endswith('/'):
#         host = host[:-1]
#     return host

host = support.config.get_channel_url()
headers = [['Referer', host]]

list_servers = ['supervideo', 'streamcherry','rapidvideo', 'streamango', 'openload']
list_quality = ['default', 'HD', '3D', '4K', 'DVD', 'SD']

@support.menu
def mainlist(item):
    support.log(item)

    film = ['',
        ('Al Cinema', ['/category/in-sala/', 'peliculas', '']),
        ('Novità', ['/category/nuove-uscite/', 'peliculas', '']),
        ('Generi', ['', 'genres', 'genres']),
        ('Sub-ITA', ['/category/sub-ita/', 'peliculas', ''])
        ]

    return locals()


@support.scrape
def peliculas(item):
    support.log(item)
    #support.dbg() # decommentare per attivare web_pdb
    #findhost()
    
    blacklist = ['']
    if item.args != 'search':
        patron = r'<div class="col-mt-5 postsh">[^<>]+<div class="poster-media-card">[^<>]+<a href="(?P<url>[^"]+)" title="(?P<title>.+?)[ ]?(?:\[(?P<lang>Sub-ITA)\])?".*?<img(?:.+?)?src="(?P<thumb>[^"]+)"'
        patronBlock = r'<div class="showpost4 posthome">(?P<block>.*?)</section>'
    else:
        patron = r'<li class="col-md-12 itemlist">.*?<a href="(?P<url>[^"]+)" title="(?P<title>[^"]+)".*?<img src="(?P<thumb>[^"]+)".*?Film dell"anno: (?P<year>\d{4})(?:[\d\-]+)?</p> <p class="text-list">(?P<plot>[^<>]+)</p>'
        patronBlock = r'<ul class="search-results-content infinite">(?P<block>.*?)</section>'

    patronNext = '<a href="([^"]+)"\s+?><i class="glyphicon glyphicon-chevron-right"'

    #support.regexDbg(item, patronBlock, headers)
    # debug = True
    return locals()


@support.scrape
def genres(item):
    support.log(item)
    #support.dbg()

    action = 'peliculas'
    blacklist = ['']
    patron = r'href="(?P<url>[^"]+)">(?P<title>[^<]+)<'
    patronBlock = r'</span>Generi</h3>(?P<block>.*?)<div class="clear"></div>'

##    debug = True
    return locals()


def search(item, text):
    support.log('search', item)

    itemlist = []
    text = text.replace(' ', '+')
    item.args = 'search'
    item.url = host+'/?s=%s' % (text)
    try:
        return peliculas(item)
    # Se captura la excepcion, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            support.log('search log:', line)
        return []

def newest(categoria):
    support.log('newest ->', categoria)

    itemlist = []
    item = Item()
    
    try:
        if categoria == 'peliculas':
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
    return support.hdpass_get_servers(item)

def play(item):
    return support.hdpass_get_url(item)
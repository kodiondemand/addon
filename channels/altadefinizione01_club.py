# -*- coding: utf-8 -*-
# -*- Channel Altadefinizione01C Film -*-
# -*- Riscritto per KOD -*-
# -*- By Greko -*-
# -*- last change: 04/05/2019
# -*- doppione di altadefinizione01

from specials import autoplay
from core import servertools, support
from core.item import Item
from platformcode import config, logger

__channel__ = "altadefinizione01_club"
host = config.get_channel_url(__channel__)

headers = [['User-Agent', 'Mozilla/50.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'],
           ['Referer', host]]

list_servers = ['verystream','openload','rapidvideo','streamango']
list_quality = ['default']

@support.menu
def mainlist(item):

    film = ''

    filmSub = [
        ('Al Cinema', ['/cinema/', 'peliculas', 'pellicola']),
        ('Generi', ['', 'categorie', 'genres']),
        ('Lettera', ['/catalog/a/', 'categorie', 'orderalf']),
        ('Anni', ['', 'categorie', 'years']),
        ('Sub-ITA', ['/sub-ita/', 'peliculas', 'pellicola'])
    ]

    return locals()

# ======== def in ordine di menu ===========================
# =========== def per vedere la lista dei film =============
@support.scrape
def peliculas(item):
##    import web_pdb; web_pdb.set_trace()
    support.log('peliculas',item)

    action="findvideos"
    if item.args == "search":
        patronBlock = r'</script> <div class="boxgrid caption">(.*?)<div id="right_bar">'
    else:
        patronBlock = r'<div class="cover_kapsul ml-mask">(.*?)<div class="page_nav">'
    patron = r'<div class="cover boxcaption"> <h2>.<a href="(?P<url>[^"]+)">.*?<.*?src="(?P<thumb>[^"]+)"'\
         '.+?[^>]+>[^>]+<div class="trdublaj"> (?P<quality>[A-Z]+)<[^>]+>(?:.[^>]+>(?P<lang>.*?)<[^>]+>).*?'\
         '<p class="h4">(?P<title>.*?)</p>[^>]+> [^>]+> [^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+> [^>]+> '\
         '[^>]+>[^>]+>(?P<year>\d{4})[^>]+>[^>]+> [^>]+>[^>]+>(?P<duration>\d+).+?>'

    patronNext =  '<span>\d</span> <a href="([^"]+)">'

    return locals()

# =========== def pagina categorie ======================================

@support.scrape
def categorie(item):
    support.log('categorie',item)
##    import web_pdb; web_pdb.set_trace()

    if item.args != 'orderalf': action = "peliculas"
    else: action = 'orderalf'
    blacklist = 'Altadefinizione01'

    if item.args == 'genres':
        patronBlock = r'<ul class="kategori_list">(.*?)</ul>'
        patron = '<li><a href="(?P<url>[^"]+)">(?P<title>.*?)</a>'
    elif item.args == 'years':
        patronBlock = r'<ul class="anno_list">(.*?)</ul>'
        patron = '<li><a href="(?P<url>[^"]+)">(?P<title>.*?)</a>'
    elif item.args == 'orderalf':
        patronBlock = r'<div class="movies-letter">(.*)<div class="clearfix">'
        patron = '<a title=.*?href="(?P<url>[^"]+)"><span>(?P<title>.*?)</span>'

    return locals()
# =========== def pagina lista alfabetica ===============================
@support.scrape
def orderalf(item):
    support.log('orderalf',item)

    action= 'findvideos'
    patron = r'<td class="mlnh-thumb"><a href="(?P<url>[^"]+)".*?src="(?P<thumb>[^"]+)"'\
             '.+?[^>]+>[^>]+ [^>]+[^>]+ [^>]+>(?P<title>[^<]+).*?[^>]+>(?P<year>\d{4})<'\
             '[^>]+>[^>]+>(?P<quality>[A-Z]+)[^>]+> <td class="mlnh-5">(?P<lang>.*?)</td>'
    patronNext =  r'<span>[^<]+</span>[^<]+<a href="(.*?)">'

    return locals()
# =========== def pagina del film con i server per verderlo =============

def findvideos(item):
    support.log('findvideos', item)
    return support.server(item, headers=headers)

# =========== def per cercare film/serietv =============
#http://altadefinizione01.link/index.php?do=search&story=avatar&subaction=search
def search(item, text):
    logger.info("%s mainlist search log: %s %s" % (__channel__, item, text))
    itemlist = []
    text = text.replace(" ", "+")
    item.url = host + "/index.php?do=search&story=%s&subaction=search" % (text)
    item.args = "search"
    try:
        return peliculas(item)
    # Cattura la eccezione così non interrompe la ricerca globle se il canale si rompe!
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s Sono qua: %s" % (__channel__, line))
        return []

# =========== def per le novità nel menu principale =============

def newest(categoria):
    support.log(categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "peliculas":
            item.url = host
            item.action = "peliculas"
            itemlist = peliculas(item)

            if itemlist[-1].action == "peliculas":
                itemlist.pop()
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist

# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per altadefinizione01
# ------------------------------------------------------------
"""
    
    Eccezioni note che non superano il test del canale:

    Avvisi:
        - L'url si prende da questo file.
        - è presente nelle novità-> Film.

    Ulteriori info:

"""
from core import scrapertools, httptools, support
from core.item import Item
from platformcode import config, logger

#impostati dinamicamente da findhost()

def findhost():
    data = httptools.downloadpage('https://altadefinizione01-nuovo.link/').data
    host = scrapertools.find_single_match(data, '<div class="elementor-button-wrapper"> <a href="([^"]+)"')
    return host


host = config.get_channel_url(findhost)
headers = [['Referer', host]]




@support.menu
def mainlist(item):

    film = [
        ('Al Cinema', ['/cinema/', 'peliculas', 'pellicola']),
        ('Ultimi Aggiornati-Aggiunti', ['','peliculas', 'update']),
        ('Generi', ['', 'genres', 'genres']),
        ('Lettera', ['/catalog/a/', 'genres', 'orderalf']),
        ('Anni', ['', 'genres', 'years']),
        ('Sub-ITA', ['/sub-ita/', 'peliculas', 'pellicola'])
    ]

    return locals()

@support.scrape
def peliculas(item):
    support.log('peliculas',item)

##    deflang = 'ITA'
    action="findvideos"

    patron = r'<div class="cover boxcaption"> <h2>.<a href="(?P<url>[^"]+)">.*?<.*?src="(?P<thumb>[^"]+)"'\
         '.+?[^>]+>[^>]+<div class="trdublaj"> (?P<quality>[A-Z/]+)<[^>]+>(?:.[^>]+>(?P<lang>.*?)<[^>]+>).*?'\
         '<p class="h4">(?P<title>.*?)</p>[^>]+> [^>]+> [^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+> [^>]+> '\
         '[^>]+>[^>]+>(?P<year>\d{4})[^>]+>[^>]+> [^>]+>[^>]+>(?P<duration>\d+).+?>.*?<p>(?P<plot>[^<]+)<'

    if item.args == "search":
        patronBlock = r'</script> <div class="boxgrid caption">(?P<block>.*)<div id="right_bar">'
        
    elif item.args == 'update':
        patronBlock = r'<div class="widget-title">Ultimi Film Aggiunti/Aggiornati</div>(?P<block>.*?)<div id="alt_menu">'
        patron = r'style="background-image:url\((?P<thumb>[^\)]+).+?<p class="h4">(?P<title>.*?)</p>[^>]+> [^>]+> [^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+> [^>]+> [^>]+>[^>]+>(?P<year>\d{4})[^>]+>[^>]+> [^>]+>[^>]+>(?P<duration>\d+).+?>.*?(?:>Film (?P<lang>Sub ITA)</a></p> )?<p>(?P<plot>[^<]+)<.*?href="(?P<url>[^"]+)'
    else:
        patronBlock = r'<div class="cover_kapsul ml-mask">(?P<block>.*)<div class="page_nav">'

    patronNext =  '<span>\d</span> <a href="([^"]+)">'
##    debug = True
    return locals()

@support.scrape
def genres(item):
    support.log('genres',item)
    
    if item.args != 'orderalf': action = "peliculas"
    else: action = 'orderalf'

    blacklist = ['Altadefinizione01']
    if item.args == 'genres':
        patronBlock = r'<ul class="kategori_list">(?P<block>.*?)<div class="tab-pane fade" id="wtab2">'
        patronMenu = '<li><a href="(?P<url>[^"]+)">(?P<title>.*?)</a>'
    elif item.args == 'years':
        patronBlock = r'<ul class="anno_list">(?P<block>.*?)</a></li> </ul> </div>'
        patronMenu = '<li><a href="(?P<url>[^"]+)">(?P<title>.*?)</a>'
    elif item.args == 'orderalf':
        patronBlock = r'<div class="movies-letter">(?P<block>.*?)<div class="clearfix">'
        patronMenu = '<a title=.*?href="(?P<url>[^"]+)"><span>(?P<title>.*?)</span>'

    #debug = True
    return locals()

@support.scrape
def orderalf(item):
    support.log('orderalf',item)
    
    action= 'findvideos'
    patron = r'<td class="mlnh-thumb"><a href="(?P<url>[^"]+)".*?src="(?P<thumb>[^"]+)"'\
             '.+?[^>]+>[^>]+ [^>]+[^>]+ [^>]+>(?P<title>[^<]+).*?[^>]+>(?P<year>\d{4})<'\
             '[^>]+>[^>]+>(?P<quality>[A-Z]+)[^>]+> <td class="mlnh-5">(?P<lang>.*?)</td>'
    patronNext =  r'<span>[^<]+</span>[^<]+<a href="(.*?)">'

    return locals()


def search(item, text):
    support.log(item, text)

    
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
            logger.error("search except: %s" % line)
        return []

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

def findvideos(item):
    support.log('findvideos', item)
    return support.server(item, headers=headers)

# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per altadefinizioneclick
# ----------------------------------------------------------
"""

    Eccezioni che non superano il test del canale:
       - indicare le eccezioni

    Novità. Indicare in quale/i sezione/i è presente il canale:
       - film
    
    Avvisi:
        - Eventuali avvisi per i tester

    Ulteriori info:


"""
from core import support
from core.item import Item
from platformcode import config

def findhost():
    data = support.httptools.downloadpage('https://altadefinizione-nuovo.me/').data
    host = support.scrapertools.find_single_match(data, '<div class="elementor-button-wrapper"> <a href="([^"]+)"')
    return host

host = config.get_channel_url(findhost)
headers = [['Referer', host]]


@support.menu
def mainlist(item):
    film = ['',
        ('Novità', ['/nuove-uscite/', 'peliculas', 'news']),
        ('Al Cinema', ['/al-cinema/', 'peliculas', 'cinema']),
        ('A-Z',['/lista-film/', 'genres', 'az']),
        ('Generi', ['', 'genres', 'genres']),
        ('Anni', ['', 'genres', 'years']),
        ('Qualità', ['', 'genres', 'quality']),
        ('Mi sento Fortunato',[ '', 'genres', 'lucky']),
        ('Sub-ITA', ['/sub-ita/', 'peliculas', 'sub'])
    ]
    return locals()

@support.scrape
def peliculas(item):
    patron = r'<div class="wrapperImage">[ ]?(?:<span class="hd">(?P<quality>[^<>]+))?.+?href="(?P<url>[^"]+)".+?src="(?P<thumb>[^"]+)".+?<h2 class="titleFilm">[^>]+>'\
             r'(?P<title>.+?)[ ]?(?:|\[(?P<lang>[^\]]+)\])?(?:\((?P<year>\d{4})\))?</a>.*?(?:IMDB\:</strong>[ ](?P<rating>.+?)<|</h2> )'
    patronBlock = r'h1>(?P<block>.*?)<div class="row ismobile">'

    if item.args == 'az':
        patron = r'<img style="[^"]+" src="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>[^>]+><a href="(?P<url>[^"]+)" [^>]+>(?P<title>[^<\[]+)(?:\[(?P<lang>[^\]]+)\]\s*)?<'\
                 r'[^>]+>[^>]+>[^>]+>[^>]+>\s*(?P<year>\d{4})[^>]+>[^>]+>\s*(?P<quality>[^<]+).*?<span class="label">(?P<ratting>[^<]+)<'
        patronBlock =''

    elif item.args == 'genres':
        patron = r'<div class="wrapperImage">[ ]?(?:<span class="hd">(?P<quality>[^<>]+))?.+?href="(?P<url>[^"]+)".+?src="(?P<thumb>[^"]+)"'\
                 r'.+?<h2 class="titleFilm(?:Mobile)?">[^>]+>(?P<title>.+?)[ ]?(?:|\[(?P<lang>[^\]]+)\])?(?:\((?P<year>\d{4})\))?</a>.*?(IMDB\:[ ](?P<rating>.+?))<'
    elif item.args == 'search':
        patronBlock = r'<section id="lastUpdate">(?P<block>.*?)<div class="row ismobile">'
        patron = r'<a href="(?P<url>[^"]+)">\s*<div class="wrapperImage">(?:<span class="hd">(?P<quality>[^<]+)<\/span>)?<img[^s]+src="(?P<thumb>[^"]+)"'\
                 r'[^>]+>[^>]+>[^>]+>(?P<title>[^<]+)<[^<]+>(?:.*?IMDB:\s(\2[^<]+)<\/div>)?'

    if not item.args:
        patronBlock = r'ULTIMI INSERITI(?P<block>.*?)<div class="sliderLastUpdate ismobile ">'

    # nella pagina "CERCA", la voce "SUCCESSIVO" apre la maschera di inserimento dati
    patronNext = r'<a class="next page-numbers" href="([^"]+)">'

    return locals()

@support.scrape
def genres(item):
    action = 'peliculas'
    patronMenu = r'<li><a href="(?P<url>[^"]+)">(?P<title>[^<]+)<'

    if item.args == 'genres':
        patronBlock = r'<ul class="listSubCat" id="Film">(?P<block>.*)<ul class="listSubCat" id="Anno">'
    elif item.args == 'years':
        patronBlock = r'<ul class="listSubCat" id="Anno">(?P<block>.*)<ul class="listSubCat" id="Qualita">'
    elif item.args == 'quality':
        patronBlock = r'<ul class="listSubCat" id="Qualita">(?P<block>.*)</li> </ul> </div> </div> </div> <a'
    elif item.args == 'lucky': # sono i titoli random nella pagina
        patronBlock = r'<h3 class="titleSidebox dado">FILM RANDOM</h3>(?P<block>.*)</section>'
        patron = r'<li><a href="(?P<url>[^"]+)">(?P<title>[^<[]+)(?:\[(?P<lang>.+?)\])?<'
        action = 'findvideos'
    elif item.args == 'az':
        blacklist = ['FILM 4K IN STREAMING']
        patron = r'<a title="(?P<title>[^"]+)" href="(?P<url>[^"]+)"'
        item.args = 'az'
    if not item.args == 'az':
        item.args = 'genres'

    return locals()

def search(item, texto):
    support.log("search ", texto)

    item.args = 'search'
    item.url = host + "/?s=" + texto
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
        return []

def newest(categoria):
    support.log(categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "peliculas":
            item.args = 'news'
            item.contentType = 'movie'
            item.url = host + "/nuove-uscite/"
            item.action = "peliculas"
            itemlist = peliculas(item)

            if itemlist[-1].action == "peliculas":
                itemlist.pop()

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            from platformcode import logger
            logger.error("{0}".format(line))
        return []

    return itemlist

def findvideos(item):
    support.log('findvideos', item)
    return support.hdpass_get_servers(item)

def play(item):
    if 'hdpass' in item.url:
        return support.hdpass_get_url(item)
    return [item]

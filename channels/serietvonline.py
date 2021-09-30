# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per serietvonline.py
# ----------------------------------------------------------
"""
    Novità. Indicare in quale/i sezione/i è presente il canale:
       - film, serie

    Avvisi:
        - Al massimo 25 titoli per le sezioni: Film
        - Al massimo 35 titoli per le sezioni: Tutte le altre
        Per aggiungere in videoteca le Anime:
            Se hanno la forma 1x01:
                -si posso aggiungere direttamente dalla pagina della serie, sulla voce in fondo "aggiungi in videoteca".
            Altrimenti:
                - Prima fare la 'Rinumerazione' dal menu contestuale dal titolo della serie
"""

from core import support,  scrapertools
from platformcode import config, logger
from core.item import Item


# def findhost(url):
#     host = support.match(url, patron=r'href="([^"]+)">\s*cliccando qui').matches[-1]
#     return host

host = config.get_channel_url()
headers = [['Referer', host]]


@support.menu
def mainlist(item):
    logger.debug()


    film = ['/ultimi-film-aggiunti/',
            ('A-Z', ['/lista-film/', 'movies', 'lista'])
        ]

    tvshow = ['',
            ('Aggiornamenti', ['/ultimi-episodi-aggiunti/', 'movies', 'update']),
            ('Tutte', ['/lista-serie-tv/', 'movies', 'qualcosa']),
            ('Italiane', ['/lista-serie-tv-italiane/', 'movies', 'qualcosa']),
            ('Anni 50-60-70-80', ['/lista-serie-tv-anni-60-70-80/', 'movies', 'qualcosa']),
            ('HD', ['/lista-serie-tv-in-altadefinizione/', 'movies', 'qualcosa'])
        ]

    anime = ['/lista-cartoni-animati-e-anime/']

    documentari = [('Documentari {bullet bold}', ['/lista-documentari/' , 'movies' , 'doc', 'tvshow'])]

    search = ''

    return locals()

@support.scrape
def movies(item):
    logger.debug()
    numerationEnabled = True

    blacklist = ['DMCA', 'Contatti', 'Attenzione NON FARTI OSCURARE', 'Lista Cartoni Animati e Anime']
    patronBlock = r'<h1>.+?</h1>(?P<block>.*?)<div class="footer_c">'
    patronNext = r'<div class="siguiente"><a href="([^"]+)" >'
    # debug = True

    if item.args == 'search':
        patronBlock = r'>Lista Serie Tv</a></li></ul></div><div id="box_movies">(?P<block>.*?)<div id="paginador">'
        patron = r'<div class="movie">[^>]+[^>]+>\s*<img src="(?P<thumb>[^"]+)" alt="(?P<title>.+?)(?:(?P<year>\d{4})|")[^>]*>\s*<a href="(?P<url>[^"]+)'
    elif item.contentType == 'episode':
        pagination = True
        action = 'findvideos'
        patron = r'<td><a href="(?P<url>[^"]+)"(?:[^>]+)?>\s?(?P<title>.*?)(?P<episode>\d+x\d+)[ ]?(?P<title2>[^<]+)?<'

    elif item.contentType == 'tvshow':
        # SEZIONE Serie TV- Anime - Documentari
        pagination = True

        if not item.args and 'anime' not in item.url:
            patron = r'<div class="movie">[^>]+>.+?src="(?P<thumb>[^"]+)" alt="[^"]+".+? href="(?P<url>[^"]+)">.*?<h2>(?P<title>[^"]+)</h2>\s?(?:<span class="year">(?P<year>\d+|\-\d+))?<'
        else:
            numerationEnabled = True
            patron = r'(?:<td>)?<a href="(?P<url>[^"]+)"(?:[^>]+)?>\s?(?P<title>[^<]+)(?P<episode>[\d\-x]+)?(?P<title2>[^<]+)?<'
    else:
        # SEZIONE FILM
        pagination = True

        if item.args == 'lista':
            patron = r'href="(?P<url>[^"]+)"[^>]+>(?P<title>.+?)(?:\s(?P<year>\d{4})|<)'
            patronBlock = r'Lista dei film disponibili in streaming e anche in download\.</p>(?P<block>.*?)<div class="footer_c">'
        else:
            patron = r'<tr><td><a href="(?P<url>[^"]+)"(?:|.+?)?>(?:&nbsp;&nbsp;)?[ ]?(?P<title>.*?)[ ]?(?P<quality>HD)?[ ]?(?P<year>\d+)?(?: | HD[^<]*| Streaming[^<]*| MD(?: iSTANCE)? [^<]*)?</a>'

    def itemHook(item):
        if 'film' in item.url:
            item.action = 'findvideos'
            item.contentType = 'movie'
        elif item.args == 'update':
            pass
        else:
            item.contentType = 'tvshow'
            item.action = 'episodes'
        return item
    return locals()


@support.scrape
def episodes(item):
    logger.debug()
    numerationEnabled = True
    action = 'findvideos'
    patronBlock = r'<table>(?P<block>.*)<\/table>'
    patron = r'<tr><td>(?P<title>.*?)?[ ](?:Parte)?(?P<episode>\d+x\d+|\d+)(?:|[ ]?(?P<title2>.+?)?(?:avi)?)<(?P<data>.*?)<\/td><tr>'
    def itemlistHook(itemlist):
        for i, item in enumerate(itemlist):
            ep = support.match(item.title, patron=r'\d+x(\d+)').match
            if ep == '00':
                item.title = item.title.replace('x00', 'x' + str(i+1).zfill(2)).replace('- ..','')
        return itemlist
    return locals()


def search(item, text):
    logger.debug("CERCA :" ,text, item)

    item.url = "%s/?s=%s" % (host, text)

    try:
        item.args = 'search'
        return movies(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

def newest(category):
    logger.debug(category)

    itemlist = []
    item = Item()

    if category == 'movie':
        item.contentType = 'movie'
        item.url = host + '/ultimi-film-aggiunti/'
    elif category == 'tvshow':
        item.args = 'update'
        item.contentType = 'episode'
        item.url = host +'/ultimi-episodi-aggiunti/'
    try:
        item.action = 'movies'
        itemlist = movies(item)

    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist

def findvideos(item):
    logger.debug()
    if item.contentType == 'movie':
        return support.server(item, headers=headers)
    else:

        if item.args != 'update':
            return support.server(item, item.data)
        else:
            itemlist = []
            item.infoLabels['mediatype'] = 'episode'

            data = support.match(item.url, headers=headers).data
            url_video = scrapertools.find_single_match(data, r'<tr><td>(.+?)</td><tr>', -1)
            url_serie = scrapertools.find_single_match(data, r'<link rel="canonical" href="([^"]+)"\s?/>')
            goseries = support.typo("Vai alla Serie:", ' bold')
            series = support.typo(item.contentSerieName, ' bold color kod')
            itemlist = support.server(item, data=url_video)

            itemlist.append(item.clone(title=goseries + series, contentType='tvshow', url=url_serie, action='episodes', plot = goseries + series + "con tutte le puntate", args=''))

        return itemlist

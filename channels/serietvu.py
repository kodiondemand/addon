# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per serietvu.py
# ----------------------------------------------------------

"""
    La pagina novità contiene al max 25 titoli
"""
import re

from core import support
from core.item import Item
from platformcode import config, logger

host = config.get_channel_url()
headers = [['Referer', host]]





@support.menu
def mainlist(item):

    tvshow = ['/category/serie-tv',
              ('Ultimi episodi', ['/ultimi-episodi/', 'movies', 'update']),
              ('Generi', ['', 'genres', 'genres'])
    ]

    return locals()


@support.scrape
def movies(item):
    # debug=True
    patronBlock = r'<div class="wrap">\s*<h.>.*?</h.>(?P<block>.*?)<footer>'

    if item.args != 'update':
        action = 'episodes'
        patron = r'<div class="item">\s*?<a href="(?P<url>[^"]+)" data-original="(?P<thumb>[^"]+)" class="lazy inner">(?:[^>]+>){4}(?P<title>[^<]+)<'
    else:
        action = 'findvideos'
        patron = r'<div class="item">\s*?<a href="(?P<url>[^"]+)"\s*?data-original="(?P<thumb>[^"]+)"(?:[^>]+>){5}(?P<title>.+?)<[^>]+>\((?P<episode>[\dx\-]+)\s+?(?P<lang>Sub-Ita|[iITtAa]+)\)<'
        pagination = True

    patronNext = r'<li><a href="([^"]+)"\s+?>Pagina successiva'
    return locals()


@support.scrape
def episodes(item):
    seasons = support.match(item, patron=r'<option value="(\d+)"[^>]*>\D+(\d+)').matches
    patronBlock = r'</select><div style="clear:both"></div></h2>(?P<block>.*?)<div id="trailer" class="tab">'
    patron = r'(?:<div class="list (?:active)?")?\s*<a data-id="\d+(?:[ ](?P<lang>[SuUbBiItTaA\-]+))?"(?P<other>[^>]+)>.*?Episodio [0-9]+\s?(?:<br>(?P<title>[^<]+))?.*?Stagione (?P<season>[0-9]+) , Episodio - (?P<episode>[0-9]+).*?<(?P<url>.*?<iframe)'
    def itemHook(i):
        for value, season in seasons:
            logger.debug(value)
            logger.debug(season)
            i.title = i.title.replace(value+'x',season+'x')
        i.other += '\n' + i.url
        i.url = item.url
        return i
    return locals()


@support.scrape
def genres(item):
    blacklist = ["Home Page", "Calendario Aggiornamenti"]
    action = 'movies'
    patronBlock = r'<h2>Sfoglia</h2>\s*<ul>(?P<block>.*?)</ul>\s*</section>'
    patronMenu = r'<li><a href="(?P<url>[^"]+)">(?P<title>[^<]+)</a></li>'
    return locals()


def search(item, text):
    logger.debug(text)
    item.url = host + "/?s=" + text
    try:
        item.contentType = 'tvshow'
        return movies(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.debug("%s" % line)
        return []


def newest(category):
    logger.debug(category)
    itemlist = []
    item = Item()
    try:
        if category == 'tvshow':
            item.url = host + "/ultimi-episodi"
            item.action = "movies"
            item.contentType = 'tvshow'
            item.args = 'update'
            itemlist = movies(item)

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def findvideos(item):
    logger.debug(item)
    if item.args != 'update':
        return support.server(item, data=item.other)
    else:
        itemlist = []
        item.infoLabels['mediatype'] = 'episode'

        data = support.match(item).data
        urls_video = support.match(data, patron=r'<a data-id="[^"]+" data-(href=".*?)</iframe>').matches[-1]
        url_serie = support.match(data, patron=r'<link rel="canonical" href="([^"]+)"\s?/>').match

        itemlist = support.server(item, data=urls_video)

        itemlist.append(
            item.clone(title=support.typo("Vai alla Serie Completa: " + item.fulltitle, ' bold'),
                        contentType='tvshow',
                        url=url_serie,
                        action='episodes',
                        thumbnail = support.thumb('tvshow')))

        return itemlist

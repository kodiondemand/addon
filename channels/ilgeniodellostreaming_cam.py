# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per ilgeniodellostreaming_cam
# ------------------------------------------------------------


from core import support
from core.item import Item
from platformcode import config, logger

host = config.get_channel_url()
headers = [['Referer', host]]

@support.menu
def mainlist(item):
    film = ['/film/',
           ('In Sala', ['', 'movies', 'sala']),
           ('Generi',['', 'genres', 'genres']),
           ('Per Lettera',['/catalog/all', 'genres', 'az']),
           ('Anni',['', 'genres', 'year'])]

    return locals()


@support.scrape
def movies(item):
    if item.args == 'sala':
        patronBlock = r'insala(?P<block>.*?)<header>'
        patron = r'<img src="(?P<thumb>[^"]+)[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s*(?P<rating>[^<]+)[^>]+>[^>]+>(?P<quality>[^<]+)[^>]+>[^>]+>[^>]+>[^>]+><a href="(?P<url>[^"]+)">(?P<title>[^<]+)[^>]+>[^>]+>[^>]+>(?P<year>\d{4})'
    elif item.args == 'az':
        patron = r'<img src="(?P<thumb>[^"]+)[^>]+>[^>]+>[^>]+>[^>]+><a href="(?P<url>[^"]+)[^>]+>(?P<title>[^<]+)<[^>]+>[^>]+>[^>]+>.*?<span class="labelimdb">(?P<rating>[^>]+)<'
    else:
        patron = r'<img src="(?P<thumb>[^"]+)[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s*(?P<rating>[^<]+)[^>]+>[^>]+>(?P<quality>[^<]+)[^>]+>[^>]+>[^>]+>[^>]+><a href="(?P<url>[^"]+)">(?P<title>[^<]+)[^>]+>[^>]+>[^>]+>(?P<year>\d{4})[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s*(?P<plot>[^<]+)<[^>]+>'

    patronNext = 'href="([^>]+)">»'

    return locals()


@support.scrape
def genres(item):
    action='movies'
    if item.args == 'genres':
        patronBlock = r'<div class="sidemenu">\s*<h2>Genere</h2>(?P<block>.*?)</ul'
    elif item.args == 'year':
        patronBlock = r'<div class="sidemenu">\s*<h2>Anno di uscita</h2>(?P<block>.*?)</ul'
    elif item.args == 'az':
        patronBlock = r'<div class="movies-letter">(?P<block>.*?)<div class="clearfix">'

    patronMenu = r'<a(?:.+?)?href="(?P<url>.*?)"[ ]?>(?P<title>.*?)<\/a>'
    if 'genres' in item.args:
        patronGenreMenu = patronMenu
    return locals()

def search(item, text):
    logger.debug(text)
    text = text.replace(' ', '+')
    item.url = host + "/search/" + text
    try:
        return movies(item)
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
        item.url = host + '/film/'
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
    urls = []
    data = support.match(item).data
    urls += support.match(data, patron=r'id="urlEmbed" value="([^"]+)').matches
    matches = support.match(data, patron=r'<iframe.*?src="([^"]+)').matches
    for m in matches:
        if 'youtube' not in m and not m.endswith('.js'):
            urls += support.match(m, patron=r'data-link="([^"]+)').matches
    return support.server(item, urls)
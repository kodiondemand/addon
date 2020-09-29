# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per 'Guarda_Serie'
# By: Napster32
# ------------------------------------------------------------
# Rev: 0.0
# Update 11-06-2020
# fix:
# 1. Emissione

# possibilità di miglioramento: gestire le novità (sezione Ultimi episodi sul sito)

from core.support import info
from core import support
from platformcode import config

host = config.get_channel_url()
headers = [['Referer', host]]




@support.menu
def mainlist(item):
    tvshow = ['/serie']
    return locals()

@support.scrape
def peliculas(item):
    patronBlock = r'movies-list movies-list-full(?P<block>.*?)footer>'
    patron = r'<div data-movie-id.*?a href="(?P<url>[^"]+).*?<img data-original="(?P<thumbnail>[^"]+).*?qtip-title">(?P<title>[^<]+).*?(?:rel="tag">(?P<year>[0-9]{4}))?</a>'
    patronNext = '<li class=.active.>.*?href=.(.*?).>'
    action = 'episodios'
    return locals()

@support.scrape
def episodios(item):
    patronBlock = r'<strong>Stagione (?P<season>[0-9]+)(?P<block>.*?)</div></div>'
    patron = r'<a href="(?P<url>[^"]+)">\s*Episodio\s*(?P<episode>[0-9]+)'
    return locals()

def search(item, text):
    info(text)
    itemlist = []
    text = text.replace(' ', '+')
    item.url = host + "/?s=" + text
    try:
        item.args = 'search'
        return peliculas(item)
    except:
        import sys
        for line in sys.exc_info():
            info("%s" % line)

    return []

def findvideos(item):
    support.info('findvideos', item)
    return support.server(item, headers=headers)
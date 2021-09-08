# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per 'guardaserie_live'
# By: Napster32
# ------------------------------------------------------------
# Rev: 0.0
# Update 11-06-2020
# fix:
# 1. Emissione

# possibilità di miglioramento: inserire menu per genere - lista serie tv e gestire le novità

from core import support
from platformcode import logger, config

host = config.get_channel_url()
headers = [['Referer', host]]


@support.menu
def mainlist(item):
    tvshow = ['/serietv-streaming',
              ('Per Lettera', ['/serietv-streaming/A', 'list', 'Serie-Tv per Lettera'])
              ]
    return locals()


@support.scrape
def list(item):
    patronMenu = r'<a title="(?P<title>[^"]+)" href="(?P<url>[^"]+)'
    action = 'peliculas'
    return locals()


@support.scrape
def peliculas(item):
    patron = r'<div class="mlnh-thumb"><a href="(?P<url>[^"]+).*?title="(?P<title>[^"]+).*?src="(?P<thumb>[^"]+).*?hdn">(?P<year>[0-9]{4})'
    patronNext = 'pagenavi.*?<span>.</span>.*?<a href="([^"]+)'
    action = 'episodios'
    return locals()


@support.scrape
def episodios(item):
    patronBlock = r'<div class="tab-pane fade" id="season-(?P<season>.)"(?P<block>.*?)</div>'
    patron = r'<a href="#" allowfullscreen data-link="(?P<url>[^"]+).*?title="(?P<title>[^"]+)(?P<lang>[sS][uU][bB]-?[iI][tT][aA])?\s*">(?P<episode>[^<]+)'
    action = 'findvideos'
    # debug = True
    return locals()


def search(item, text):
    logger.debug('search', text)
    item.contentType = 'tvshow'
    itemlist = []
    text = text.replace(' ', '+')
    item.url = host + '/index.php?story=%s&do=search&subaction=search' % (text)
    try:
        return peliculas(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error('search log:', line)
        return []


def findvideos(item):
    logger.debug()
    return support.server(item, item.url)
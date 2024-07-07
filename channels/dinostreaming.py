# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Dinostreaming
# by ilmich
# ------------------------------------------------------------

from core import httptools, support
from core.item import Item
from platformcode import logger

host = support.config.get_channel_url()
headers = [['Referer', host]]

@support.menu
def mainlist(item):
    film = [('Film al cinema',['/film-category/al-cinema/', 'peliculas']),
            ('Generi',['', 'genres']),
            ]
    search = ''
    return locals()

@support.scrape
def genres(item):
    action = 'peliculas'
    blacklist = ['Seguici su Telegram',]
    patronMenu = r'<li class="elementor-icon-list-item">.*?href="(?P<url>.*?)".*?text">(?P<title>.*?)</span>'
    
    return locals()

@support.scrape
def peliculas(item):
    if not item.args == 'search': # pagination not works
        if not item.nextpage:
            item.page = 1
        else:
            item.page = item.nextpage

        if not item.parent_url:
            item.parent_url = item.url

        item.nextpage = item.page + 1
        nextPageUrl = "{}/page/{}".format(item.parent_url, item.nextpage)
        
        resp = httptools.downloadpage(nextPageUrl, only_headers = True)
        if (resp.code > 399): # no more elements
            nextPageUrl = ''

    patron = r'<div data-elementor-type="loop-item".*?<a.*?url="(?P<thumb>[^"]+).*?<a href=\"(?P<url>[^"]+)\">(?P<title>.*?)</a>.*?<span class="elementor-heading-title elementor-size-default">(?P<year>.*?)</span>'

    def itemlistHook(itemlist):
        return itemlist[:-1:]
    return locals()

def search(item, text):
    item.url = "{}/?{}".format(host, support.urlencode({'s': text}))
    item.args = 'search'

    try:
        return peliculas(item)

    except:
        import sys
        for line in sys.exc_info():
            logger.error("search except: %s" % line)
        return []

def findvideos(item):
    support.info()    
    data = httptools.downloadpage(item.url).data
    video_url = support.match(data, patron=r'<a href="([^"]+)" rel="nofollow" title="Guarda il film in streaming">' ).match
    if (video_url == ''):
        return []

    item.url = video_url
    itemlist = support.server(item)
    return itemlist


# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Tantifilm
# ------------------------------------------------------------

from core import support
from core.item import Item
from platformcode import logger
from platformcode import config


host = config.get_channel_url()
headers = [['Referer', host]]

player_iframe = r'<iframe.*?src="([^"]+)"[^>]+></iframe>\s*<\/div'

@support.menu
def mainlist(item):

    top = [('Generi', ['', 'genres'])]
    film = ['/film']
    tvshow = ['/serie-tv/']
    search = ''

    return locals()


@support.scrape
def genres(item):

    blacklist = ['Ultimi Film Aggiornati', 'Anime', 'Serie TV Altadefinizione', 'HD AltaDefinizione', 'Al Cinema', 'Serie TV', 'Miniserie', 'Programmi Tv', 'Live', 'Trailers', 'Serie TV Aggiornate', 'Aggiornamenti', 'Featured']
    patronMenu = '<li><a href="(?P<url>[^"]+)"><span></span>(?P<title>[^<]+)</a></li>'
    patron_block = '<ul class="table-list">(.*?)</ul>'
    action = 'peliculas'

    return locals()


def search(item, text):    
    item.url = "{}/?{}".format(host, support.urlencode({'story': text,'do':'search', 'subaction':'search'}))
    #item.url = host + "/?story=" + texto
    try:
        item.args = 'search'
        return peliculas(item)

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

@support.scrape
def peliculas(item):
    action = 'check'
    item.contentType = 'undefined'
    if item.args == 'search':
        patron = r'<div class="film.*?<a href="(?P<url>[^"]+)"(?:[^>]+)?>?\s*(?:<img[^s]+src="(?P<thumb>[^"]+)"[^>]+>\s*)?<p>(?P<title>[^<]+?)(?P<lang>[sS][uU][bB]\-[iI][tT][aA]+)?(?:[ ]?\((?P<year>\d{4})-?(?:\d{4})?).*?\)[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s*(?P<quality>[a-zA-Z]+)?'
    else:
        patronNext = r'<b class="nextpostslink">.*?<a href="([^"]+)">'
        if 'serie-tv' in item.url:
            patron = r'<div class="mediaWrap mediaWrapAlt">\s*<a href="(?P<url>[^"]+)"(?:[^>]+)?>?\s*(?:<img[^s]+src="(?P<thumb>[^"]+)"[^>]+>\s*)?<\/a>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>[^<]+?)(?P<lang>[sS][uU][bB]\-[iI][tT][aA]+)?(?:[ ]?\((?P<year>\d{4})-?(?:\d{4})?).*?\)[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s*(?P<quality>[a-zA-Z]+)?'
        else:
            patron = r'<div class="mediaWrap mediaWrapAlt">\s*<a href="(?P<url>[^"]+)"(?:[^>]+)?>?\s*(?:<img[^s]+src="(?P<thumb>[^"]+)"[^>]+>\s*)?<\/a>[^>]+>[^>]+>[^>]+>(?P<title>[^<]+?)(?P<lang>[sS][uU][bB]\-[iI][tT][aA]+)?(?:[ ]?\((?P<year>\d{4})-?(?:\d{4})?).*?\)[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s*(?P<quality>[a-zA-Z]+)?'
        patronBlock = r'<div id="dle-content">(?P<block>.*?)<!\-\- main_col \-\->'

    return locals()

@support.scrape
def episodios(item):
    patron = r'data-num="(?P<season>.*?)x(?P<episode>.*?)"\s*data-title="(?P<title>[^"]+)(?P<lang>[sS][uU][bB]\-[iI][tT][aA]+)?".*?<div class="mirrors"(?P<server_links>.*?)<!---'
    action = 'findvideos'
    return locals()

def check(item):
    item.data = support.match(item.url, headers=headers).data
    check = support.match(item.data, patron=r'<div class="category-film">(.*?)</div>').match
    if 'sub' in check.lower():
        item.contentLanguage = 'Sub-ITA'
    logger.debug("CHECK : ", check)
    if 'serie' in check.lower():
        item.contentType = 'tvshow'
        return episodios(item)
    else:
        item.contentTitle = item.fulltitle
        item.contentType = 'movie'
        return findvideos(item)


def findvideos(item):
    if item.server_links:
        return support.server(item, data = item.server_links)

    video_url = support.match(item.url, patron=player_iframe).match

    if (video_url == ''):
       return []

    itemlist = [item.clone(action="play", url=srv) for srv in support.match(video_url, patron='<li class="(?:active)?" data-link=\"([^"]+)').matches]
    itemlist = support.server(item,itemlist=itemlist)
    return itemlist

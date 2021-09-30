# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per altadefinizione01
# ------------------------------------------------------------

from core import scrapertools, httptools, support
from core.item import Item
from platformcode import config, logger

# def findhost(url):
#     data = httptools.downloadpage(url).data
#     host = scrapertools.find_single_match(data, '<div class="elementor-button-wrapper"> <a href="([^"]+)"')
#     return host


host = config.get_channel_url()
headers = [['Referer', host]]


@support.menu
def mainlist(item):

    film = [
        ('Al Cinema', ['/cinema/', 'movies', 'pellicola']),
        ('Ultimi Aggiornati-Aggiunti', ['','movies', 'update']),
        ('Generi', ['', 'genres', 'genres']),
        ('Lettera', ['/catalog/a/', 'genres', 'az']),
        ('Anni', ['', 'genres', 'years']),
        ('Sub-ITA', ['/sub-ita/', 'movies', 'pellicola'])
    ]

    return locals()


@support.scrape
def movies(item):

    action="findvideos"

    patron = r'<div class="cover boxcaption"> +<h2>\s*<a href="(?P<url>[^"]+)">(?P<title>[^<]+).*?src="(?P<thumb>[^"]+).*?<div class="trdublaj">(?P<quality>[^<]+).*?<span class="ml-label">(?P<year>[0-9]+).*?<span class="ml-label">(?P<duration>[^<]+).*?<p>(?P<plot>[^<]+)'

    if item.args == "search":
        patronBlock = r'</script> <div class="boxgrid caption">(?P<block>.*)<div id="right_bar">'

    elif item.args == 'update':
        patronBlock = r'<div class="widget-title">Ultimi Film Aggiunti/Aggiornati</div>(?P<block>.*?)<div id="alt_menu">'
        patron = r'style="background-image:url\((?P<thumb>[^\)]+).+?<p class="h4">(?P<title>.*?)</p>[^>]+> [^>]+> [^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+> [^>]+> [^>]+>[^>]+>(?P<year>\d{4})[^>]+>[^>]+> [^>]+>[^>]+>(?P<duration>\d+|N/A).+?>.*?(?:>Film (?P<lang>Sub ITA)</a></p> )?<p>(?P<plot>[^<]+)<.*?href="(?P<url>[^"]+)'
    elif item.args == 'az':
        patron = r'<td class="mlnh-thumb"><a href="(?P<url>[^"]+)".*?src="(?P<thumb>[^"]+)"' \
                 '.+?[^>]+>[^>]+ [^>]+[^>]+ [^>]+>(?P<title>[^<]+).*?[^>]+>(?P<year>\d{4})<' \
                 '[^>]+>[^>]+>(?P<quality>[A-Z]+)[^>]+> <td class="mlnh-5">(?P<lang>.*?)</td>'
    else:
        patronBlock = r'<div class="cover_kapsul ml-mask">(?P<block>.*)<div class="page_nav">'

    patronNext =  r'<a href="([^"]+)">&raquo;'
    patronTotalPages = r'>(\d+)(?:[^>]+>){3}&raquo;'

    return locals()


@support.scrape
def genres(item):
    action = "movies"

    blacklist = ['Altadefinizione01']
    if item.args == 'genres':
        patronBlock = r'<ul class="kategori_list">(?P<block>.*?)<div class="tab-pane fade" id="wtab2">'
        patronGenreMenu = '<li><a href="(?P<url>[^"]+)">(?P<title>.*?)</a>'
    elif item.args == 'years':
        patronBlock = r'<ul class="anno_list">(?P<block>.*?)</li> </ul> </div>'
        patronMenu = '<li><a href="(?P<url>[^"]+)">(?P<title>.*?)</a>'
    elif item.args == 'az':
        patronBlock = r'<div class="movies-letter">(?P<block>.*?)<div class="clearfix">'
        patronMenu = '<a title=.*?href="(?P<url>[^"]+)"><span>(?P<title>.*?)</span>'

    return locals()

@support.scrape
def az(item):

    action = 'findvideos'
    patron = r'<td class="mlnh-thumb"><a href="(?P<url>[^"]+)".*?src="(?P<thumb>[^"]+)"'\
             '.+?[^>]+>[^>]+ [^>]+[^>]+ [^>]+>(?P<title>[^<]+).*?[^>]+>(?P<year>\d{4})<'\
             '[^>]+>[^>]+>(?P<quality>[A-Z]+)[^>]+> <td class="mlnh-5">(?P<lang>.*?)</td>'

    return locals()


def search(item, text):
    logger.debug(text)


    itemlist = []
    text = text.replace(" ", "+")
    item.url = host + "/index.php?do=search&story=%s&subaction=search" % (text)
    item.args = "search"
    try:
        return movies(item)
    # Cattura la eccezione così non interrompe la ricerca globle se il canale si rompe!
    except:
        import sys
        for line in sys.exc_info():
            logger.error("search except: %s" % line)
        return []

def newest(category):
    logger.debug(category)

    itemlist = []
    item = Item()
    try:
        if category == "movie":
            item.url = host
            item.action = "movies"
            item.contentType = 'movie'
            itemlist = movies(item)
            if itemlist[-1].action == "movies":
                itemlist.pop()
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist

def findvideos(item):
    logger.debug()
    data = httptools.downloadpage(item.url).data
    iframe = support.match(data, patron='player-container[^>]+>\s*<iframe[^>]+src="([^"]+)').match
    if iframe:
        item.url = iframe
        return support.server(item)
    else:
        itemlist = [item.clone(action="play", url=srv[0], quality=srv[1]) for srv in support.match(item, patron='<a href="#" data-link="([^"]+).*?<span class="d">([^<]+)').matches]
        return support.server(item, itemlist=itemlist, headers=headers)

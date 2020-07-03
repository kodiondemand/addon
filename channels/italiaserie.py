# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per italiaserie
# ------------------------------------------------------------
"""

    Problemi noti che non superano il test del canale:


    Avvisi:


    Ulteriori info:

"""

import re
from core import support, httptools, scrapertools
from core.item import Item
from platformcode import config

host = config.get_channel_url()
headers = [['Referer', host]]


@support.menu
def mainlist(item):
    support.log()

    tvshow = ['/category/serie-tv/',
        ('Aggiornamenti', ['/ultimi-episodi/', 'peliculas', 'update']),
        ('Generi', ['', 'category', 'Serie-Tv per Genere'])
        ]

    return locals()


@support.scrape
def peliculas(item):
    support.log()

    action = 'episodios'
    patron = r'<div class="post-thumb">\s*<a href="(?P<url>[^"]+)" '\
             'title="(?P<title>[^"]+)">\s*<img src="(?P<thumb>[^"]+)"[^>]+>'

    if item.args == 'update':
        patron += r'.*?aj-eps">(?P<episode>.+?)[ ]?(?P<lang>Sub-Ita|Ita)</span>'
        action = 'findvideos'
    patronNext = r'<a class="next page-numbers" href="(.*?)">'

##    debug = True
    return locals()


@support.scrape
def episodios(item):
    support.log()

    patronBlock = r'</i> Stagione (?P<block>(?P<season>\d+)</div> '\
                  '<div class="su-spoiler-content".*?)<div class="clearfix">'
    patron = r'(?:(?P<season>\d+)?</div> <div class="su-spoiler-content"(:?.+?)?> )?'\
             '<div class="su-link-ep">\s+<a.*?href="(?P<url>[^"]+)".*?strong>[ ]'\
             '(?P<title>.+?)[ ](?P<episode>\d+-\d+|\d+)[ ](?:-\s+(?P<title2>.+?))?'\
             '[ ]?(?:(?P<lang>Sub-ITA))?[ ]?</strong>'


    #debug = True
    return locals()


@support.scrape
def category(item):
    support.log()

    action = 'peliculas'
    patron = r'<li class="cat-item.*?href="(?P<url>[^"]+)".*?>(?P<title>.*?)</a>'

    return locals()


def search(item, texto):
    support.log("s=", texto)
    item.url = host + "/?s=" + texto
    item.contentType = 'tvshow'
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    support.log("newest", categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "series":
            item.url = host + "/ultimi-episodi/"
            item.action = "peliculas"
            item.args = "update"
            item.contentType = "episode"
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
    support.log()

    if item.args == 'update':
        itemlist = []
        item.infoLabels['mediatype'] = 'episode'

        data = httptools.downloadpage(item.url, headers=headers).data
        data = re.sub('\n|\t', ' ', data)
        data = re.sub(r'>\s+<', '> <', data)
        url_video = scrapertools.find_single_match(data, r'<a rel="[^"]+" target="[^"]+" act="[^"]+"\s+href="([^"]+)" class="[^"]+-link".+?\d+.+?</strong> </a>', -1)
        url_serie = scrapertools.find_single_match(data, r'<link rel="canonical" href="([^"]+)" />')
        goseries = support.typo("Vai alla Serie:", ' bold')
        series = support.typo(item.contentSerieName, ' bold color kod')
        itemlist = support.server(item, data=url_video)

        itemlist.append(
            Item(channel=item.channel,
                    title=goseries + series,
                    fulltitle=item.fulltitle,
                    show=item.show,
                    contentType='tvshow',
                    contentSerieName=item.contentSerieName,
                    url=url_serie,
                    action='episodios',
                    contentTitle=item.contentSerieName,
                    plot = goseries + series + "con tutte le puntate",
                    ))

        return itemlist
    else:
        return support.server(item, data=item.url)

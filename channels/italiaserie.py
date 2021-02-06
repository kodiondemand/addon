# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per italiaserie
# ------------------------------------------------------------


from core import support, httptools, scrapertools
from core.item import Item
from platformcode import config, logger

host = config.get_channel_url()
headers = [['Referer', host]]


@support.menu
def mainlist(item):
    tvshow = ['',
        ('Aggiornamenti', ['/aggiornamento-episodi/', 'peliculas', 'update']),
        ('Top 10', ['/top-10', 'peliculas', 'top']),
        ('Netflix {tv submenu}', ['/genere/netflix', 'peliculas'])
        ]

    return locals()


@support.scrape
def peliculas(item):
    # debug=True
    blacklist = ['Aggiornamento Episodi']
    action = 'episodios'
    patron = r'<div class="post-thumb">\s*<a href="(?P<url>[^"]+)" title="(?P<title>[^"\[]+)[^>]+>\s*<img src="(?P<thumb>[^"]+)"[^>]+>'

    if item.args == 'update':
        pagination = ''
        #patron = r'br />(?:[^>]+>)?(?P<title>[^–]+)[^<]+<a href="(?P<url>[^"]+)">(?P<episode>[^ ]+)\s*(?P<title2>[^\(<]+)(?:\((?P<lang>[^\)]+))?'
        patron = r'br[\s/]*>(?:\s*<[^>]+>)*(?P<title>[^–<]+)[^<]+<a href="(?P<url>[^"]+)"[^>]*>(?:[^,]{0,80}[, ]{2})*(?P<episode>[\S]+)\s*(?P<title2>[^\(<]+)(?:\((?P<lang>[^\)]+))?'
        action = 'episodios'
    if item.args == 'top':
        patron = r'<a href="(?P<url>[^"]+)">(?P<title>[^<]+)</a>(?:[^>]+>){3}<img.*?src="(?P<thumb>[^"]+)"[^>]+>(?:[^>]+>){5}:\s*(?P<rating>[^/]+)'
    if item.args =='a-z':
        pagination = ''
        patron = r'<li ><a href="(?P<url>[^"]+)" title="(?P<title>[^"]+)"'
    patronNext = r'<a class="next page-numbers" href="(.*?)">'

    def itemHook(item):
        item.title = support.re.sub(r'<[^>]+>','', item.title)
        return item

    return locals()


@support.scrape
def episodios(item):
    res = support.match(item, patron=r'<a href="([^"]+)">&gt;')
    if res.match: data = support.match(res.match).data
    else: data = res.data

    patronBlock = r'(?:Stagione|STAGIONE)\s*(?P<lang>[^<]+)?(?:</p>)?(?P<block>.*?)</p>'
    patron = r'(?:p>|/>)(?P<title>[^–]+)–(?P<data>.*?)(?:<br|$)'

    def itemHook(item):
        item.title = support.re.sub('<[^>]+>','', item.title)
        return item
    return locals()


@support.scrape
def category(item):
    action = 'peliculas'
    patron = r'<li class="cat-item.*?href="(?P<url>[^"]+)".*?>(?P<title>.*?)</a>'
    return locals()


def search(item, texto):
    support.info("s=", texto)
    item.url = host + "/?s=" + texto
    item.contentType = 'tvshow'
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.info("%s" % line)
        return []


def newest(categoria):
    support.info("newest", categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "series":
            item.url = host + "/aggiornamento-episodi/"
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
    logger.debug()
    data = support.match(item.data, patron=r'href="([^"]+)').matches
    return support.server(item, data=data)

# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per altadefinizione
# ------------------------------------------------------------


from core import httptools, support
from platformcode import config, logger


def findhost(url):
    host = support.match(url, patron=r'<h2[^>]+><a href="([^"]+)').match.rstrip('/')
    permUrl = httptools.downloadpage(host, follow_redirects=False).headers
    return permUrl['location']

host = config.get_channel_url(findhost)
headers = [['Referer', host]]

@support.menu
def mainlist(item):

    film = ['/category/film/',
            ('Al Cinema', ['/category/ora-al-cinema/', 'peliculas']),
            ('Generi', ['', 'genres']),
            # ('Sub-ITA', ['/sub-ita/', 'peliculas'])
            ]

    tvshow = ['/category/serie-tv/',
             ('Aggiornamenti Serie TV', ['/aggiornamenti-serie-tv/', 'peliculas']),]

    search = ''

    return locals()


@support.scrape
def genres(item):
    action = 'peliculas'
    blacklist = ['Scegli il Genere', 'Film', 'Serie Tv', 'Sub-Ita', 'Anime', "Non reperibile", 'Anime Sub-ITA', 'Prossimamente',]
    patronBlock = r'(?<=<ul class="listSubCat" id="Film">)(?P<block>.*?)(?=<\/ul>)'
    patron = r'<a href=\"(?P<url>https:\/\/.*?)\"> (?P<title>.*?) </a>'

    def itemlistHook(itemlist):
        itl = []
        for item in itemlist:
            if len(item.fulltitle) != 3:
                itl.append(item)
        return itl
    return locals()


def search(item, text):
    logger.debug(text)
    item.url = "{}/?{}".format(host, support.urlencode({'s': text}))
    item.args = 'search'

    try:
        return peliculas(item)

    except:
        import sys
        for line in sys.exc_info():
            logger.error("search except: %s" % line)
        return []


@support.scrape
def peliculas(item):
    item.contentType = "undefined"
    action = 'check'
    patron = r'<h2 class=\"titleFilm\"><a href=\"(?P<url>[^\"]+)\">(?P<title>[\'’\+A-Za-zÀ-ÿ\d\s&#8217;&#8211;:\.-]*)\s*\[?(?P<quality>[a-zA-Z]*)\]?\s*\(?(?P<year>[0-9]*)\)?'

    if item.args == 'search':
          patron = r'<div class="col-lg-3 col-md-3 [^>]*> <a href=\"(?P<url>[^\"]+)\">.*?(?=<h5).*?(?=>)>(?P<title>[\'’\+A-Za-zÀ-ÿ\d\s&#8217;&#8211;:\.-]*)\s*\[?(?P<quality>[a-zA-Z]*)\]?\s*\(?(?P<year>[0-9]*)\)?'
    patronNext = r'href="([^"]+)[^>]+>Successivo'
    return locals()


@support.scrape
def episodios(item):
    item.quality = ''
    data = item.data
    action='findvideos'
    patron = r'<div class="episode-wrap".*?(?=<li class="season-no">).*?(?=>)>(?P<episode>[^<]+).*?(?=<a)<a href="(?P<url>[^\"]+).*?(?=>)>(?P<title>[\'’\+A-Za-zÀ-ÿ\d\s&#8217;&#8211;:\.-]*)'
    return locals()


def check(item):
    item.data = httptools.downloadpage(item.url).data
    if 'stagione' in item.data.lower():
        item.contentType = 'tvshow'
        return episodios(item)
    else:
        return findvideos(item)


def findvideos(item):
    video_url = item.url

    if item.contentType == 'movie':
        video_url = support.match(item, patron=r'<div class="embed-player" data-id=\"(https://.*?)\"').match

    itemlist = [item.clone(action="play", url=srv) for srv in support.match(video_url, patron='<div class="megaButton" meta-type="v" meta-link="([^"]+).*?(?=>)>').matches]
    itemlist = support.server(item,itemlist=itemlist)
    
    return itemlist


# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per ilcorsaronero
# ------------------------------------------------------------

from core import support, httptools

# def findhost(url):
#     data = support.httptools.downloadpage(url).data
#     url = support.scrapertools.find_single_match(data, '<li><a href="([^"]+)')
#     return url[:-1] if url.endswith('/') else url

host = support.config.get_channel_url()
support.info('HOST',host)
# host = 'https://ilcorsaronero.xyz'
headers = [['Referer', host]]


@support.menu
def mainlist(item):

    menu = [
        ('Film {film}', ['/cat/film', 'peliculas', [0, 'movie', True], 'undefined']),
	('Serie TV', ['/cat/serie-tv', 'peliculas', [0 , 'tvshow', True], 'tvshow']),
	('Animazione', ['/cat/animazione', 'peliculas', [0 , 'anime', True], 'tvshow']),
	('Documentari', ['/cat/altro/documentari', 'peliculas', [0 , 'documentary', True], 'tvshow']),
	('Programmi TV', ['/cat/altro/programmi-tv', 'peliculas', [0 , 'tvshow', True], 'tvshow'])
    ]
    search = ''

    return locals()


@support.scrape
def peliculas(item):
    debug = False
    action = 'findvideos'
    sceneTitle = item.args[2]
    if not item.args == 'search': # pagination not works
        if not item.nextpage:
            item.page = 1
        else:
            item.page = item.nextpage

        if not item.parent_url:
            item.parent_url = item.url

        item.nextpage = item.page + 1
        nextPageUrl = "{}?page={}".format(item.parent_url, item.nextpage)
        
        resp = httptools.downloadpage(nextPageUrl, only_headers = True)
        if (resp.code > 399): # no more elements
            nextPageUrl = ''

    def itemHook(item):
        if not sceneTitle:
            item.title = item.title.replace('_', ' ')
            item.fulltitle = item.fulltitle.replace('_', ' ')
        item.title = support.scrapertools.decodeHtmlentities(support.urlparse.unquote(item.title))

        return item

    patron = r'<a class="hover:underline line-clamp-1.*?href="(?P<url>[^"]+)"\s*>(?P<title>.*?)</a>'
        
    return locals()

def search(item, text):
    item.url = "{}/search?{}".format(host, support.urlencode({'q': text}))
    item.args = 'search'

    try:
        return peliculas(item)

    except:
        import sys
        for line in sys.exc_info():
            logger.error("search except: %s" % line)
        return []


def findvideos(item):
    if item.contentType == 'tvshow': item.contentType = 'episode'
    Videolibrary = True if 'movie' in item.args else False
    return support.server(item, support.match(item.url, patron=r'"(magnet[^"]+)').match, Videolibrary=Videolibrary)

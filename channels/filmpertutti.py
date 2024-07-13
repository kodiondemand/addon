# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per filmpertutti.py
# ------------------------------------------------------------

from core import httptools, support, scrapertools
from core.item import Item
from platformcode import config, logger

def findhost(url):
    page = httptools.downloadpage(url).data
    url = support.scrapertools.find_single_match(page, 'Il nuovo indirizzo di FILMPERTUTTI è ?<a href="([^"]+)')
    return url

host = config.get_channel_url(findhost)
headers = [['Referer', host]]


@support.menu
def mainlist(item):

    film = ['/category/film/feed/',
            ('Film al cinema', ['/category/ora-al-cinema/feed/', 'peliculas']),
            ('Generi', ['/', 'genres']),
	    ('Saghe', ['/', 'genres', 'saghe']),
           ]

    tvshow = ['/category/serie-tv/feed/',
             ]

    search = ''
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
        
        if item.args == 'genres':
            action = 'check'

        item.nextpage = item.page + 1
        nextPageUrl = "{}/?paged={}".format(item.parent_url, item.nextpage)
        patron= r'<item>\s<title>(?P<title>[^<]+?)\s*(\((?P<lang>Sub-[a-zA-Z]+)*\))?\s*(\[(?P<quality>[A-Z]*)\])?\s*(\((?P<year>[0-9]{4})\))?</title>.*?<link>(?P<url>.*?)</link>'
        def fullItemlistHook(itemlist):
            if len(itemlist) < 10:
                return itemlist[:-1:]
            else:
                return itemlist
    else:
        action = 'check'
        patron= r'<article class=\"elementor-post.*?(<img .*?src=\"(?P<thumb>[^\"]+).*?)?<h3 class=\"elementor-post__title\".*?<a href=\"(?P<url>[^\"]+)\" >\s*(?P<title>[^<]+?)\s*(\((?P<lang>Sub-[a-zA-Z]+)*\))?\s*(\[(?P<quality>[A-Z]*)\])?\s*(\((?P<year>[0-9]{4})\))?\s+<'

    return locals()

def episodios(item):
    item.quality = ''
    data = item.data if item.data else httptools.downloadpage(item.url).data
    itemlist = []

    for it in support.match(data, patron=[r'div class=\"single-season.*?(?P<id>season_[0-9]+).*?>Stagione:\s(?P<season>[0-9]+).*?(\s-\s(?P<lang>[a-zA-z]+?))?<']).matches:
        block = support.match(data, patron = r'div id=\"'+ it[0] +'\".*?</div').match
        for ep in support.match(block, patron=[r'<li><a href=\"(?P<url>[^\"]+).*?img\" src=\"(?P<thumb>[^\"]+).*?title\">(?P<episode>[0-9]+)\.\s+(?P<title>.*?)</span>']).matches:
            itemlist.append(item.clone(contentType = 'episode',
                                   action='findvideos',
                                   thumb = ep[1],
                                   title = support.format_longtitle(support.cleantitle(ep[3]), season = it[1], episode = ep[2], lang= it[3]),
                                   url = ep[0], data = '')
                        )

    support.check_trakt(itemlist)
    support.videolibrary(itemlist, item)
    if (config.get_setting('downloadenabled')):    
        support.download(itemlist, item)

    return itemlist

@support.scrape
def genres(item):
    action = 'peliculas'
    item.args = 'genres'
    blacklist = ['Tutti i film',]
    wantSaga = True if item.args == 'saghe' else False

    patronBlock = r'<nav class="elementor-nav-menu--main (?P<block>.*?)</nav>'
    patronMenu = r'<li class="menu-item.*?<a href="(?P<url>https:\/\/.*?)".*?>(?P<title>.*?)</a></li>'

    def itemHook(item):
        item.url = "{}/feed/".format(item.url)
        return item
	
    def itemlistHook(itemlist):
        itl = []
        for item in itemlist:
            isSaga = item.fulltitle.startswith('Saga')

            if len(item.fulltitle) != 3:
                if (isSaga and wantSaga) or (not isSaga and not wantSaga):
                    itl.append(item)
        return itl
    return locals()


def check(item):
    item.data = httptools.downloadpage(item.url).data
    if 'season-details' in item.data.lower():
        item.contentType = 'tvshow'
        return episodios(item)
    else:
        item.contentType = 'movie'
        return findvideos(item)


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


def newest(categoria):
    support.info()
    itemlist = []
    item = Item()
    try:
        if categoria == "peliculas":
            item.url = host + "/category/film/feed/"
            item.action = "peliculas"
            item.extra = "movie"
            item.contentType = 'movie'
            itemlist = peliculas(item)
        else:
            item.url = host + "/category/serie-tv/feed/"
            item.action = "peliculas"
            item.args = "newest"
            item.contentType = 'tvshow'
            itemlist = peliculas(item)

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.info("{0}".format(line))
        return []

    return itemlist


def findvideos(item):
    video_url = item.url
    
    if item.contentType == 'movie':
        video_url = support.match(item.url, patron=r'<a href="([^"]+)" rel="nofollow">').match    
        
    video_url = support.match(video_url, patron=r'<iframe src=\"(https://.*?)\"').match

    if (video_url == ''):
       return []

    itemlist = [item.clone(action="play", url=srv) for srv in support.match(video_url, patron='<div class=\"megaButton\" meta-type=\"v\" meta-link=\"([^\"]+).*?(?=>)>').matches]
    itemlist = support.server(item,itemlist=itemlist)
    return itemlist

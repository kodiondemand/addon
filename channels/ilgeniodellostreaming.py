# -*- coding: utf-8 -*-
# ------------------------------------------------------------
#
# Canale per ilgeniodellostreaming
# ------------------------------------------------------------


from core import support
from core.item import Item
from platformcode import config, logger

host = config.get_channel_url()
headers = [['Referer', host]]

@support.menu
def mainlist(item):

    film = ['/film/',
        ('Generi',['', 'genres', 'genres']),
        ('Per Lettera',['/film-a-z/', 'genres', 'letter']),
        ('Anni',['', 'genres', 'year']),
        ('Popolari',['/trending/?get=movies', 'movies', 'populared']),
        ('Più Votati', ['/ratings/?get=movies', 'movies', 'populared'])
        ]

    tvshow = ['/serie/',
        ('Aggiornamenti', ['/aggiornamenti-serie/', 'movies', 'update']),
        ('Popolari',['/trending/?get=tv', 'movies', 'populared']),
        ('Più Votati', ['/ratings/?get=tv', 'movies', 'populared'])

        ]

    anime = ['/anime/'
        ]

    Tvshow = [
        ('Show TV {bullet bold}', ['/tv-show/', 'movies', '', 'tvshow'])
        ]

    search = ''

    return locals()


@support.scrape
def movies(item):
    logger.debug()
    # debugBlock = True
    # debug=True

    if item.args == 'search':
        patronBlock = r'<div class="search-page">(?P<block>.*?)<footer class="main">'
        patron = r'<img src="(?P<thumb>[^"]+)" alt="[^"]+" ?/?>[^>]+>(?P<type>[^<]+)</span>.*?<a href="(?P<url>[^"]+)">(?P<title>.+?)[ ]?(?:\[(?P<lang>Sub-ITA)\])?</a>[^>]+>[^>]+>(?:<span class="rating">IMDb\s*(?P<rating>[^>]+)</span>)?.?(?:<span class="year">(?P<year>[0-9]+)</span>)?.*?<p>(?P<plot>.*?)</p>'

        typeContentDict={'movie': ['film'], 'tvshow': ['tv']}
        typeActionDict={'findvideos': ['film'], 'episodes': ['tv']}
    else:

        if item.contentType == 'movie':
            endBlock = '</article></div>'
        else:
            endBlock = '<footer class="main">'

        patronBlock = r'<header><h1>.+?</h1>(?P<block>.*?)'+endBlock

        if item.contentType == 'movie':
            if item.args == 'letter':
                patronBlock = r'<table class="table table-striped">(?P<block>.+?)</table>'
                patron = r'<img src="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+><td class="mlnh-2"><a href="(?P<url>[^"]+)">(?P<title>.+?)[ ]?(?:\[(?P<lang>Sub-ITA)\])?<[^>]+>[^>]+>[^>]+>(?P<year>\d{4})\s+<'
            elif item.args == 'populared':
                patron = r'<img src="(?P<thumb>[^"]+)" alt="[^"]+">[^>]+>[^>]+>[^>]+>[^>]+>\s+?(?P<rating>\d+.?\d+|\d+)<[^>]+>[^>]+>(?P<quality>[a-zA-Z\-]+)[^>]+>[^>]+>[^>]+>[^>]+><a href="(?P<url>[^"]+)">(?P<title>[^<]+)<[^>]+>[^>]+>[^>]+>(?P<year>\d+)<'
            else:

                #patron = r'<div class="poster">\s*<a href="(?P<url>[^"]+)"><img src="(?P<thumb>[^"]+)" alt="[^"]+"><\/a>[^>]+>[^>]+>[^>]+>\s*(?P<rating>[0-9.]+)<\/div><span class="quality">(?:SUB-ITA|)?(?P<quality>|[^<]+)?<\/span>[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>.+?)[ ]?(?:\[(?P<lang>Sub-ITA)\])?<\/a>[^>]+>[^>]+>(?P<year>[^<]+)<\/span>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<plot>[^<]+)<div'
                patron = r'<div class="poster">\s?<a href="(?P<url>[^"]+)"><img src="(?P<thumb>[^"]+)" alt="[^"]+"><\/a>[^>]+>[^>]+>[^>]+>\s*(?P<rating>[0-9.]+)<\/div>(?:<span class="quality">(?:SUB-ITA|)?(?P<quality>|[^<]+)?<\/span>)?[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>.+?)[ ]?(?:\[(?P<lang>Sub-ITA)\])?<\/a>[^>]+>[^>]+>(?P<year>[^<]+)<\/span>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<plot>[^<]+)<div'
        else:
            # TVSHOW
            action = 'episodes'
            if item.args == 'update':
                action = 'findvideos'
                patron = r'<div class="poster"><img src="(?P<thumb>[^"]+)"(?:[^>]+>){2}<a href="(?P<url>[^"]+)">[^>]+>(?P<episode>[\d\-x]+)(?:[^>]+>){4}(?P<title>.+?)(?:\[(?P<lang>[SsuUbBiItTaA-]{7})\])?<(?:[^>]+>){4}(?P<quality>[HDWEBRIP-]+)?(?:.+?)?/span><p class="serie"'
                pagination = True
                def itemHook(item):
                    item.contentType = 'episode'
                    return item
            else:
                patron = r'<div class="poster">\s?<a href="(?P<url>[^"]+)"><img src="(?P<thumb>[^"]+)" alt="[^"]+"><\/a>[^>]+>[^>]+>[^>]+> (?P<rating>[0-9.]+)<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>.+?)[ ]?(?:\[(?P<lang>Sub-ITA|Sub-ita)\])?<[^>]+>[^>]+>[^>]+>(?P<year>[0-9]{4})?[^<]*(?:<.*?<div class="texto">(?P<plot>[^<]+)?)?'
    patronNext = '<span class="current">[^<]+<[^>]+><a href=[\'"]([^\'"]+)[\'"]'

    #support.regexDbg(item, patron, headers)
    # debug = True
    return locals()


@support.scrape
def episodes(item):
    logger.debug()

    patronBlock = r'<h1>.*?[ ]?(?:\[(?P<lang>.+?\]))?</h1>.+?<div class="se-a" style="display:block">\s*<ul class="episodes">(?P<block>.*?)</ul>\s*</div>\s*</div>\s*</div>\s*</div>\s*</div>'
    patron = r'<a href="(?P<url>[^"]+)"><img src="(?P<thumb>[^"]+)">.*?'\
             '<div class="numerando">(?P<episode>[^<]+).*?<div class="episodiotitle">'\
             '[^>]+>(?P<title>[^<]+)<\/a>'
    # debugBlock = True
    return locals()


@support.scrape
def genres(item):
    logger.debug(item)

    action='movies'
    if item.args == 'genres':
        patronBlock = r'<div class="sidemenu"><h2>Genere</h2>(?P<block>.*?)/li></ul></div>'
    elif item.args == 'year':
        item.args = 'genres'
        patronBlock = r'<div class="sidemenu"><h2>Anno di uscita</h2>(?P<block>.*?)/li></ul></div>'
    elif item.args == 'letter':
        patronBlock = r'<div class="movies-letter">(?P<block>.*?)<div class="clearfix">'

    patronMenu = r'<a(?:.+?)?href="(?P<url>.*?)"[ ]?>(?P<title>.*?)<\/a>'
    # debugBlock = True

    return locals()


def search(item, text):
    logger.debug(text)
    import uuid
    text = text.replace(' ', '+')
    item.url = host + '/?' + uuid.uuid4().hex + '=' + uuid.uuid4().hex + '&s=' + text
    try:
        item.args = 'search'
        return movies(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)

    return []

def newest(category):
    logger.debug(category)
    itemlist = []
    item = Item()

    if category == 'movie':
        item.contentType = 'movie'
        item.url = host + '/film/'
    elif category == 'tvshow':
        item.args = 'update'
        item.contentType = 'tvshow'
        item.url = host + '/aggiornamenti-serie/'
##    elif category == 'anime':
##        item.contentType = 'tvshow'
##        item.url = host + '/anime/'
    try:
        item.action = 'movies'
        itemlist = movies(item)

    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def findvideos(item):
    logger.debug()
    matches = support.match(item, patron=[r'var ilinks\s?=\s?([^;]+)',r' href="#option-\d">([^\s]+)\s*([^\s]+)']).matches
    itemlist = []
    list_url = []
    list_quality = []
    list_servers = []
    for match in matches:
        if type(match) == tuple:
            list_servers.append(match[0])
            list_quality.append(match[1])
        else:
            import ast, base64
            encLinks = ast.literal_eval(match)

            for link in encLinks:
                linkDec = base64.b64decode(link.encode()).decode()
                if 'player.php' in linkDec:
                    linkDec = support.httptools.downloadpage(linkDec, only_headers=True, follow_redirects=False).headers.get('Location')
                if linkDec:
                    list_url.append(linkDec)
    if list_servers:
        for i, url in enumerate(list_url):
            itemlist.append(support.Item(
                    channel=item.channel,
                    # title=list_servers[i],
                    url=url,
                    action='play',
                    quality=list_quality[i],
                    infoLabels=item.infoLabels))

    return support.server(item, itemlist=itemlist)

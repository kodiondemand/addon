# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per animeuniverse
# ----------------------------------------------------------

from core import support
from platformcode import logger

host = support.config.get_channel_url()
headers = {}

perpage_list = ['20','30','40','50','60','70','80','90','100']
perpage = perpage_list[support.config.get_setting('perpage' , 'animeuniverse')]
epPatron = r'<td>\s*(?P<title>[^ <]+)\s*(?P<episode>\d+)?[^>]+>[^>]+>\s*<a href="(?P<url>[^"]+)"'


@support.menu
def mainlist(item):
    anime=['/anime/',
           ('Tipo',['', 'menu', 'Anime']),
           ('Anno',['', 'menu', 'Anno']),
           ('Genere', ['', 'menu','Genere']),
           ('Ultimi Episodi',['/2/', 'movies', 'last']),
           ('Hentai', ['/hentai/', 'movies'])]
    return locals()


@support.scrape
def menu(item):
    action = 'movies'
    patronBlock = item.args + r'</a>\s*<ul class="sub-menu">(?P<block>.*?)</ul>'
    patronMenu = r'<a href="(?P<url>[^"]+)">(?P<title>[^<]+)<'
    if 'genere' in item.args.lower():
        patronGenreMenu = patronMenu
    return locals()


def search(item, text):
    logger.debug(text)
    item.search = text
    try:
        return movies(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(category):
    logger.debug(category)
    item = support.Item()
    try:
        if category == "anime":
            item.url = host
            item.args = "last"
            return movies(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []


@support.scrape
def movies(item):
    query = ''
    if '/mos/' in item.url:
        item.contentType = 'movie'
        action='findvideos'
    elif item.args == 'last':
        query='cat%5D=1&currentquery%5Bcategory__not_in%5D%5B'
        searchtext=''
        item.contentType = 'episode'
        action='findvideos'
    else:
        item.contentType = 'tvshow'
        action='episodes'
    if item.search:
        query = 's'
        searchtext = item.search
    if not query:
        query='category_name'
        searchtext = item.url.split('/')[-2] if item.url != host else ''
    if not item.pag: item.pag = 1

    numerationEnabled = False
    # blacklist=['Altri Hentai']
    data = support.match(host + '/wp-content/themes/animeuniverse/functions/ajax.php', post='sorter=recent&location=&loop=main+loop&action=sort&numarticles='+perpage+'&paginated='+str(item.pag)+'&currentquery%5B'+query+'%5D='+searchtext+'&thumbnail=1').data.replace('\\','')
    patron=r'<a href="(?P<url>[^"]+)"><img width="[^"]+" height="[^"]+" src="(?P<thumb>[^"]+)" class="[^"]+" alt="" title="(?P<title>.*?)\s*(?P<lang>Sub ITA|ITA)?(?:"| \[)'

    def itemlistHook(itemlist):
        if len(itemlist) == int(perpage):
            item.pag += 1
            itemlist.append(item.clone(title=support.typo(support.config.get_localized_string(30992), 'color kod bold'), action='movies'))
        return itemlist
    return locals()




@support.scrape
def episodes(item):
    numerationEnabled = True
    pagination = True
    patron = epPatron
    return locals()


def findvideos(item):
    itemlist = []
    if item.contentType == 'movie':
        matches = support.match(item, patron=epPatron).matches
        for title, url in matches:
            get_video_list(url, title, itemlist)
    else:
        get_video_list(item.url, support.config.get_localized_string(30137), itemlist)
    return support.server(item, itemlist=itemlist)


def get_video_list(url, title, itemlist):
    from requests import get
    if not url.startswith('http'): url = host + url

    url = support.match(get(url).url, string=True, patron=r'file=([^$]+)').match
    if 'http' not in url: url = 'http://' + url
    itemlist.append(support.Item(title=title, url=url, server='directo', action='play'))

    return itemlist

# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per animeworld
# thanks to fatshotty
# ----------------------------------------------------------

from core import httptools, support, jsontools
from platformcode import logger

host = support.config.get_channel_url()
__channel__ = 'animeworld'
cookie = support.config.get_setting('cookie', __channel__)
headers = [['Cookie', cookie]]


def get_cookie(data):
    global cookie, headers
    cookie = support.match(data, patron=r'document.cookie="([^\s]+)').match
    support.config.set_setting('cookie', cookie, __channel__)
    headers = [['Cookie', cookie]]


def get_data(item):
    data = ''
    if item.url:
        url = httptools.downloadpage(item.url, headers=headers, follow_redirects=True, only_headers=True).url
        data = support.match(url, headers=headers, follow_redirects=True).data
        if 'AWCookieVerify' in data:
            get_cookie(data)
            data = get_data(item)
    return data


def order():
    # Seleziona l'ordinamento dei risultati
    return str(support.config.get_setting("order", __channel__))


@support.menu
def mainlist(item):
    anime=['/filter?sort=',
           ('ITA',['/filter?dub=1&sort=', 'menu', '1']),
           ('SUB-ITA',['/filter?dub=0&sort=', 'menu', '0']),
           ('In Corso', ['/ongoing', 'movies','noorder']),
           ('Ultimi Episodi', ['/updated', 'movies', 'updated']),
           ('Nuove Aggiunte',['/newest', 'movies','noorder' ]),
           ('Generi',['/?d=1','genres',])]
    return locals()


@support.scrape
def genres(item):
    action = 'movies'
    data = get_data(item)
    patronBlock = r'dropdown[^>]*>\s*Generi\s*<span.[^>]+>(?P<block>.*?)</ul>'
    patronGenreMenu = r'<input.*?name="(?P<name>[^"]+)" value="(?P<value>[^"]+)"\s*>[^>]+>(?P<title>[^<]+)</label>'

    def itemHook(item):
        item.url = host + '/filter?' + item.name + '=' + item.value + '&sort='
        return item
    return locals()


@support.scrape
def menu(item):
    action = 'submenu'
    data = get_data(item)
    patronMenu = r'<button[^>]+>\s*(?P<title>[A-Za-z0-9]+)\s*<span.[^>]+>(?P<other>.*?)</ul>'
    genre = False
    def itemlistHook(itemlist):
        for item in itemlist:
            item.title += ' {anime}'
        itemlist.insert(0, item.clone(title=support.typo('Tutti {anime}','bold'), action='movies'))
        itemlist.append(item.clone(title=support.typo('Cerca... {anime}','bold'), action='search', search=True, thumbnail=support.thumb('search.png')))
        return itemlist
    return locals()


@support.scrape
def submenu(item):
    action = 'movies'
    data = item.other
    patronMenu = r'<input.*?name="(?P<name>[^"]+)" value="(?P<value>[^"]+)"\s*>[^>]+>(?P<title>[^<]+)<\/label>'
    def itemHook(item):
        item.url = host + '/filter?' + item.name + '=' + item.value + '&dub=' + item.args + ('&sort=' if item.name != 'sort' else '')
        return item
    return locals()


def newest(category):
    logger.debug(category)
    item = support.Item()
    try:
        if category == "anime":
            item.url = host + '/updated'
            item.args = "updated"
            return movies(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []


def search(item, texto):
    logger.debug(texto)
    if item.search:
        item.url = host + '/filter?dub=' + item.args + '&keyword=' + texto + '&sort='
    else:
        item.args = 'noorder'
        item.url = host + '/search?keyword=' + texto
    item.contentType = 'tvshow'
    try:
        return movies(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


@support.scrape
def movies(item):
    numerationEnabled = True
    # debug = True
    if item.args not in ['noorder', 'updated'] and not item.url[-1].isdigit(): item.url += order() # usa l'ordinamento di configura canale
    data = get_data(item)

    if item.args == 'updated':
        item.contentType='episode'
        patron=r'<div class="inner">\s*<a href="(?P<url>[^"]+)" class[^>]+>\s*<img.*?src="(?P<thumb>[^"]+)" alt?="(?P<title>[^\("]+)(?:\((?P<lang>[^\)]+)\))?"[^>]+>[^>]+>\s*(?:<div class="[^"]+">(?P<type>[^<]+)</div>)?[^>]+>[^>]+>\s*<div class="ep">[^\d]+(?P<episode>\d+)[^<]*</div>'
        action='findvideos'
    else:
        patron= r'<div class="inner">\s*<a href="(?P<url>[^"]+)" class[^>]+>\s*<img.*?src="(?P<thumb>[^"]+)" alt?="(?P<title>[^\("]+)(?:\((?P<year>\d+)\) )?(?:\((?P<lang>[^\)]+)\))?(?P<title2>[^"]+)?[^>]+>[^>]+>(?:\s*<div class="(?P<l>[^"]+)">[^>]+>)?\s*(?:<div class="[^"]+">(?P<type>[^<]+)</div>)?'
        action='episodes'

    # Controlla la lingua se assente
    patronNext=r'<a href="([^"]+)" class="[^"]+" id="go-next'
    typeContentDict={'movie':['movie', 'special']}
    typeActionDict={'findvideos':['movie', 'special']}
    def itemHook(item):
        if not item.contentLanguage:
            if 'dub=1' in item.url or item.l == 'dub':
                item.contentLanguage = 'ITA'
                # item.title += support.typo(item.contentLanguage,'_ [] color kod')
            else:
                item.contentLanguage = 'Sub-ITA'
                # item.title += support.typo(item.contentLanguage,'_ [] color kod')
        return item
    return locals()


@support.scrape
def episodes(item):
    data = get_data(item)
    numerationEnabled = True
    # pagination = True
    patronBlock= r'<div class="server\s*active\s*"(?P<block>.*?)(?:<div class="server|<link)'
    patron = r'<li[^>]*>\s*<a.*?href="(?P<url>[^"]+)"[^>]*>(?P<episode>[^-<]+)(?:-(?P<episode2>[^<]+))?'
    # def itemHook(item):
    #     item.title = item.fulltitle
    #     return item
    action='findvideos'
    return locals()


def findvideos(item):
    import time
    logger.debug()
    itemlist = []
    urls = []
    # resp = support.match(get_data(item), headers=headers, patron=r'data-name="(\d+)">([^<]+)<')
    resp = support.match(get_data(item), headers=headers, patron=r'data-name="(\d+)">([^<]+)<')
    data = resp.data

    for ID, name in resp.matches:
        # if not item.number: item.number = support.match(item.title, patron=r'(\d+) -').match
        match = support.match(data, patronBlock=r'data-name="{}"[^>]+>(.*?)(?:<div class="(?:server|download)|link)'.format(ID), patron=r'data-id="([^"]+)" data-episode-num="{}".*?href="([^"]+)"'.format(item.contentEpisodeNumber if item.contentEpisodeNumber else 1)).match

        if match:
            epID, epurl = match
            # if 'vvvvid' in name.lower():
            #     urls.append(support.match(host + '/api/episode/ugly/serverPlayerAnimeWorld?id=' + epID, headers=headers, patron=r'<a.*?href="([^"]+)"', debug=True).match)
            if 'animeworld' in name.lower():
                url = support.match(data, patron=r'href="([^"]+)"\s*id="alternativeDownloadLink"', headers=headers).match
                title = support.match(url, patron=r'http[s]?://(?:www.)?([^.]+)', string=True).match
                itemlist.append(item.clone(action="play", title=title, url=url, server='directo'))
            else:
                json = support.match(host + '/api/episode/info?id=' + epID + '&alt=0', headers=headers).response.json
                title = support.match(json['grabber'], patron=r'server\d+.([^.]+)', string=True).match
                if title: itemlist.append(item.clone(action="play", title=title, url=json['grabber'].split('=')[-1], server='directo'))
                else: urls.append(json['grabber'])
    return support.server(item, urls, itemlist)

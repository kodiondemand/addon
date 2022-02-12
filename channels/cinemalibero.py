# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per 'cinemaLibero'
# ------------------------------------------------------------

import re

from core import httptools, support, scrapertools
from core.item import Item
from core.support import typo
from platformcode import config
import sys
if sys.version_info[0] >= 3:
    from concurrent import futures
else:
    from concurrent_py2 import futures

# rimanda a .today che contiene tutti link a .plus
# def findhost(url):
#     permUrl = httptools.downloadpage('https://www.cinemalibero.online/', follow_redirects=False).headers
#     try:
#         import urlparse
#     except:
#         import urllib.parse as urlparse
#     p = list(urlparse.urlparse(permUrl['location'].replace('https://www.google.com/search?q=site:', '')))
#     if not p[0]:
#         p[0] = 'https'
#     return urlparse.urlunparse(p)

host = config.get_channel_url()
headers = [['Referer', host]]

@support.menu
def mainlist(item):

    film = ['/category/film/',
            ('Novità', ['', 'peliculas', 'update']),
            ('Generi', ['', 'genres'])]

    tvshow = ['/category/serie-tv/']

    anime = ['/category/anime-giapponesi/']

##    Sport = [(support.typo('Sport', 'bullet bold'), ['/category/sport/', 'peliculas', 'sport', 'tvshow'])]
    news = [('Ultimi episodi Serie/Anime', ['/aggiornamenti-serie-tv/', 'peliculas', 'update', 'tvshow'])]

    search = ''

    return locals()


@support.scrape
def peliculas(item):
    # debug = True
    action = 'check'
    patronBlock = r'<div class="container">.*?class="col-md-12[^"]*?">(?P<block>.*?)<div class=(?:"container"|"bg-dark ")>'
    if item.args == 'newest':
        patron = r'<div class="col-lg-3">[^>]+>[^>]+>\s<a href="(?P<url>[^"]+)".+?url\((?P<thumb>[^\)]+)\)">[^>]+>(?P<title>[^<]+)<[^>]+>[^>]+>(?:[^>]+>)?\s?(?P<rating>[\d\.]+)?[^>]+>.+?(?:[ ]\((?P<year>\d{4})\))?<[^>]+>[^>]+>(.?[\d\-x]+\s\(?(?P<lang>[sSuUbBiItTaA\-]+)?\)?\s?(?P<quality>[\w]+)?[|]?\s?(?:[fFiInNeE]+)?\s?\(?(?P<lang2>[sSuUbBiItTaA\-]+)?\)?)?'
        pagination = 25
    elif item.contentType == 'movie':
        # action = 'findvideos'
        patron = r'<a href="(?P<url>[^"]+)" title="(?P<title>.+?)(?:[ ]\[(?P<lang>[sSuUbB\-iItTaA]+)\])?(?:[ ]\((?P<year>\d{4})?\))?"\s*alt="[^"]+"\s*class="[^"]+"(?: style="background-image: url\((?P<thumb>.+?)\)">)?\s*<div class="voto">[^>]+>[^>]+>.(?P<rating>[\d\.a-zA-Z\/]+)?[^>]+>[^>]+>[^>]+>(?:<div class="genere">(?P<quality>[^<]+)</div>)?'
        if item.args == 'update':
            patronBlock = r'<section id="slider">(?P<block>.*?)</section>'
            patron = r'<a href="(?P<url>(?:https:\/\/.+?\/(?P<title>[^\/]+[a-zA-Z0-9\-]+)(?P<year>\d{4})?))/".+?url\((?P<thumb>[^\)]+)\)">'
    elif item.contentType == 'tvshow':
        # action = 'episodios'
        if item.args == 'update':
            patron = r'<a href="(?P<url>[^"]+)"[^<]+?url\((?P<thumb>.+?)\)">\s*?<div class="titolo">(?P<title>.+?)(?: &#8211; Serie TV)?(?:\([sSuUbBiItTaA\-]+\))?[ ]?(?P<year>\d{4})?</div>\s*?(?:<div class="genere">)?(?:[\w]+?\.?\s?[\s|S]?[\dx\-S]+?\s\(?(?P<lang>[iItTaA]+|[sSuUbBiItTaA\-]+)\)?\s?(?P<quality>[HD]+)?|.+?\(?(?P<lang2>[sSuUbBiItTaA\-]+)?\)?</div>)'
            pagination = 25
        else:
            patron = r'<a href="(?P<url>[^"]+)"\s*title="(?P<title>[^"\(]+)(?:"|\()(?:(?P<year>\d+)[^"]+)?.*?url\((?P<thumb>[^\)]+)\)(?:.*?<div class="voto">[^>]+>[^>]+>\s*(?P<rating>[^<]+))?.*?<div class="titolo">[^>]+>(?:<div class="genere">[^ ]*(?:\s\d+)?\s*(?:\()?(?P<lang>[^\)< ]+))?'
    else:
        patron = r'<div class="col-lg-3">[^>]+>[^>]+>\s*<a href="(?P<url>[^"]+)".+?url\((?P<thumb>[^\)]+)\)">[^>]+>[^>]+>[^>]+>(?:[^>]+>)?\s?(?P<rating>[\d\.]+)?[^>]+>(?P<title>.+?)(?:[ ]\((?P<year>\d{4})\))?<[^>]+>[^>]+>(.?[\d\-x]+\s\(?(?P<lang>[sSuUbBiItTaA\-]+)?\)?\s?(?P<quality>[\w]+)?[|]?\s?(?:[fFiInNeE]+)?\s?\(?(?P<lang2>[sSuUbBiItTaA\-]+)?\)?)?'

    def itemHook(item):
        if 'sub' in item.contentLanguage.lower() and not 'ita' in item.contentLanguage.lower():
            item.contentLanguage= 'Sub-ITA'
            item.title = re.sub('[Ss]ub(?:-)?', item.contentLanguage, item.title)
        if item.lang2:
            if len(item.lang2)<3:
                item.lang2 = 'ITA'
            item.contentLanguage = item.lang2
            item.title += support.typo(item.lang2, '_ [] color kod')
        if item.args == 'update':
            item.title = item.title.replace('-', ' ')
        # if item.args == 'search':
        #     item.contentType = 'tvshow' if 'serie-' in item.url else 'movie'

        return item

    patronNext = r'<a class="next page-numbers".*?href="([^"]+)">'
    return locals()

@support.scrape
def episodios(item):
    data = item.data
    # debugBlock = True
    if item.args == 'anime':
        support.info("Anime :", item)
        # blacklist = ['Clipwatching', 'Verystream', 'Easybytez', 'Flix555', 'Cloudvideo']
        patron = r'<a target=(?P<url>[^>]+>(?P<title>Episodio\s(?P<episode>\d+))(?::)?(?:(?P<title2>[^<]+))?.*?(?:<br|</p))'
        patronBlock = r'(?:Stagione (?P<season>\d+))?(?:</span><br />|</span></p>|strong></p>)(?P<block>.*?)(?:<div style="margin-left|<span class="txt_dow">)'
        item.contentType = 'tvshow'
    elif item.args == 'serie' or item.contentType == 'tvshow':
        support.info("Serie :", item)
        patron = r'(?:>| )(?P<episode>\d+(?:x|×|&#215;)\d+|Puntata \d+)[;]?[ ]?(?:(?P<title>[^<–-]+)?(?P<data>.*?)|(\2[ ])(?:<(\3.*?)))(?:</a><br /|</a></p|$)|(?P<stagione>.+)'
        patronBlock = r'>(?:[^<]+[Ss]tagione\s|[Ss]tagione [Uu]nica)(?:(?P<lang>iTA|ITA|Sub-ITA|Sub-iTA))?.*?</strong>(?P<block>.+?)(?:<strong|<div class="at-below)'
        item.contentType = 'tvshow'
    else:
        patron = r'(?P<title>\s*[0-9]{2}/[0-9]{2}/[0-9]{4})(?P<data>.*?)(?:<br|</p)'

    def itemHook(it):
        if not scrapertools.find_single_match(it.title, r'(\d+x\d+)'):
            it.title = re.sub(r'(\d+) -', '1x\\1', it.title)
        return it

    def itemlistHook(itl):
        ret = []
        for it in itl:
            if it.stagione:  # stagione intera
                def get_ep(s):
                    srv_mod = __import__('servers.%s' % s.server, None, None, ["servers.%s" % s.server])
                    if hasattr(srv_mod, 'get_filename'):
                        title = srv_mod.get_filename(s.url)
                        ep = scrapertools.get_season_and_episode(title)
                        if ep:
                            if ep not in episodes:
                                episodes[ep] = []
                            episodes[ep].append(s)
                servers = support.server(item, it.stagione, AutoPlay=False, CheckLinks=False, Download=False, Videolibrary=False)
                episodes = {}

                # ottengo l'episodio dal nome del file
                with futures.ThreadPoolExecutor() as executor:
                    for s in servers:
                        executor.submit(get_ep, s)
                ret.extend([it.clone(title=ep+typo(it.contentLanguage, '_ [] color kod'), contentSeason=int(ep.split('x')[0]), contentEpisodeNumber=int(ep.split('x')[1]), servers=[srv.tourl() for srv in episodes[ep]]) for ep in episodes])
            else:
                ret.append(it)
        return sorted(ret, key=lambda i: i.title)

    return locals()


@support.scrape
def genres(item):
    action='peliculas'
    patron_block=r'<div id="bordobar" class="dropdown-menu(?P<block>.*?)</li>'
    patronMenu=r'<a class="dropdown-item" href="(?P<url>[^"]+)" title="(?P<title>[A-z]+)"'

    return locals()


def search(item, texto):
    support.info(item.url,texto)
    texto = texto.replace(' ', '+')
    item.url = host + "/?s=" + texto
    # item.contentType = 'tv'
    item.args = 'search'
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.info("%s" % line)
    return []


def newest(categoria):
    support.info('newest ->', categoria)
    itemlist = []
    item = Item()
    item.args = 'newest'
    try:
        if categoria == 'series' or categoria == 'anime':
            item.args = 'update'
            item.url = host+'/aggiornamenti-serie-tv/'
            item.contentType = 'tvshow'
        item.action = 'peliculas'
        itemlist = peliculas(item)
    except:
        import sys
        for line in sys.exc_info():
            support.info('newest log: ', (line))
        return []

    return itemlist


def check(item):
    support.info()
    data = support.match(item.url, headers=headers).data
    if data:
        ck = support.match(data, patron=r'Supportaci condividendo quest[oa] ([^:]+)').match.lower()

        if ck == 'serie tv':
            item.contentType = 'tvshow'
            item.args = 'serie'
            item.data = data
            return episodios(item)

        elif ck == 'anime':
            item.contentType = 'tvshow'
            item.args = 'anime'
            item.data = data
            itemlist = episodios(item)
            if not itemlist:
                item.data = data
                item.action = 'findvideos'
                return findvideos(item)

        elif ck == 'film':
            item.contentType = 'movie'
            item.data = data
            item.action = 'findvideos'
            return findvideos(item)

        else:
            item.contentType = 'tvshow'
            item.data = data
            itemlist = episodios(item)
            if not itemlist:
                item.contentType = 'movie'
                item.data = data
                item.action = 'findvideos'
                return findvideos(item)



def findvideos(item):
    def filter_ep(s):
        srv_mod = __import__('servers.%s' % s.server, None, None, ["servers.%s" % s.server])
        if hasattr(srv_mod, 'get_filename'):
            title = srv_mod.get_filename(s.url)
            # support.dbg()
            if scrapertools.get_season_and_episode(title) == str(item.contentSeason) + "x" + str(
                    item.contentEpisodeNumber).zfill(2):
                servers.append(s)
    support.info()
    if item.servers:
        return support.server(item, itemlist=[Item().fromurl(s) for s in item.servers])
    if not item.data:
        item.data = httptools.downloadpage(item.url)
    item.data = scrapertools.find_single_match(item.data, '<div class="at-above-post addthis_tool"(.*?)<div class="at-below-post')

    servers = []
    if item.args == 'anime':
        if item.urls:  # this is a episode
            return support.server(item, itemlist=[Item(url=support.unshortenit.FileCrypt().unshorten(u)) for u in item.urls])
        itemlist = []
        episodes = {}
        # support.dbg()
        for uri in support.unshortenit.FileCrypt().find(item.data):
            for ep in support.unshortenit.FileCrypt(uri).list_files():
                ep = ('.'.join(ep[0].split('.')[:-1]), ep[1])  # remove extension
                if not ep[0] in episodes:
                    episodes[ep[0]] = []
                episodes[ep[0]].append(ep[1])
        for ep in episodes.keys():
            itemlist.append(item.clone(title=ep, urls=episodes[ep], action='findvideos', data=''))
        return itemlist
    total_servers = support.server(item, data=item.data)

    if item.contentType == 'episode' and len(set([srv.server for srv in total_servers])) < len([srv.server for srv in total_servers]):
        # i link contengono più puntate, cerco quindi quella selezionata
        with futures.ThreadPoolExecutor() as executor:
            for s in total_servers:
                if s.server:
                    executor.submit(filter_ep, s)
                else:
                    servers.append(s)
        return servers
    else:
        return total_servers

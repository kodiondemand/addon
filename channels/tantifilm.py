# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Tantifilm
# ------------------------------------------------------------

from core import scrapertools, httptools, support
from core.item import Item
from core.support import info
from platformcode import logger
from platformcode import config


# def findhost(url):
#     permUrl = httptools.downloadpage(url).data
#     host = scrapertools.find_single_match(permUrl, r'<a href="([^"]+)')
#     return host


host = config.get_channel_url()
headers = [['Referer', host]]

player_iframe = r'<iframe.*?src="([^"]+)"[^>]+></iframe>\s*<div class="player'

@support.menu
def mainlist(item):
    info()

    top = [('Generi', ['', 'category'])]
    film = ['/film',
        ('Al Cinema', ['/watch-genre/al-cinema/']),
        ('HD', ['/watch-genre/altadefinizione/']),
        ('Sub-ITA', ['/watch-genre/sub-ita/'])

        ]

    tvshow = ['/serie-tv/',
        ('HD', ['/watch-genre/serie-altadefinizione/']),
        ('Miniserie', ['/watch-genre/miniserie-1/']),
        ('Programmi TV', ['/watch-genre/programmi-tv/']),
        #('LIVE', ['/watch-genre/live/'])
        ]

    anime = ['/watch-genre/anime/'
        ]

    search = ''
    return locals()

@support.scrape
def peliculas(item):
    # debug = True
    if item.args == 'search':
        patron = r'<a href="(?P<url>[^"]+)" title="Permalink to\s*(?P<title>[^"]+) \((?P<year>[0-9]+)[^<]*\)[^"]*"[^>]+>\s*<img[^s]+src="(?P<thumb>[^"]+)".*?<div class="calitate">\s*<p>(?P<quality>[^<]+)<\/p>'
    else:
        patronNext = r'<a class="nextpostslink" rel="next" href="([^"]+)">'
        patron = r'<div class="mediaWrap mediaWrapAlt">\s*<a href="(?P<url>[^"]+)"(?:[^>]+)?>?\s*(?:<img[^s]+src="(?P<thumb>[^"]+)"[^>]+>\s*)?<\/a>[^>]+>[^>]+>[^>]+>(?P<title>[^<]+?)(?P<lang>[sS][uU][bB]\-[iI][tT][aA]+)?(?:[ ]?\((?P<year>\d{4})-?(?:\d{4})?)\).[^<]+[^>]+><\/a>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s*(?P<quality>[a-zA-Z-0-9\.]+)?'
        patronBlock = r'<div id="main_col">(?P<block>.*?)<!\-\- main_col \-\->'

    # if item.args != 'all' and item.args != 'search':
    #     action = 'findvideos' if item.extra == 'movie' else 'episodios'
    #     item.contentType = 'movie' if item.extra == 'movie' else 'tvshow'
    # debug = True
    return locals()



@support.scrape
def episodios(item):
    def get_season(pageData, seas_url, season):
        data = ''
        episodes = support.match(pageData if pageData else seas_url, patronBlock=patron_episode, patron=patron_option).matches
        for episode_url, episode in episodes:
            title = season + "x" + episode.zfill(2) + ' - ' + item.fulltitle
            data += title + '|' + episode_url + '\n'
        return data

    patron_season = 'Stagioni<\/a>.*?<ul class="nav navbar-nav">(.*?)<\/ul>'
    patron_episode = 'Episodio<\/a>.*?<ul class="nav navbar-nav">(?P<block>.*?)<\/ul>'
    patron_option = r'<a href="([^"]+?)".*?>[^>]+></i>\s*(\d+)'

    url = support.match(item, patron=player_iframe).match
    seasons = support.match(url, patronBlock=patron_season, patron=patron_option)

    data = ''

    import sys
    if sys.version_info[0] >= 3: from concurrent import futures
    else: from concurrent_py2 import futures
    with futures.ThreadPoolExecutor() as executor:
        thL = []
        for i, season in enumerate(seasons.matches):
            thL.append(executor.submit(get_season, seasons.data if i == 0 else '', season[0], season[1]))
        for res in futures.as_completed(thL):
            if res.result():
                data += res.result()
    patron = r'(?P<season>\d+)x(?P<episode>\d+)\s*-\s*(?P<title>[^\|]+)\|(?P<url>[^ ]+)'
    action = 'findvideos'

    def itemlistHook(itemlist):
        itemlist.sort(key=lambda item: (item.infoLabels['season'], item.infoLabels['episode']))
        return itemlist

    return locals()


@support.scrape
def category(item):
    blacklist = ['Ultimi Film Aggiornati', 'Anime', 'Serie TV Altadefinizione', 'HD AltaDefinizione', 'Al Cinema', 'Serie TV', 'Miniserie', 'Programmi Tv', 'Live', 'Trailers', 'Serie TV Aggiornate', 'Aggiornamenti', 'Featured']
    patron = '<li><a href="(?P<url>[^"]+)"><span></span>(?P<title>[^<]+)</a></li>'
    patron_block = '<ul class="table-list">(.*?)</ul>'
    action = 'peliculas'

    return locals()


def search(item, texto):
    info(texto)


    item.url = host + "/?s=" + texto
    try:
        item.args = 'search'
        return peliculas(item)

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


@support.scrape
def newest(categoria):
    if categoria == 'series':
        item = Item(url=host + '/aggiornamenti-giornalieri-serie-tv')
        data = support.match(item).data.replace('<u>','').replace('</u>','')
        item.contentType = 'episode'
        patronBlock = r'Aggiornamenti Giornalieri Serie TV.*?<div class="sp-body folded">(?P<block>.*?)</div>'
        patron = r'<p>(?P<title>.*?)\((?P<year>[0-9]{4})[^\)]*\)[^<]+<a href="(?P<url>[^"]+)">(?P<episode>[^ ]+) (?P<lang>[Ss][Uu][Bb].[Ii][Tt][Aa])?(?P<title2>[^<]+)?'

    return locals()


@support.scrape
def hdpass(item):
    patronBlock = r'<ul class="nav navbar-nav">(?P<block>.*?)</ul>'
    patron = r'<a.*?href="(?P<url>[^"]+)">'

    def itemHook(item):
        url = support.match(item.url, patron='<iframe.*?src="([^"]+)').match
        return Item(url=url)

    return locals()


def findvideos(item):
    info()
    support.info("ITEMLIST: ", item)
    data = support.match(item.url, headers=headers).data
    check = support.match(data, patron=r'<div class="category-film">(.*?)</div>').match
    if 'sub' in check.lower():
        item.contentLanguage = 'Sub-ITA'
    support.info("CHECK : ", check)
    if 'anime' in check.lower():
        item.contentType = 'tvshow'
        item.data = data
        support.info('select = ### è una anime ###')
        try:
            return episodios(item)
        except:
            pass
    elif 'serie' in check.lower():
        item.contentType = 'tvshow'
        item.data = data
        return episodios(item)
    else:
        item.contentTitle = item.fulltitle
        item.contentType = 'movie'

    # if 'protectlink' in data:
    #     urls = scrapertools.find_multiple_matches(data, r'<iframe src="[^=]+=(.*?)"')
    #     support.info("SONO QUI: ", urls)
    #     for url in urls:
    #         url = url.decode('base64')
    #         # tiro via l'ultimo carattere perchè non c'entra
    #         url, c = unshorten_only(url)
    #         if 'nodmca' in url:
    #             page = httptools.downloadpage(url, headers=headers).data
    #             url = '\t' + scrapertools.find_single_match(page, '<meta name="og:url" content="([^=]+)">')
    #         if url:
    #             listurl.add(url)
    # data += '\n'.join(listurl)
    info(data)
    itemlist = []
    # support.dbg()

    if '/serietv/series/names' in item.url:
        itemlist.extend(support.server(item, itemlist=hdpass(Item(url=item.url))))
    else:
        urls = support.match(data, patron=player_iframe).matches
        # support.dbg()
        if item.otherLinks:
            urls += support.match(item.otherLinks, patron=r'href="([^"]+)').matches

        info('URLS', urls)
        for u in urls:
            if 'hdplayer.casa/series/' in u:
                urls.remove(u)
                itemlist.extend(support.server(item, itemlist=hdpass(Item(url=u))))
                break
            if 'protectlink.stream' in u:
                import base64
                urls.remove(u)
                urls.append(base64.b64decode(u.split('?data=')[1]))
        else:
            itemlist.extend(support.server(item, urls))
        support.addQualityTag(item, itemlist, data, 'Keywords:\s*(?:<span>)?([^<]+)')
    return itemlist

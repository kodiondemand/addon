# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Tantifilm
# ------------------------------------------------------------

from core import support
from core.item import Item
from platformcode import logger
from platformcode import config


host = config.get_channel_url()
headers = [['Referer', host]]

player_iframe = r'<iframe.*?src="([^"]+)"[^>]+></iframe>\s*<div class="player'

@support.menu
def mainlist(item):
    logger.debug()

    top = [('Generi', ['', 'genres'])]

    film = ['/film',
            ('Al Cinema', ['/watch-genre/al-cinema/']),
            ('HD', ['/watch-genre/altadefinizione/']),
            ('Sub-ITA', ['/watch-genre/sub-ita/'])]

    tvshow = ['/serie-tv/',
        ('HD', ['/watch-genre/serie-altadefinizione/']),
        ('Miniserie', ['/watch-genre/miniserie-1/']),
        ('Programmi TV', ['/watch-genre/programmi-tv/'])]

    anime = ['/watch-genre/anime/']

    search = ''

    return locals()


@support.scrape
def genres(item):

    blacklist = ['Ultimi Film Aggiornati', 'Anime', 'Serie TV Altadefinizione', 'HD AltaDefinizione', 'Al Cinema', 'Serie TV', 'Miniserie', 'Programmi Tv', 'Live', 'Trailers', 'Serie TV Aggiornate', 'Aggiornamenti', 'Featured']
    patronMenu = '<li><a href="(?P<url>[^"]+)"><span></span>(?P<title>[^<]+)</a></li>'
    patron_block = '<ul class="table-list">(.*?)</ul>'
    action = 'peliculas'

    return locals()


def search(item, texto):
    logger.debug(texto)

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
        item = Item(url=host + '/aggiornamenti-serie-tv')
        data = support.match(item).data.replace('<u>','').replace('</u>','')
        item.contentType = 'episode'
        patronBlock = r'Aggiornamenti (?:Giornalieri )?Serie TV.*?<div class="sp-body folded">(?P<block>.*?)</div>'
        patron = r'<p>(?P<title>.*?)\((?P<year>[0-9]{4})[^\)]*\)[^<]+<a href="(?P<url>[^"]+)">(?P<episode>[^ ]+) (?P<lang>[Ss][Uu][Bb].[Ii][Tt][Aa])?(?P<title2>[^<]+)?'
    return locals()


@support.scrape
def peliculas(item):
    action = 'check'
    item.contentType = 'undefined'
    if item.args == 'search':
        patron = r'<a href="(?P<url>[^"]+)" title="Permalink to\s*(?P<title>[^"]+) \((?P<year>[0-9]+)[^<]*\)[^"]*"[^>]+>\s*<img[^s]+src="(?P<thumb>[^"]+)".*?<div class="calitate">\s*<p>(?P<quality>[^<]+)<\/p>'
    else:
        patronNext = r'<a class="nextpostslink" rel="next" href="([^"]+)">'
        patron = r'<div class="mediaWrap mediaWrapAlt">\s*<a href="(?P<url>[^"]+)"(?:[^>]+)?>?\s*(?:<img[^s]+src="(?P<thumb>[^"]+)"[^>]+>\s*)?<\/a>[^>]+>[^>]+>[^>]+>(?P<title>[^<]+?)(?P<lang>[sS][uU][bB]\-[iI][tT][aA]+)?(?:[ ]?\((?P<year>\d{4})-?(?:\d{4})?)\).[^<]+[^>]+><\/a>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s*(?P<quality>[a-zA-Z-0-9\.]+)?'
        patronBlock = r'<div id="main_col">(?P<block>.*?)<!\-\- main_col \-\->'

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

    if item.data:
        url = support.match(item.data, patron=player_iframe).match
        item.data = ''
    else:
        url = support.match(item, patron=player_iframe).match
    seasons = support.match(url, patronBlock=patron_season, patron=patron_option)

    data = ''

    import sys
    if sys.version_info[0] >= 3: from concurrent import futures
    else: from concurrent_py2 import futures
    with futures.ThreadPoolExecutor() as executor:
        thL = []
        for i, season in enumerate(seasons.matches):
            thL.append(executor.submit(get_season, '', season[0], season[1]))
        for res in futures.as_completed(thL):
            if res.result():
                data += res.result()
    patron = r'(?P<season>\d+)x(?P<episode>\d+)\s*-\s*(?P<title>[^\|]+)\|(?P<url>[^ ]+)'
    # debug = True
    action = 'findvideos'

    def itemlistHook(itemlist):
        itemlist.sort(key=lambda item: (item.infoLabels['season'], item.infoLabels['episode']))
        return itemlist

    return locals()


def check(item):
    item.data = support.match(item.url, headers=headers).data
    check = support.match(item.data, patron=r'<div class="category-film">(.*?)</div>').match
    if 'sub' in check.lower():
        item.contentLanguage = 'Sub-ITA'
    logger.debug("CHECK : ", check)
    # if 'anime' in check.lower():
    #     item.contentType = 'tvshow'
    #     logger.debug('select = ### è una anime ###')
    #     try:
    #         return episodios(item)
    #     except:
    #         pass
    if 'serie' in check.lower():
        item.contentType = 'tvshow'
        return episodios(item)
    else:
        item.contentTitle = item.fulltitle
        item.contentType = 'movie'
        return findvideos(item)


def findvideos(item):
    logger.debug()
    data = item.data if item.data else support.match(item.url, headers=headers).data
    itemlist = []

    if '/serietv/series/names' in item.url:
        itemlist.extend(support.server(item, itemlist=hdpass(Item(url=item.url))))
    else:
        urls = support.match(data, patron=player_iframe).matches
        if item.otherLinks:
            urls += support.match(item.otherLinks, patron=r'href="([^"]+)').matches

        logger.debug('URLS', urls)
        for u in urls:
            if 'hdplayer.casa/series/' in u:
                urls.remove(u)
                itemlist.extend(support.server(item, itemlist=hdpass(Item(url=u))))
                break
        else:
            itemlist.extend(support.server(item, urls))
        support.addQualityTag(item, itemlist, data, 'Keywords:\s*(?:<span>)?([^<]+)')
    return itemlist


@support.scrape
def hdpass(item):
    patronBlock = r'<ul class="nav navbar-nav">(?P<block>.*?)</ul>'
    patron = r'<a.*?href="(?P<url>[^"]+)">'

    def itemHook(item):
        url = support.match(item.url, patron='<iframe.*?src="([^"]+)').match
        return Item(url=url)

    return locals()
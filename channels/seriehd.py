# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per seriehd
# ------------------------------------------------------------
import urlparse
import re

from channelselector import thumb
from lib import cloudscraper
from core import scrapertoolsV2, servertools, httptools, support
from core.item import Item
from core.support import menu, log
from platformcode import logger, config
from specials import autoplay

host = "https://www.seriehd.zone"

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['verystream', 'openload', 'streamango', 'thevideome']
list_quality = ['1080p', '720p', '480p', '360']

checklinks = config.get_setting('checklinks', 'seriehd')
checklinks_number = config.get_setting('checklinks_number', 'seriehd')

headers = [['Referer', host]]


def mainlist(item):
    log()
    itemlist = []

    menu(itemlist, 'Serie TV', 'peliculas', host + '/serie-tv-streaming', 'tvshow')
    menu(itemlist, 'Per Genere submenu', 'genre', host, 'tvshow', 'TV')
    menu(itemlist, 'Per Nazione submenu', 'nation', host + '/serie-tv-streaming/', 'tvshow', 'TV')
    menu(itemlist, 'Cerca...', 'search', contentType='tvshow', args='TV')

    autoplay.init(item.channel, list_servers, list_quality)
    autoplay.show_option(item.channel, itemlist)

    return itemlist


def search(item, texto):
    log(texto)

    item.url = host + "/?s=" + texto

    try:
        return peliculas(item)

    # Continua la ricerca in caso di errore .
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    log(categoria)
    itemlist = []
    item = Item()
    try:

        ## cambiar los valores "peliculas, infantiles, series, anime, documentales por los que correspondan aqui en
        # el py y en l json ###
        if categoria == "series":
            item.url = host
            itemlist = peliculas(item)

            if 'Successivo>>' in itemlist[-1].title:
                itemlist.pop()

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def genre(item):
    itemlist = support.scrape(item, '<a href="([^"]+)">([^<]+)</a>', ['url', 'title'], headers,['Serie TV','Serie TV Americane','Serie TV Italiane','altadefinizione'], action='peliculas')
    return thumb(itemlist)


def nation(item):
    log()
    itemlist = []
    menu(itemlist, 'Serie TV Americane', 'peliculas', host + '/serie-tv-streaming/serie-tv-americane/')
    menu(itemlist, 'Serie TV Italiane', 'peliculas', host + '/serie-tv-streaming/serie-tv-italiane/')
    return itemlist


def peliculas(item):
    item.contentType = 'tvshow'
    return support.scrape(item,r'<h2>(.*?)</h2>\s*<img src="([^"]+)" alt="[^"]*" />\s*<A HREF="([^"]+)">.*?<span class="year">([0-9]{4}).*?<span class="calidad">([A-Z]+)',['title', 'thumb', 'url', 'year', 'quality'], headers, patronNext=r"<span class='current'>\d+</span><a rel='nofollow' class='page larger' href='([^']+)'>\d+</a>", action='episodios')


def episodios(item):
    log()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    patron = r'<iframe width=".+?" height=".+?" src="([^"]+)" allowfullscreen frameborder="0">'
    url = scrapertoolsV2.find_single_match(data, patron).replace("?seriehd", "")
    seasons = support.match(item, r'<a href="([^"]+)">(\d+)<', r'<h3>STAGIONE</h3><ul>(.*?)</ul>', headers, url)[0]
    for season_url, season in seasons:
        season_url = urlparse.urljoin(url, season_url)
        episodes = support.match(item, r'<a href="([^"]+)">(\d+)<', '<h3>EPISODIO</h3><ul>(.*?)</ul>', headers, season_url)[0]
        for episode_url, episode in episodes:
            episode_url = urlparse.urljoin(url, episode_url)
            title = season + "x" + episode.zfill(2)

            itemlist.append(
                Item(channel=item.channel,
                     action="findvideos",
                     contentType="episode",
                     title=support.typo(title + ' - ' +item.show,'bold'),
                     url=episode_url,
                     fulltitle=title + ' - ' + item.show,
                     show=item.show,
                     thumbnail=item.thumbnail))

    support.videolibrary(itemlist, item, 'color kod bold')

    return itemlist


def findvideos(item):
    log()

    itemlist = []
    itemlist = support.hdpass_get_servers(item)

    if checklinks:
        itemlist = servertools.check_list_links(itemlist, checklinks_number)

    autoplay.start(itemlist, item)

    return itemlist




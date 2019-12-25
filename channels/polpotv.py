# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# KoD - XBMC Plugin
# Canale polpotv
# ------------------------------------------------------------

from core import scrapertools, httptools, support, jsontools
from core.item import Item
from platformcode import config
import json, datetime

__channel__ = "polpotv"
host = config.get_channel_url(__channel__)

headers = [['Accept', 'application/ld+json']]

list_servers = ['directo']
list_quality = ['1080p','720p','480p','360p']

@support.menu
def mainlist(item):
    menu = [
        ('Ultimi Film aggiunti', ['/api/movies', 'peliculas', '']),
        ('Generi', ['/api/genres', 'search_movie_by_genre', '']),
        ('Anni {film}', ['', 'search_movie_by_year', '']),
        ('Cerca Film... bold', ['', 'search', ''])
    ]
    return locals()

def newest(categoria):
    support.log()
    item = Item()
    if categoria == 'peliculas':
        item.contentType = 'movie'
        item.url = host + '/api/movies'
    return peliculas(item)

def peliculas(item):
    support.log()
    itemlist = []
    data = httptools.downloadpage(item.url, headers=headers).data
    json_object = jsontools.load(data)

    for movie in json_object['hydra:member']:
        itemlist.extend(get_itemlist_movie(movie,item))

    try:
        if support.inspect.stack()[1][3] not in ['newest']:
            support.nextPage(itemlist, item, next_page=json_object['hydra:view']['hydra:next'])
    except:
        pass

    return itemlist

def search(item, texto):
    support.log(item.url, "search", texto)
    itemlist=[]
    try:
        item.url = host + "/api/movies?originalTitle="+texto+"&translations.name=" +texto
        data = httptools.downloadpage(item.url, headers=headers).data
        json_object = jsontools.load(data)
        for movie in json_object['hydra:member']:
            itemlist.extend(get_itemlist_movie(movie,item))
        return itemlist
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
        return []

def search_movie_by_genre(item):
    support.log()
    itemlist = []
    data = httptools.downloadpage(item.url, headers=headers).data
    json_object = jsontools.load(data)
    for genre in json_object['hydra:member']:
        itemlist.append(
            Item(channel=item.channel,
             action="peliculas",
             title=support.typo(genre['name'],'bold'),
             contentType='movie',
             url="%s/api/movies?genres.id=%s" %(host,genre['id']),
             extra=item.extra))
    return support.thumb(itemlist, True)

def search_movie_by_year(item):
    support.log()
    now = datetime.datetime.now()
    year = int(now.year)
    itemlist = []
    for i in range(100):
        year_to_search = year - i
        itemlist.append(Item(channel=item.channel,
                           url="%s/api/movies?releaseDate=%s" %(host,year_to_search),
                           plot="1",
                           type="movie",
                           title=support.typo(year_to_search,'bold'),
                           action="peliculas"))
    return itemlist

def findvideos(item):
    support.log()
    itemlist = []
    try:
        data = httptools.downloadpage(item.url, headers=headers).data
        json_object = jsontools.load(data)
        for video in json_object['hydra:member'][0]['playlist']['videos']:
            # data = httptools.downloadpage(video['src'], headers={'Origin': host},follow_redirects=None).data
            # patron = 'href="([^"]+)"'
            # video_link = scrapertools.find_single_match(data, patron)
            itemlist.append(
                Item(
                    channel=item.channel,
                    action="play",
                    thumbnail=item.thumbnail,
                    url=video['src'],
                    server='directo',
                    quality=str(video['size'])+ 'p',
                    folder=False))
    except:
        pass
    return support.server(item, itemlist=itemlist)

def get_itemlist_movie(movie,item):
    support.log()
    itemlist=[]
    try:
        if movie['originalLanguage']['id']=='it':
            scrapedtitle=movie['originalTitle']
        else:
            scrapedtitle=movie['translations'][1]['name']
        if scrapedtitle=='':
            scrapedtitle=movie['originalTitle']
    except:
        scrapedtitle=movie['originalTitle']
    try:
        scrapedplot=movie['translations'][1]['overview']
    except:
        scrapedplot = ""
    try:
        scrapedthumbnail="http://"+movie['posterPath']
    except:
        scrapedthumbnail=""
    try:
        scrapedfanart="http://"+movie['backdropPath']
    except:
        scrapedfanart=""
    infoLabels = {}
    infoLabels['tmdbid']=movie['tmdbId']
    itemlist.append(
        Item(channel=item.channel,
             action="findvideos",
             title=support.typo(scrapedtitle,'bold') + support.typo(movie['lastQuality'].upper(), '_ [] color kod bold'),
             fulltitle=scrapedtitle,
             show=scrapedtitle,
             plot=scrapedplot,
             fanart=scrapedfanart,
             thumbnail=scrapedthumbnail,
             contentType='movie',
             contentTitle=scrapedtitle,
             url="%s%s/releases" %(host,movie['@id'] ),
             infoLabels=infoLabels,
             extra=item.extra))
    return itemlist

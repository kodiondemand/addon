# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# KoD - XBMC Plugin
# Canale polpotv
# ------------------------------------------------------------

from core import scrapertools, httptools, support, jsontools
from core.item import Item
from platformcode import config
import json, datetime

host = config.get_channel_url()

headers = [['Accept', 'application/ld+json']]

list_servers = ['directo']
list_quality = ['1080p','720p','480p','360p']

@support.menu
def mainlist(item):
    menu = [
        ('Ultimi Film aggiunti', ['/api/movies', 'peliculas', '']),
        ('Ultime Serie TV aggiunte', ['/api/shows', 'peliculas', '']),
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
    elif categoria == 'series':
        item.contentType = 'tvshow'      
        item.url = host+'/api/shows'
    return peliculas(item)

def peliculas(item):
    support.log()
    itemlist = []
    
    data = httptools.downloadpage(item.url, headers=headers).data
    json_object = jsontools.load(data)
    for element in json_object['hydra:member']:
        if 'shows' not in item.url:
            item.contentType='movie'
        else:
            item.contentType='tvshow'
        itemlist.extend(get_itemlist_element(element,item))

    try:
        if support.inspect.stack()[1][3] not in ['newest']:
            support.nextPage(itemlist, item, next_page=json_object['hydra:view']['hydra:next'])
    except:
        pass

    return itemlist

def episodios(item):
    support.log()
    itemlist = []
    data = httptools.downloadpage(item.url, headers=headers).data
    json_object = jsontools.load(data)
    i=1
    for season in json_object['seasons']:
        item.url=host+season['@id']+'/releases'
        itemlist_season=get_season(item)
        if(len(itemlist_season)>0):
            itemlist.append(
                Item(channel=item.channel,
                 action='',
                 title=support.typo('Stagione '+str(i), '_ [] color kod bold'),
                 url='',
                 extra=season['@id'] ))
            itemlist.extend(itemlist_season)
        i=i+1;

    return itemlist

def get_season(item):
    support.log()
    itemlist = []
    s=item.url
    data = httptools.downloadpage(item.url, headers=headers).data
    json_object = jsontools.load(data)
    for episode in json_object['hydra:member']:
        itemlist.append(
            Item(channel=item.channel,
                 action='findvideos',
                 title="Epsiodio "+str(episode['episodeNumber']),
                 url=item.url,
                 extra=str(len(json_object['hydra:member'])-episode['episodeNumber'])))
    return itemlist[::-1]

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
        array_index=0
        if item.contentType!='movie':
            array_index=int(item.extra)
        for video in json_object['hydra:member'][array_index]['playlist']['videos']:
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

def get_itemlist_element(element,item):
    support.log()
    itemlist=[]
    try:
        if element['originalLanguage']['id']=='it':
            scrapedtitle=element['originalTitle']
        else:
            scrapedtitle=element['translations'][1]['name']
        if scrapedtitle=='':
            scrapedtitle=element['originalTitle']
    except:
        scrapedtitle=element['originalTitle']
    try:
        scrapedplot=element['translations'][1]['overview']
    except:
        scrapedplot = ""
    try:
        scrapedthumbnail="http://"+element['posterPath']
    except:
        scrapedthumbnail=""
    try:
        scrapedfanart="http://"+element['backdropPath']
    except:
        scrapedfanart=""

    infoLabels = {}
    if item.contentType=='movie':
        next_action='findvideos'
        quality=support.typo(element['lastQuality'].upper(), '_ [] color kod bold')
        url="%s%s/releases"
        infoLabels['tmdbid']=element['tmdbId']
    else:
        next_action='episodios'
        quality=''
        url="%s%s"
    itemlist.append(
        Item(channel=item.channel,
             action=next_action,
             title=support.typo(scrapedtitle,'bold') + quality,
             fulltitle=scrapedtitle,
             show=scrapedtitle,
             plot=scrapedplot,
             fanart=scrapedfanart,
             thumbnail=scrapedthumbnail,
             contentType=item.contentType,
             contentTitle=scrapedtitle,
             url=url %(host,element['@id'] ),
             infoLabels=infoLabels,
             extra=item.extra))
    return itemlist

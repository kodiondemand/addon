# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Tantifilm
# ------------------------------------------------------------

import re

import urlparse

from core import scrapertoolsV2, httptools, tmdb, support
from core.item import Item
from core.support import menu, log, aplay
from platformcode import logger
from specials import autorenumber
from platformcode import config

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['verystream', 'openload', 'streamango', 'vidlox', 'youtube']
list_quality = ['default']

__channel__ = "tantifilm"
host = config.get_channel_url(__channel__)

headers = [['Referer', host]]


def mainlist(item):
    log()
    itemlist = []

    menu(itemlist, 'Film', 'peliculas', host + '/film/', 'movie', args='movie')
    menu(itemlist, 'Film Al Cinema submenu', 'peliculas', host + '/watch-genre/al-cinema/', 'movie')    
    menu(itemlist, 'Film HD submenu', 'peliculas', host + '/watch-genre/altadefinizione/', 'movie')
    menu(itemlist, 'Film Per Categoria submenu', 'category', host, 'movie')
    menu(itemlist, 'Cerca film... submenu color kod', 'search', contentType='movie', args='findvideos')
    menu(itemlist, 'Serie TV', 'peliculas', host + '/watch-genre/serie-tv/', contentType='episode')
    menu(itemlist, 'Serie TV HD submenu', 'peliculas', host + '/watch-genre/serie-altadefinizione/', contentType='episode')
    menu(itemlist, 'Miniserie submenu', 'peliculas', host + '/watch-genre/miniserie/', contentType='episode', args='serie')
    menu(itemlist, 'Programmi TV submenu', 'peliculas', host + '/watch-genre/programmi-tv/', contentType='episode')
    menu(itemlist, 'Anime submenu', 'peliculas', host + '/watch-genre/anime/', contentType='episode', args='anime')
    menu(itemlist, 'Cerca Serie TV... submenu color kod', 'search', contentType='episode', args='episodios')
    aplay(item, itemlist, list_servers, list_quality)

    return itemlist


def newest(categoria):
    log()
    itemlist = []
    item = Item()
    item.url = host +'/aggiornamenti/'

    matches = support.match(item, r'mediaWrapAlt recomended_videos"[^>]+>\s*<a href="([^"]+)" title="([^"]+)" rel="bookmark">\s*<img[^s]+src="([^"]+)"[^>]+>')[0]

    for url, title, thumb in matches:
        title = scrapertoolsV2.decodeHtmlentities(title).replace("Permalink to ", "").replace("streaming", "")
        title = re.sub(r'\s\(\d+\)','',title)
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentType="movie",
                 fulltitle=title,
                 show=title,
                 title=support.typo(title, 'bold'),
                 url=url,
                 thumbnail=thumb,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def search(item, texto):
    log(texto)
    item.url = host + "/?s=" + texto

    try:
        return search_peliculas(item)

    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []



def search_peliculas(item):
    log()
    itemlist = []

    action = 'findvideos' if item.extra == 'movie' else 'episodios'

    data = httptools.downloadpage(item.url, headers=headers, ignore_response_code=True).data.replace('\t','').replace('\n','')
    log(data)
    patron = r'<a href="([^"]+)" title="Permalink to\s([^"]+) \(([^<]+)\).*?".*?<img[^s]+src="([^"]+)".*?<div class="calitate">\s*<p>([^<]+)<\/p>'
    matches = re.compile(patron, re.MULTILINE).findall(data)    

    for url, title, year, thumb, quality in matches:
        infoLabels = {}
        infoLabels['year'] = year
        title = scrapertoolsV2.decodeHtmlentities(title)
        quality = scrapertoolsV2.decodeHtmlentities(quality)
        longtitle = title + support.typo(quality,'_ [] color kod')
        itemlist.append(
            Item(channel=item.channel,
                 action=action,
                 contentType=item.contentType,
                 fulltitle=title,
                 show=title,
                 title=longtitle,
                 url=url,
                 thumbnail=thumb,
                 infoLabels=infoLabels,                 
                 args=item.args))
    
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def category(item):
    blacklist = ['Serie TV Altadefinizione', 'HD AltaDefinizione', 'Al Cinema', 'Serie TV', 'Miniserie', 'Programmi Tv', 'Live', 'Trailers', 'Serie TV Aggiornate', 'Aggiornamenti', 'Featured']
    itemlist = support.scrape(item, '<li><a href="([^"]+)"><span></span>([^<]+)</a></li>', ['url', 'title'], headers, blacklist, patron_block='<ul class="table-list">(.*?)</ul>', action='peliculas')
    return support.thumb(itemlist)


def peliculas(item):
    log()
    action = 'findvideos' if item.extra == 'movie' else 'episodios'
    if item.args == 'movie':
        patron= r'<div class="mediaWrap mediaWrapAlt">[^<]+<a href="([^"]+)" title="Permalink to\s([^"]+) \(([^<]+)\).*?"[^>]+>[^<]+<img[^s]+src="([^"]+)"[^>]+>[^<]+<\/a>.*?<p>\s*([a-zA-Z-0-9]+)\s*<\/p>'  
        itemlist = support.scrape(item, patron, ['url', 'title', 'year', 'thumb', 'quality'], headers, action=action, patron_block='<div id="main_col">(.*?)main_col', patronNext='<a class="nextpostslink" rel="next" href="([^"]+)">')
    else:
        patron = r'<div class="media3">[^>]+><a href="([^"]+)"><img[^s]+src="([^"]+)"[^>]+><\/a><[^>]+><a[^<]+><p>([^<]+) \(([^\)]+)[^<]+<\/p>.*?<p>\s*([a-zA-Z-0-9]+)\s*<\/p>'
        itemlist = support.scrape(item, patron, ['url', 'thumb', 'title', 'year', 'quality'], headers, action=action, patronNext='<a class="nextpostslink" rel="next" href="([^"]+)">')
        if item.args == 'anime': autorenumber.renumber(itemlist)
    return itemlist


def episodios(item):
    log()
    itemlist = []
    if item.args == 'anime': return anime(item)

    data = httptools.downloadpage(item.url).data

    # Check if is series
    check = scrapertoolsV2.find_single_match(data.replace('\t','').replace('\n',''), r'<div class="category-film"><h3>([^<]+)<\/h3>')
    if 'serie tv' not in check.lower(): return findvideos(item)
    elif 'anime' in check.lower(): return findvideos(item)

    patron = r'<iframe src="([^"]+)" scrolling="no" frameborder="0" width="626" height="550" allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true">'
    url = scrapertoolsV2.find_single_match(data, patron)
    log('URL =', url)
    seasons = support.match(item, r'<a href="([^"]+)"\s*>\s*<i[^>]+><\/i>\s*(\d+)<\/a>', r'Stagioni<\/a>.*?<ul class="nav navbar-nav">(.*?)<\/ul>', headers=headers, url=url)[0]
    
    for season_url, season in seasons:
        season_url = urlparse.urljoin(url, season_url)
        episodes = support.match(item, r'<a href="([^"]+)"\s*>\s*<i[^>]+><\/i>\s*(\d+)<\/a>', r'Episodio<\/a>.*?<ul class="nav navbar-nav">(.*?)<\/ul>', headers=headers, url=season_url)[0]
        for episode_url, episode in episodes:
            episode_url = urlparse.urljoin(url, episode_url)
            title = season + "x" + episode.zfill(2)

            itemlist.append(
                Item(channel=item.channel,
                     action="findvideos",
                     contentType=item.contentType,
                     title=support.typo(title + ' - ' + item.fulltitle,'bold'),
                     url=episode_url,
                     fulltitle=title + ' - ' + item.show,
                     show=item.show,
                     thumbnail=item.thumbnail))

    support.videolibrary(itemlist, item, 'color kod bold')

    return itemlist

def anime(item):
    log()
    itemlist = []

    seasons = support.match(item, r'<div class="sp-body[^"]+">(.*?)<\/div>')[0]
    for season in seasons:
        episodes = scrapertoolsV2.find_multiple_matches(season, r'<a.*?href="([^"]+)"[^>]+>([^<]+)<\/a>(.*?)<(:?br|\/p)')
        for url, title, urls, none in episodes:
            urls = scrapertoolsV2.find_multiple_matches(urls, '<a.*?href="([^"]+)"[^>]+>')
    
            for url2 in urls:
                url += url2 + '\n'

            log('EP URL',url)
            

            itemlist.append(
                Item(channel=item.channel,
                     action="findvideos",
                     contentType=item.contentType,
                     title=support.typo(title + ' - ' + item.fulltitle,'bold'),
                     url=url,
                     fulltitle=title + ' - ' + item.show,
                     show=item.show,
                     thumbnail=item.thumbnail,
                     args=item.args))

    autorenumber.renumber(itemlist, item,'bold')
    support.videolibrary(itemlist, item, 'color kod bold')

    return itemlist


def findvideos(item):
    log()    
    # itemlist = []

    if item.args == 'anime':
        data = item.url
    else:
        data = httptools.downloadpage(item.url, headers=headers).data

        # Check if is series
        check = scrapertoolsV2.find_single_match(data.replace('\t','').replace('\n',''), r'<div class="category-film"><h3>([^<]+)<\/h3>')
        if 'serie tv' in check.lower(): return episodios(item)
        elif 'anime' in check.lower(): return anime(item)

        if 'protectlink' in data:
            urls = scrapertoolsV2.find_multiple_matches(data, r'<iframe src="[^=]+=(.*?)"')
            for url in urls:
                url= url.decode('base64')
                if '\t' in url:
                    url = url[:-1]
                data += '\t' + url
            if 'nodmca' in data:
                page = httptools.downloadpage(url, headers=headers).data
                data += '\t' + scrapertoolsV2.find_single_match(page,'<meta name="og:url" content="([^=]+)">')
 
    return support.server(item, data, headers=headers)
    # return itemlist

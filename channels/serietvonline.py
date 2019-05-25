# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per serietvonline
# ----------------------------------------------------------
import re

from channelselector import thumb
from core import httptools, scrapertoolsV2, servertools, tmdb, support
from core.item import Item
from lib import unshortenit
from platformcode import logger, config
from specials import autoplay

host = "https://serietvonline.live"
headers = [['Referer', host]]

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['akvideo', 'wstream', 'backin', 'vidto', 'nowvideo']
list_quality = ['default']

PERPAGE = 30

def mainlist(item):
    logger.info(item.channel + 'mainlist')

    itemlist = web_menu()
    support.menu(itemlist, "Cerca Film... color kod", 'search', '', 'movie')
    support.menu(itemlist, "Cerca Serie... color kod", 'search', '', 'episode')

    autoplay.init(item.channel, list_servers, list_quality)
    autoplay.show_option(item.channel, itemlist)
                
    return itemlist


def web_menu():
    itemlist=[]

    data = httptools.downloadpage(host, headers=headers).data
    matches = scrapertoolsV2.find_multiple_matches(data, r'<li class="page_item.*?><a href="([^"]+)">(.*?)<\/a>')
    blacklist = ['DMCA','Contatti','Attenzione NON FARTI OSCURARE']

    for url, title in matches:
        if not title in blacklist:
            title = title.replace('Lista ','') + ' bold'
            if 'film' in title.lower():
                contentType = 'movie'
            else:
                contentType = 'episode'
            support.menu(itemlist, title, 'peliculas', url,contentType=contentType)            

    return itemlist


def search(item, texto):
    logger.info(item.channel + 'search' + texto)

    item.url = host + "/?s= " + texto
    
    return search_peliculas(item)


def search_peliculas(item):
    logger.info(item.channel + 'search_peliculas')

    logger.info('TYPE= ' + item.contentType)

    if item.contentType == 'movie':
        action = 'findvideos'
    else:
        action = 'episodios'

    return support.scrape(item, r'<a href="([^"]+)"><span[^>]+><[^>]+><\/a>[^h]+h2>(.*?)<',
                          ["url", "title"], patronNext="<a rel='nofollow' class=previouspostslink href='([^']+)'",
                          headers=headers, action=action)


def peliculas(item):
    logger.info(item.channel + 'peliculas')
    itemlist = []

    if item.contentType == 'movie':
        action = 'findvideos'
    else:
        action = 'episodios'

    page = 1
    if '{}' in item.url:
        item.url, page = item.url.split('{}')
        page = int(page)

    data = httptools.downloadpage(item.url, headers=headers).data
    block = scrapertoolsV2.find_single_match(data, r'id="lcp_instance_0">(.*?)<\/ul>')
    matches = re.compile(r'<a\s*href="([^"]+)" title="([^<]+)">[^<]+</a>', re.DOTALL).findall(block)

    for i, (url, title) in enumerate(matches):
        if (page - 1) * PERPAGE > i: continue
        if i >= page * PERPAGE: break
        title = scrapertoolsV2.decodeHtmlentities(title)
        itemlist.append(
            Item(channel=item.channel,
                 action=action,
                 title=title,
                 contentTitle=title,
                 fulltitle=title,
                 url=url,
                 contentType=item.contentType,
                 show=title))

    if len(matches) >= page * PERPAGE:
        url = item.url + '{}' + str(page + 1)
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title="[COLOR blue]" + config.get_localized_string(30992) + " >[/COLOR]",
                 url=url,
                 thumbnail=thumb(),
                 contentType=item.contentType))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def episodios(item):
    logger.info(item.channel + 'episodios')
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    block= scrapertoolsV2.find_single_match(data, r'<table>(.*?)<\/table>')

    matches = re.compile(r'<tr><td>(.*?)</td><tr>', re.DOTALL).findall(block)

    for episode in matches:
        episode = "<td class=\"title\">" + episode
        logger.info('EPISODE= ' + episode)
        title = scrapertoolsV2.find_single_match(episode, '<td class="title">(.*?)</td>')
        title = title.replace(item.title, "")
        if scrapertoolsV2.find_single_match(title, '([0-9]+x[0-9]+)'):            
            title = scrapertoolsV2.find_single_match(title, '([0-9]+x[0-9]+)') + ' - ' + re.sub('([0-9]+x[0-9]+)',' -',title)
        elif scrapertoolsV2.find_single_match(title, ' ([0-9][0-9])') and not scrapertoolsV2.find_single_match(title, ' ([0-9][0-9][0-9])'):  
            title = '1x' + scrapertoolsV2.find_single_match(title, ' ([0-9]+)') + ' - ' + re.sub(' ([0-9]+)',' -',title)
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 fulltitle=title,
                 contentType="episode",
                 show=title,
                 title=title,
                 url=episode))

    support.videolibrary(itemlist,item,'bold color kod')

    return itemlist


def findvideos(item):
    logger.info(item.channel + 'findvideos')
    itemlist=[]
    logger.info('TYPE= ' + item.contentType)
    if item.contentType == 'movie':
        data = httptools.downloadpage(item.url, headers=headers).data
        logger.info('DATA= ' + data)
        item.url= scrapertoolsV2.find_single_match(data, r'<table>(.*?)<\/table>')

    urls = scrapertoolsV2.find_multiple_matches(item.url, r"<a href='([^']+)'.*?>.*?>.*?([a-zA-Z]+).*?<\/a>")
    logger.info('EXTRA= ' + item.extra)
    for url, server in urls:
        itemlist.append(
            Item(channel=item.channel,
                 action='play',
                 title=item.title + ' [COLOR blue][' + server + '][/COLOR]',
                 contentType="movie",
                 server=server,
                 url=url))

    autoplay.start(itemlist, item)

    return itemlist


def play(item):

    data, c = unshortenit.unshorten(item.url)

    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.title
        videoitem.fulltitle = item.fulltitle
        videoitem.show = item.show
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel

    return itemlist





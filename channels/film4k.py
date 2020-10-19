# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per film4k
# ------------------------------------------------------------

from core import support
from platformcode import logger, config


def findhost(url):
    return support.httptools.downloadpage(url).url

host = config.get_channel_url(findhost)


@support.menu
def mainlist(item):

    film = ['movies',
            ('Qualità', ['', 'menu', 'quality']),
            ('Generi', ['movies', 'menu', 'genres']),
            ('Anno', ['movies', 'menu', 'releases']),
            ('Più popolari', ['trending/?get=movies', 'peliculas']),
            ('Più votati', ['ratings/?get=movies', 'peliculas'])]
    tvshow = ['/tvshows',
              ('Più popolari', ['trending/?get=tv', 'peliculas']),
              ('Più votati', ['ratings/?get=tv', 'peliculas'])]
    return locals()


def search(item, text):
    logger.info()
    item.url = item.url + "/?s=" + text
    try:
        return support.dooplay_search(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []



def peliculas(item):
    if 'anime' in item.url:
        return support.dooplay_peliculas(item, True)
    else:
        return support.dooplay_peliculas(item, False)


def episodios(item):
    itemlist = support.dooplay_get_episodes(item)
    return itemlist


def findvideos(item):
    itemlist = []
    if item.contentType == 'episode':
        linkHead = support.httptools.downloadpage(item.url, only_headers=True).headers['link']
        epId = support.scrapertools.find_single_match(linkHead, r'\?p=([0-9]+)>')
        for link in support.dooplay_get_links(item, host, paramList=[['tv', epId, 1, 'title', 'server']]):
            itemlist.append(
                item.clone(action="play", url=link['url']))
    else:
        for link, quality in support.match(item.url, patron="(" + host + """links/[^"]+).*?class="quality">([^<]+)""").matches:
            srv = support.servertools.find_video_items(data=support.httptools.downloadpage(link).data)
            for s in srv:
                s.quality = quality
            itemlist.extend(srv)
    return support.server(item, itemlist=itemlist)


@support.scrape
def menu(item):
    action = 'peliculas'
    if item.args in ['genres','releases']:
        patronBlock = r'<nav class="' + item.args + r'">(?P<block>.*?)</nav'
        patronMenu= r'<a href="(?P<url>[^"]+)"[^>]*>(?P<title>[^<]+)<'
    else:
        patronBlock = r'class="main-header">(?P<block>.*?)headitems'
        patronMenu = r'(?P<url>' + host + r'quality/[^/]+/\?post_type=movies)">(?P<title>[^<]+)'
    return locals()

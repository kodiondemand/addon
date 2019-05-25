# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per guardogratis
# 
# ----------------------------------------------------------
import re

import urlparse

from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import logger, config

__channel__ = "guardogratis"

host = "https://guardogratis.it/"

headers = [['Referer', host]]

def mainlist(item):
    logger.info("[guardogratis.py] mainlist")

    # Main options
    itemlist = [Item(channel=item.channel,
                     action="list_titles",
                     title="[COLOR azure]Film[/COLOR]",
                     url="%s/movies/" % host,
                     extra="movie",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="list_titles",
                     title="[COLOR azure]Top Film[/COLOR]",
                     url="%s/top-imdb/" % host,
                     extra="movie",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="categorie",
                     title="[COLOR azure]Categorie[/COLOR]",
                     url="%s" % host,
                     extra="categorie",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="list_titles",
                     title="[COLOR azure]Serie Tv[/COLOR]",
                     url="%s/series/" % host,
                     extra="tvshow",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="search",
                     title="[COLOR yellow]Cerca Film[/COLOR]",
                     extra="movie",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search"),
                Item(channel=item.channel,
                     action="search",
                     title="[COLOR yellow]Cerca SerieTV[/COLOR]",
                     extra="tvshow",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

    return itemlist

def list_titles(item):
    logger.info("[guardogratis.py] list_titles")
    itemlist = []
    
    tipo='movie'
    if 'tvshow' in item.extra: tipo='tv'

    if item.url == "":
        item.url = host
    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    patronvideos = '<div data-movie-id=.*?href="([^"]+)".*?data-original="([^"]+)".*?<h2>([^<]+)<\/h2>.*?[I,T]MDb:\s*([^<]+)<\/div>'

    matches = re.compile(patronvideos, re.DOTALL).finditer(data)
    
    for match in matches:
        scrapedurl = urlparse.urljoin(item.url, match.group(1))
        scrapedthumbnail = urlparse.urljoin(item.url, match.group(2))
        scrapedthumbnail = scrapedthumbnail.replace(" ", "%20")
        rate='  IMDb: [[COLOR orange]%s[/COLOR]]' % match.group(4) if match.group(4)!='N/A'else ''
        scrapedtitle = scrapertools.unescape(match.group(3))
        #scrapedtitle = scrapertools.unescape(match.group(3))+rate
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos" if not 'tvshow' in item.extra else 'serietv',
                 contentType="movie" if not 'tvshow' in item.extra else 'serie',
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 title=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 extra=item.extra,
                 viewmode="movie_with_plot"))

    nextpage_regex=''
    if item.extra in "movies,tvshow":
        nextpage_regex='<div id="pagination" style="margin: 0;">.*?active.*?href=\'([^\']+)\'.*?</div>'
    elif item.extra=="categorie":
        nextpage_regex='<li class=\'active\'>.*?href=\'([^\']+)\'.*?</a></li>'

    if nextpage_regex:
        next_page = scrapertools.find_single_match(data, nextpage_regex)
        if next_page != "":
            itemlist.append(
                Item(channel=item.channel,
                     action="list_titles",
                     title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                     url="%s" % next_page,
                     extra=item.extra,
                     thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png"))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

def search(item, texto):
    logger.info("[guardogratis.py] search")
    item.url = host + "/?s=" + texto
    try:
        if item.extra == "movie":
            return list_titles(item)
        if item.extra == "tvshow":
            return list_titles(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

def categorie(item):
    logger.info("[guardogratis.py] categorie")
    itemlist = []

    if item.url == "":
        item.url = host

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data
    patronvideos = '<li id="menu-item-.*?category.*?href="([^"]+)">([^"]+)</a>'

    matches = re.compile(patronvideos, re.DOTALL).finditer(data)
    
    for match in matches:
        scrapedurl = urlparse.urljoin(item.url, match.group(1))
        scrapedtitle = match.group(2)
        itemlist.append(
            Item(channel=item.channel,
                 action="list_titles",
                 title=scrapedtitle,
                 url=scrapedurl,
                 extra=item.extra,
                 folder=True))

    return itemlist


def serietv(item):
    logger.info("[guardogratis.py] serietv")

    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    patron = '<a href="([^"]+)">Episode[^<]+</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = scrapedurl
        scrapedtitle = scrapedtitle.replace(host, "")
        scrapedtitle = scrapedtitle.replace("episode/", "")
        scrapedtitle = scrapedtitle.replace("/", "")
        scrapedtitle = scrapedtitle.replace("-", " ")
        scrapedtitle = scrapedtitle.title()
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 folder=True))

    if config.get_videolibrary_support() and len(itemlist) != 0:
        itemlist.append(
            Item(channel=item.channel,
                title="[COLOR lightblue]%s[/COLOR]" % config.get_localized_string(30161),
                url=item.url,
                action="add_serie_to_library",
                extra="serietv",
                show=item.show))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

def findvideos(item):
    logger.info("[guardogratis.py] findvideos")

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    itemlist = servertools.find_video_items(data=data)
    for i in itemlist:
        tab=re.compile('<div\s*id="(tab[^"]+)"[^>]+>[^>]+>[^>]+src="http[s]*:%s[^"]+"'%i.url.replace('http:','').replace('https:',''), re.DOTALL).findall(data)
        qual=''
        if tab:
            qual=re.compile('<a\s*href="#%s">([^<]+)<'%tab[0], re.DOTALL).findall(data)[0].replace("'","")
            qual="[COLOR orange]%s[/COLOR] - "%qual
        i.title='%s[COLOR green][B]%s[/B][/COLOR] - %s'%(qual,i.title[2:],item.title)
        i.channel=__channel__
        i.fulltitle=item.title

    return itemlist


# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Altadefinizione HD
# ----------------------------------------------------------
import re

from channelselector import thumb
from core import httptools, scrapertools, servertools, tmdb
from core.item import Item
from platformcode import logger, config
from specials import autoplay

host = "https://altadefinizione.doctor"

headers = [['Referer', host]]

list_servers = ['openload']
list_quality = ['default']

def mainlist(item):
    logger.info("[altadefinizionehd.py] mainlist")

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = [Item(channel=item.channel,
                     action="video",
                     title="[B]Film[/B]",
                     url=host + '/movies/',
                     thumbnail=NovitaThumbnail,
                     fanart=FilmFanart),
                Item(channel=item.channel,
                     action="menu",
                     title="[B] > Film per Genere[/B]",
                     url=host,
                     extra='GENERE',
                     thumbnail=NovitaThumbnail,
                     fanart=FilmFanart),
                Item(channel=item.channel,
                     action="menu",
                     title="[B] > Film per Anno[/B]",
                     url=host,
                     extra='ANNO',
                     thumbnail=NovitaThumbnail,
                     fanart=FilmFanart),
                Item(channel=item.channel,
                     action="video",
                     title="Film Sub-Ita",
                     url=host + "/genre/sub-ita/",
                     thumbnail=NovitaThumbnail,
                     fanart=FilmFanart),
                Item(channel=item.channel,
                     action="video",
                     title="Film Rip",
                     url=host + "/genre/dvdrip-bdrip-brrip/",
                     thumbnail=NovitaThumbnail,
                     fanart=FilmFanart),
                Item(channel=item.channel,
                     action="video",
                     title="Film al Cinema",
                     url=host + "/genre/cinema/",
                     thumbnail=NovitaThumbnail,
                     fanart=FilmFanart),
                Item(channel=item.channel,
                     action="search",
                     extra="movie",
                     title="[COLOR blue]Cerca Film...[/COLOR]",
                     thumbnail=CercaThumbnail,
                     fanart=FilmFanart)]

    autoplay.show_option(item.channel, itemlist)

    itemlist = thumb(itemlist)

    return itemlist


def menu(item):
    logger.info("[altadefinizionehd.py] menu")
    itemlist = []
    data = httptools.downloadpage(item.url, headers=headers).data
    logger.info("[altadefinizionehd.py] DATA"+data)
    patron = r'<li id="menu.*?><a href="#">FILM PER ' + item.extra + r'<\/a><ul class="sub-menu">(.*?)<\/ul>'
    logger.info("[altadefinizionehd.py] BLOCK"+patron)
    block = scrapertools.find_single_match(data, patron)
    logger.info("[altadefinizionehd.py] BLOCK"+block)
    patron = r'<li id=[^>]+><a href="(.*?)">(.*?)<\/a><\/li>'
    matches = re.compile(patron, re.DOTALL).findall(block)
    for url, title in matches:
        itemlist.append(
            Item(channel=item.channel,
            action='video',
            title=title,
            url=url))
    return itemlist



def newest(categoria):
    logger.info("[altadefinizionehd.py] newest" + categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "peliculas":
            item.url = host
            item.action = "video"
            itemlist = video(item)

            if itemlist[-1].action == "video":
                itemlist.pop()

    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def video(item):
    logger.info("[altadefinizionehd.py] video")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    logger.info("[altadefinizionehd.py] Data" +data)
    if 'archive-content' in data:
        regex = r'<div id="archive-content".*?>(.*?)<div class="pagination'
    else:
        regex = r'<div class="items".*?>(.*?)<div class="pagination'
    block = scrapertools.find_single_match(data, regex)
    logger.info("[altadefinizionehd.py] Block" +block)
    
    patron = r'<article .*?class="item movies">.*?<img src="([^"]+)".*?<span class="quality">(.*?)<\/span>.*?<a href="([^"]+)">.*?<h4>([^<]+)<\/h4>(.*?)<\/article>'
    matches = re.compile(patron, re.DOTALL).findall(block)

    for scrapedthumb, scrapedquality, scrapedurl, scrapedtitle, scrapedinfo in matches:
        title = scrapedtitle + " [" + scrapedquality + "]"
        
        patron = r'IMDb: (.*?)<\/span> <span>(.*?)<\/span>.*?"texto">(.*?)<\/div>'
        matches = re.compile(patron, re.DOTALL).findall(scrapedinfo)
        logger.info("[altadefinizionehd.py] MATCHES" + str(matches))
        for rating, year, plot in matches:
        
            infoLabels = {}
            infoLabels['Year'] = year
            infoLabels['Rating'] = rating
            infoLabels['Plot'] = plot
            itemlist.append(
                Item(channel=item.channel,
                    action="findvideos",
                    contentType="movie",
                    title=title,
                    fulltitle=scrapedtitle,
                    infoLabels=infoLabels,
                    url=scrapedurl,
                    thumbnail=scrapedthumb))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    patron = '<a class='+ "'arrow_pag'" + ' href="([^"]+)"'
    next_page = scrapertools.find_single_match(data, patron)
    if next_page != "":
        itemlist.append(
            Item(channel=item.channel,
                 action="video",
                 title="[COLOR blue]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=next_page,
                 thumbnail=thumb()))

    return itemlist


def search(item, texto):
    logger.info("[altadefinizionehd.py] init texto=[" + texto + "]")
    item.url = host + "/?s=" + texto
    return search_page(item)

def search_page(item):
        itemlist = []
        data = httptools.downloadpage(item.url, headers=headers).data

        patron = r'<img src="([^"]+)".*?.*?<a href="([^"]+)">(.*?)<\/a>'
        matches = re.compile(patron, re.DOTALL).findall(data)

        for scrapedthumbnail, scrapedurl, scrapedtitle in matches:
            scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
            itemlist.append(
                Item(channel=item.channel,
                    action="findvideos",
                    title=scrapedtitle,
                    fulltitle=scrapedtitle,
                    url=scrapedurl,
                    thumbnail=scrapedthumbnail))

        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

        patron = '<a class='+ "'arrow_pag'" + ' href="([^"]+)"'
        next_page = scrapertools.find_single_match(data, patron)
        if next_page != "":
            itemlist.append(
                Item(channel=item.channel,
                    action="search_page",
                    title="[COLOR blue]" + config.get_localized_string(30992) + "[/COLOR]",
                    url=next_page,
                    thumbnail=thumb()))
    
        return itemlist    


def findvideos(item):
    data = httptools.downloadpage(item.url).data
    patron = r"<li id='player-.*?'.*?class='dooplay_player_option'\sdata-type='(.*?)'\sdata-post='(.*?)'\sdata-nume='(.*?)'>.*?'title'>(.*?)</"
    matches = re.compile(patron, re.IGNORECASE).findall(data)

    itemlist = []

    for scrapedtype, scrapedpost, scrapednume, scrapedtitle in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action="play",
                 fulltitle=item.title + " [" + scrapedtitle + "]",
                 show=scrapedtitle,
                 title=item.title + " [COLOR blue][" + scrapedtitle + "][/COLOR]",
                 url=host + "/wp-admin/admin-ajax.php",
                 post=scrapedpost,
                 server=scrapedtitle,
                 nume=scrapednume,
                 type=scrapedtype,
                 extra=item.extra,
                 folder=True))

    autoplay.start(itemlist, item)

    return itemlist

def play(item):
    import urllib
    payload = urllib.urlencode({'action': 'doo_player_ajax', 'post': item.post, 'nume': item.nume, 'type': item.type})
    data = httptools.downloadpage(item.url, post=payload).data

    patron = r"<iframe.*src='(([^']+))'\s"
    matches = re.compile(patron, re.IGNORECASE).findall(data)

    url = matches[0][0]
    url = url.strip()
    data = httptools.downloadpage(url, headers=headers).data

    itemlist = servertools.find_video_items(data=data)

    return itemlist



NovitaThumbnail = "https://superrepo.org/static/images/icons/original/xplugin.video.moviereleases.png.pagespeed.ic.j4bhi0Vp3d.png"
GenereThumbnail = "https://farm8.staticflickr.com/7562/15516589868_13689936d0_o.png"
FilmFanart = "https://superrepo.org/static/images/fanart/original/script.artwork.downloader.jpg"
CercaThumbnail = "http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search"
CercaFanart = "https://i.ytimg.com/vi/IAlbvyBdYdY/maxresdefault.jpg"
ListTxt = "[COLOR orange]Torna a video principale [/COLOR]"
AvantiTxt = config.get_localized_string(30992)
AvantiImg = "http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png"
thumbnail = "http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"

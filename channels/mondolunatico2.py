# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per MondoLunatico 2.0
# ------------------------------------------------------------

import re
import urlparse
import urllib
import urllib2
import time

from channelselector import thumb
from specials import autoplay, filtertools
from core import scrapertools, httptools, tmdb, servertools, support, scrapertoolsV2
from core.item import Item
from platformcode import logger, config, platformtools

channel = "mondolunatico2"
host = "https://mondolunatico.org/stream/"
headers = [['Referer', host]]

list_servers = ['verystream', 'wstream', 'openload', 'streamango']
list_quality = ['HD', 'default']

def mainlist(item):

    # Main options
    itemlist = []
    support.menu(itemlist, 'Novità bold', 'carousel', host, contentType='movie', args='movies')
    support.menu(itemlist, 'Sub ITA bold', 'carousel_subita', host, contentType='movie', args='movies')
    support.menu(itemlist, 'Ultime Richieste Inserite bold', 'carousel_request', host, contentType='movie', args='movies')
    support.menu(itemlist, 'Film Nelle Sale bold', 'carousel_cinema', host, contentType='movie', args='movies')
    support.menu(itemlist, 'Film Ultimi Inseriti submenu', 'carousel_last', host, contentType='movie', args='movies')
    support.menu(itemlist, 'Film Top ImDb submenu', 'top_imdb', host + 'top-imdb/', contentType='movie', args='movies')
    support.menu(itemlist, 'Serie TV', 'carousel_episodes', host, contentType='episode', args='tvshows')
    support.menu(itemlist, 'Serie TV Top ImDb submenu', 'top_serie', host + 'top-imdb/', contentType='episode', args='tvshows')
    support.menu(itemlist, '[COLOR blue]Cerca...[/COLOR] bold', 'search', host)
    autoplay.init(item.channel, list_servers, list_quality)
    autoplay.show_option(item.channel, itemlist)

    return itemlist

# ---------------------------------------------------------------------------------------------------------------------------------------------

def carousel(item, regex=r'<h2>Ultime Richieste Inserite</h2>(.*?)<header>', contentType="movie"):
    logger.info("[mondolunatico2.py] carousel")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    block = scrapertools.find_single_match(data,regex)

    patron = r'<article id.*?src="([^"]+).*?alt="([^"]+).*?href="([^"]+).*?,.([^<]+)'
    matches = re.compile(patron, re.DOTALL).findall(block)

    for scrapedthumbnail, scrapedtitle, scrapedurl, year in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        scrapedtitle = re.sub(r'[0-9]{4}', "", scrapedtitle)
        itemlist.append(
            Item(channel=channel,
                 action="findvideos",
                 contentType=contentType,
                 title=scrapedtitle + " " + "[COLOR orange][" + year + "][/COLOR]",
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 show=scrapedtitle,
                 args=item.args,
                 infoLabels={'year': year},
                 thumbnail=scrapedthumbnail))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist

# ---------------------------------------------------------------------------------------------------------------------------------------------
def carousel_subita(item):
    return carousel(item, regex=r'<h2>Film SubITA</h2>(.*?)<header>', contentType="movie")
# ---------------------------------------------------------------------------------------------------------------------------------------------
def carousel_request(item):
    return carousel(item, regex=r'<h2>Ultime Richieste Inserite</h2>(.*?)<header>', contentType="movie")
# ---------------------------------------------------------------------------------------------------------------------------------------------
def carousel_cinema(item):
    return carousel(item, regex=r'<h2>Nelle Sale</h2>(.*?)<header>', contentType="movie")
# ---------------------------------------------------------------------------------------------------------------------------------------------
def carousel_last(item):
    return carousel(item, regex=r'<h2>Ultimi Film Inseriti</h2>(.*?)<header>', contentType="movie")
# ---------------------------------------------------------------------------------------------------------------------------------------------
def carousel_episodes(item):
    return carousel(item, regex=r'<h2>Serie TV</h2>(.*?)<header>', contentType="episode")
# ---------------------------------------------------------------------------------------------------------------------------------------------

def top_imdb(item, contentType='movie', regex=r'<h1.*?TOP IMDb.*?<h3>(.*?)<h3>'):
    logger.info("[mondolunatico2.py] top_imdb")
    itemlist = []

    minpage = 20
    p = 1
    if '{}' in item.url:
        item.url, p = item.url.split('{}')
        p = int(p)

    data = httptools.downloadpage(item.url, headers=headers).data

    block = scrapertools.find_single_match(data, regex)

    patron = r"<div class='image'><div class='[^']+'><a href='([^']+)'[^']+'([^']+)'[^']+'([^']+)"
    matches = re.compile(patron, re.DOTALL).findall(block)

    for i, (scrapedurl, scrapedthumbnail, scrapedtitle) in enumerate(matches):
        if (p - 1) * minpage > i: continue
        if i >= p * minpage: break
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        scrapedtitle = re.sub(r'[0-9]{4}', "", scrapedtitle)
        scrapedthumbnail = scrapedthumbnail.replace ("-90x135","").replace("/w92/", "/w600_and_h900_bestv2/")
        itemlist.append(
            Item(channel=channel,
                 action="findvideos" if "movie" in contentType else "episodios",
                 contentType=item.contentType,
                 contentTitle=scrapedtitle,
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 show=scrapedtitle,
                 thumbnail=scrapedthumbnail,
                 args=item.args))

    if len(matches) >= p * minpage:
        thumbnail = thumb(itemlist=[])
        scrapedurl = item.url + '{}' + str(p + 1)
        itemlist.append(
            Item(channel=channel,
                 contentType=item.contentType,
                 action="top_imdb",
                 title="[COLOR blue][B]Successivo >[/B][/COLOR]",
                 thumbnail=thumbnail,
                 url=scrapedurl))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist

# ---------------------------------------------------------------------------------------------------------------------------------------------
def top_serie(item):
    return top_imdb(item, contentType='episode', regex=r'<h3>TVShows</h3>(.*?)<div class="sidebar scrolling">')
# ---------------------------------------------------------------------------------------------------------------------------------------------

def search(item, texto):
    logger.info("[mondolunatico2.py] " + item.url + " search " + texto)
    item.url = host + "?s=" + texto

    try:
        return peliculas(item)

    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
            return []

# ---------------------------------------------------------------------------------------------------------------------------------------------

def peliculas(item):
    logger.info("[mondolunatico2.py] peliculas")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    patron = r'<div class="result-item">.*?<a href="([^"]+).*?src="([^"]+).*?alt="([^"]+).*?span class="([^"]+).*?<span class="year">([^<]+).*?<p>([^<]+)'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, args, year, scrapedplot in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        scrapedtitle = re.sub(r'[0-9]{4}', "", scrapedtitle)
        type = "[COLOR aqua][Serie][/COLOR]" if "tvshows" in item.args else "[COLOR aqua][Film][/COLOR]"
        itemlist.append(
            Item(channel=channel,
                 action="episodios" if "tvshows" in item.args else "findvideos",
                 contentType="episode" if "tvshows" in item.args else "movie",
                 title=scrapedtitle + " " + "[COLOR orange][" + year + "][/COLOR]" + " " + type,
                 fulltitle=scrapedtitle,
                 thumbnail=scrapedthumbnail,
                 url=scrapedurl,
                 show=scrapedtitle,
                 args=args,
                 infoLabels={'year':year},
                 plot=scrapedplot))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

# ---------------------------------------------------------------------------------------------------------------------------------------------

def findvideos(item):
    logger.info("[mondolunatico2.py] findvideos")

    if item.args == "tvshows":
        ret=support.dooplay_get_links(item, host)

        if ret == []:
            return episodios(item)
        else:
            item.url = ret[0]["url"]
            return videoplayer(item)

    if item.args == "movies" or "movie":
        return videoplayer(item)

    else:
        return halfplayer(item)

# ---------------------------------------------------------------------------------------------------------------------------------------------

def episodios(item):
    logger.info("[mondolunatico2.py] episodios")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    if "<h2>Stagioni ed Episodi</h2>" in data:
        # Se è presente direttamente la lista Stagioni con i relativi episodi
        block = scrapertools.find_single_match(data, r'<h2>Stagioni ed Episodi</h2>(.*?)<div class=\'sbox\'>')
        patron = r'episodiotitle.*?href=\'([^\']+)\'>([^<]+)'
        matches = re.compile(patron, re.DOTALL).findall(block)
        for scrapedurl, scrapedtitle in matches:
            itemlist.append(
                Item(channel=channel,
                     action="videoplayer",
                     contentType=item.contentType,
                     title=scrapedtitle,
                     thumbnail=item.thumbnail,
                     fulltitle=scrapedtitle,
                     url=scrapedurl,
                     args=item.args,
                     show=item.show))
        support.videolibrary(itemlist, item, 'color kod')
        return itemlist

    if "File Unico..." in data:
        #Se è direttamente un file unico
        return dooplayer(item)

    if "http://mondolunatico.org/stream/wp-content/uploads/2017/08/hand.gif" in data:
        # Keeplinks
        return keeplink(item)

    else:
        # Se nella lista è presente Dooplayer con elenco episodi
        patron = r'<div class="sp-head" title="Espandi">([^<]+).*?<iframe.*?src="([^"]+)'
        matches = re.compile(patron, re.DOTALL).findall(data)
        if len(matches) > 1:
            for scrapedtitle, scrapedurl in matches:
                itemlist.append(
                    Item(channel=channel,
                         action="player_list",
                         contentType=item.contentType,
                         title=scrapedtitle,
                         thumbnail=item.thumbnail,
                         fulltitle=scrapedtitle,
                         url=scrapedurl,
                         show=item.show))
            return itemlist
        else:
             return dooplayer(item)

# ---------------------------------------------------------------------------------------------------------------------------------------------

def player(item):
    logger.info ("[mondolunatico2.py] player")

    data = httptools.downloadpage(item.url, headers=headers).data

    item.url = scrapertools.find_single_match(item.url, r'([^/]+//[^/]+/[^/]+/[^/]+)')

    if "https://mondolunatico.tk" in data:
        data = httptools.downloadpage(item.url, headers=headers).data
        link = scrapertools.find_single_match(data, r'<p><iframe src="(.*?/.*?)[A-Z]')
        item.url = link
        return halfplayer(item)

    if "mondolunatico.tk" in item.url:
        return halfplayer(item)

    #Scarica il link del video integrato nella pagina
    ret=support.dooplay_get_links(item, host)

    #Prelevo il link del video integrato
    url = ret[0]["url"]

    data = httptools.downloadpage(url, headers=headers).data

    if "zmdi zmdi-playlist-audio zmdi-hc-3x" in data:
        return player_list(item)

    else:
        #Correggo il link con il lin del POST
        url = url.replace("/v/", "/api/source/").replace("/p/", "/api/source/")

        postData = urllib.urlencode({
            "r": "",
            "d": "modolunatico.tk",
        })

        block = httptools.downloadpage(url, post=postData).data

        patron = r'"file":".*?\/(r[^"]+)'
        matches = re.compile(patron, re.DOTALL).findall(block)

        itemlist = []

        for scrapedurl in matches:
            scrapedurl = "https://fvs.io/" + scrapedurl
            itemlist.append(
                Item(channel=channel,
                    action="play",
                    contentType=item.contentType,
                    title=item.title,
                    thumbnail=item.thumbnail,
                    fulltitle=item.title,
                     url=scrapedurl,
                    show=item.show))

        autoplay.start(itemlist, item)

        return itemlist

# ---------------------------------------------------------------------------------------------------------------------------------------------

def player_list(item):
    itemlist = []

    # Scarico la pagina
    data = httptools.downloadpage(item.url, headers=headers).data

    if "panel_toggle toggleable" in data:
        # Prelevo il blocco lista puntate
        block = scrapertools.find_single_match(data, r'panel_toggle toggleable.*?(<div.*?)<!-- Javascript -->')

        patron = r'data-url="([^"]+)">.*?([A-Z].*?)  '
        matches = re.compile(patron, re.DOTALL).findall(block)

        for scrapedurl, scrapedtitle in matches:
            scrapedtitle = re.sub('mp4|avi|mkv', '', scrapedtitle)
            scrapedtitle = re.sub('WebRip|WEBRip|x264|AC3|1080p|DLMux|XviD-|BDRip|BluRay|HD|WEBMux|H264|BDMux|720p|TV|NFMux|DVDRip|DivX|DVDip|Ac3|Dvdrip|Mux|NovaRip|DVD|SAT|Divx', '', scrapedtitle)
            scrapedtitle = re.sub('ITA|ENG|Italian|SubITA|SUBITA|iTALiAN|LiAN|Ita', '', scrapedtitle)
            scrapedtitle = re.sub('Pir8|UBi|M L|BEDLAM|REPACK|DD5.1|bloody|SVU', '', scrapedtitle)
            scrapedtitle = scrapedtitle.replace(".", " ").replace(" - ", " ").replace("  -", "").replace("  ", "")
            itemlist.append(
                Item(channel=channel,
                    action="halfplayer",
                    contentType=item.contentType,
                    title=scrapedtitle,
                    thumbnail=item.thumbnail,
                    fulltitle=scrapedtitle,
                    url="https://mondolunatico.tk" + scrapedurl,
                    show=item.show))

        support.videolibrary(itemlist, item, 'color kod')

        return itemlist

    else:
        return player(item)

# ---------------------------------------------------------------------------------------------------------------------------------------------

def dooplayer(item):
    logger.info ("[mondolunatico2.py] dooplayer")
    itemlist = []

    url = item.url
    data = httptools.downloadpage(url, headers=headers).data

    link= scrapertools.find_single_match(data, r'(https://mondolunatico.tk/./[^"]+)')

    data = httptools.downloadpage(link, headers=headers).data
    if "panel_toggle toggleable" in data:
        item.url = link
        return player_list(item)

    # Correggo il link con il lin del POST
    link1 = link.replace("/v/", "/api/source/").replace("/p/", "/api/source/")

    postData = urllib.urlencode({
        "r": link,
        "d": "modolunatico.tk",
    })

    block = httptools.downloadpage(link1, post=postData).data

    patron = r'"file":".*?\/(r[^"]+)'
    matches = re.compile(patron, re.DOTALL).findall(block)

    for scrapedurl in matches:
        scrapedurl = "https://fvs.io/" + scrapedurl
        itemlist.append(
            Item(channel=channel,
                 action="play",
                 contentType=item.contentType,
                 title=item.title,
                 thumbnail=item.thumbnail,
                 fulltitle=item.title,
                 url=scrapedurl,
                 show=item.show))

    autoplay.start(itemlist, item)
    support.videolibrary(itemlist, item, 'color kod')

    return itemlist

# ---------------------------------------------------------------------------------------------------------------------------------------------

def keeplink(item):
    itemlist = []

    # Scarico la pagina
    data = httptools.downloadpage(item.url).data

    # Prendo url keeplink
    patron = 'href="(https?://www\.keeplinks\.(?:co|eu)/p92/([^"]+))"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for keeplinks, id in matches:
        headers = [['Cookie', 'flag[' + id + ']=1; defaults=1; nopopatall=' + str(int(time.time()))],
                   ['Referer', keeplinks]]

        html = httptools.downloadpage(keeplinks, headers=headers).data
        data += str(scrapertools.find_multiple_matches(html, '</lable><a href="([^"]+)" target="_blank"'))

        patron = 'src="([^"]+)" frameborder="0"'
        matches = re.compile(patron, re.DOTALL).findall(data)
        for scrapedurl in matches:
            data += httptools.downloadpage(scrapedurl).data

        for videoitem in servertools.find_video_items(data=data):
            videoitem.title = item.title + " - " + videoitem.title
            videoitem.fulltitle = item.fulltitle
            videoitem.thumbnail = item.thumbnail
            videoitem.show = item.show
            videoitem.plot = item.plot
            videoitem.channel = item.channel
            itemlist.append(videoitem)

    return itemlist

# ---------------------------------------------------------------------------------------------------------------------------------------------

def videoplayer(item):
    logger.info("[mondolunatico2.py] videoplayer")
    itemlist = []

    for link in support.dooplay_get_links(item, host):
        server = link['server'][:link['server'].find(".")]
        if server == "":
            server = "mondolunatico"

        itemlist.append(
            Item(channel=item.channel,
                 action="player" if "mondolunatico" in server else "play",
                 title=server + " [COLOR blue][" + link['title'] + "][/COLOR]",
                 url=link['url'],
                 server=server,
                 fulltitle=item.fulltitle,
                 thumbnail=item.thumbnail,
                 show=item.show,
                 quality=link['title'],
                 contentType=item.contentType,
                 folder=False))

    support.videolibrary(itemlist, item, 'color kod', function_level=2)

    autoplay.start(itemlist, item)

    return itemlist

# ---------------------------------------------------------------------------------------------------------------------------------------------

def halfplayer(item):
    logger.info("[mondolunatico2.py] halfplayer")

    url=item.url

    # Correggo il link con il lin del POST
    url = url.replace("/v/", "/api/source/").replace("/p/", "/api/source/")

    postData = urllib.urlencode({
        "r": "",
        "d": "modolunatico.tk",
    })

    block = httptools.downloadpage(url, post=postData).data

    patron = r'"file":".*?\/(r[^"]+)'
    matches = re.compile(patron, re.DOTALL).findall(block)

    for scrapedurl in matches:
        item.url = "https://fvs.io/" + scrapedurl
        item.server = ""
        itemlist = platformtools.play_video(item, force_direct=True, autoplay=True)

        return itemlist

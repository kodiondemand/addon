# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per italiafilmhd
# ----------------------------------------------------------
import base64
import re
import urlparse

from channels import autoplay
from channels import filtertools, support
from core import scrapertools, servertools, httptools
from core.item import Item
from core import tmdb
from platformcode import logger, config

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['verystream', 'openload', 'youtube']
list_quality = ['default']

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'italiafilmhd')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'italiafilmhd')

host = "https://italiafilm.network"

headers = [['Referer', host]]


def mainlist(item):
    logger.info("kod.italiafilmhd mainlist")

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = [
        Item(channel=item.channel,
             title="[COLOR azure]Novita'[/COLOR]",
             action="fichas",
             url=host + "/cinema/",
             thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
        Item(channel=item.channel,
             title="[COLOR azure]Ultimi Film Inseriti[/COLOR]",
             action="fichas",
             url=host + "/film/",
             thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
        Item(channel=item.channel,
             title="[COLOR azure]Film per Genere[/COLOR]",
             action="genere",
             url=host,
             thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
        Item(channel=item.channel,
             title="Serie TV",
             text_color="azure",
             action="tv_series",
             url="%s/serie-tv-hd/" % host,
             thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
        Item(channel=item.channel,
             title="[COLOR orange]Cerca...[/COLOR]",
             action="search",
             extra="movie",
             thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def newest(categoria):
    logger.info("[italiafilmvideohd.py] newest" + categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "film":
            item.url = host + "/cinema/"
            item.action = "fichas"
            itemlist = fichas(item)

            if itemlist[-1].action == "fichas":
                itemlist.pop()

    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def search(item, texto):
    logger.info("[italiafilmvideohd.py] " + item.url + " search " + texto)

    item.url = host + "/?s=" + texto

    try:
        return fichas(item)

    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def genere(item):
    logger.info("[italiafilmvideohd.py] genere")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    patron = '<div class="sub_title">Genere</div>(.+?)</div>'
    data = scrapertools.find_single_match(data, patron)

    patron = '<li>.*?'
    patron += 'href="([^"]+)".*?'
    patron += '<i>([^"]+)</i>'

    matches = re.compile(patron, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapedtitle.replace('&amp;', '-')
        itemlist.append(
            Item(channel=item.channel,
                 action="fichas",
                 title=scrapedtitle,
                 url=scrapedurl,
                 folder=True))

    return itemlist


def fichas(item):
    logger.info("[italiafilmvideohd.py] fichas")

    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data
    # fix - calidad

    patron = '<li class="item">.*?'
    patron += 'href="([^"]+)".*?'
    patron += 'title="([^"]+)".*?'
    patron += '<img src="([^"]+)".*?'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scraped_2, scrapedtitle, scrapedthumbnail in matches:
        scrapedurl = scraped_2

        title = scrapertools.decodeHtmlentities(scrapedtitle)
        # title += " (" + scrapedcalidad + ")

        # ------------------------------------------------
        scrapedthumbnail = httptools.get_url_headers(scrapedthumbnail)
        # ------------------------------------------------
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentType="movie",
                 title=title,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 fulltitle=title,
                 show=scrapedtitle))

    # Paginación
    next_page = scrapertools.find_single_match(data, '<a href="([^"]+)"\s*><span aria-hidden="true">&raquo;')

    if next_page != "":
        itemlist.append(
            Item(channel=item.channel,
                 action="fichas",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=next_page,
                 text_color="orange",
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png"))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def tv_series(item):
    logger.info("[italiafilmvideohd.py] tv_series")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    blocco = scrapertools.find_single_match(data, r'<ul class="list_mt">(.*?)</ul>')
    patron = r'<a class="poster" href="([^"]+)" title="([^"]+)"[^>]*>\s*<img src="([^"]+)"[^>]+>'
    matches = re.findall(patron, blocco, re.DOTALL)

    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()

        itemlist.append(
            Item(channel=item.channel,
                 action="seasons",
                 contentType="tv",
                 title=scrapedtitle,
                 text_color="azure",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 fulltitle=scrapedtitle,
                 show=scrapedtitle))

    # Pagine
    next_page = scrapertools.find_single_match(data, '<a href="([^"]+)"\s*><span aria-hidden="true">&raquo;')

    if next_page != "":
        itemlist.append(
            Item(channel=item.channel,
                 action="fichas",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 text_color="orange",
                 url=next_page,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png"))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def seasons(item):
    logger.info("[italiafilmvideohd.py] seasons")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    url = scrapertools.find_single_match(data,
                                         r'<div class="playerhdpass" id="playerhdpass">\s*[^>]+>\s*<iframe[^s]+src="([^"]+)"[^>]*></iframe>')
    data = httptools.downloadpage(url, headers=headers).data
    blocco = scrapertools.find_single_match(data, r'<h3>STAGIONE</h3>\s*<ul>(.*?)</ul>')
    seasons = re.findall(r'<li[^>]*><a href="([^"]+)">([^<]+)</a></li>', blocco, re.DOTALL)

    for scrapedurl, season in seasons:
        itemlist.append(
            Item(channel=item.channel,
                 action="episodes",
                 contentType=item.contentType,
                 title="Stagione: %s" % season,
                 text_color="azure",
                 url="https://hdpass.net/%s" % scrapedurl,
                 thumbnail=item.thumbnail,
                 fulltitle=item.fulltitle,
                 show=item.show))

    return itemlist


def episodes(item):
    logger.info("[italiafilmvideohd.py] episodes")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    blocco = scrapertools.find_single_match(data, r'<section id="seasons">(.*?)</section>')
    episodes = re.findall(r'<li[^>]*><a href="([^"]+)">([^<]+)</a></li>', blocco, re.DOTALL)

    for scrapedurl, episode in episodes:
        itemlist.append(
            Item(channel=item.channel,
                 action="findvid_series",
                 contentType=item.contentType,
                 title="Episodio: %s" % episode,
                 text_color="azure",
                 url="https://hdpass.net/%s" % scrapedurl,
                 thumbnail=item.thumbnail,
                 fulltitle=item.fulltitle,
                 show=item.show))

    return itemlist


def findvideos(item):
    logger.info("[italiafilmvideohd.py] findvideos")

    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    patron = r'<div class="playerhdpass" id="playerhdpass"><iframe width=".+?" height=".+?" src="([^"]+)"'
    url = scrapertools.find_single_match(data, patron)

    if url:
        data += httptools.downloadpage(url, headers=headers).data

    itemlist = servertools.find_video_items(data=data)
    for videoitem in itemlist:
        videoitem.title = item.title + videoitem.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.show = item.show
        videoitem.plot = item.plot
        videoitem.channel = item.channel
        videoitem.contentType = item.contentType
        videoitem.language = IDIOMAS['Italiano']

    # Requerido para Filtrar enlaces

    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if item.contentType != 'episode':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            itemlist.append(
                Item(channel=item.channel, title='[COLOR yellow][B]Aggiungi alla videoteca[/B][/COLOR]', url=item.url,
                     action="add_pelicula_to_library", extra="findvideos", contentTitle=item.contentTitle))

    return itemlist


def findvid_series(item):
    logger.info("[italiafilmvideohd.py] findvideos")

    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data.replace('\n', '')
    patron = r'<iframe id="[^"]+" width="[^"]+" height="[^"]+" src="([^"]+)"[^>]+><\/iframe>'
    url = scrapertools.find_single_match(data, patron).replace("?alta", "")
    url = "https:" + url.replace("&download=1", "")

    data = httptools.downloadpage(url, headers=headers).data

    start = data.find('<div class="row mobileRes">')
    end = data.find('<div id="playerFront">', start)
    data = data[start:end]

    patron_res = '<div class="row mobileRes">(.*?)</div>'
    patron_mir = '<div class="row mobileMirrs">(.*?)</div>'
    patron_media = r'<input type="hidden" name="urlEmbed" data-mirror="([^"]+)" id="urlEmbed" value="([^"]+)"\s*/>'

    res = scrapertools.find_single_match(data, patron_res)

    urls = []
    for res_url, res_video in scrapertools.find_multiple_matches(res, '<option.*?value="([^"]+?)">([^<]+?)</option>'):

        data = httptools.downloadpage(urlparse.urljoin(url, res_url), headers=headers).data.replace('\n', '')
        mir = scrapertools.find_single_match(data, patron_mir)
        for mir_url in scrapertools.find_multiple_matches(mir, '<option.*?value="([^"]+?)">[^<]+?</value>'):
            data = httptools.downloadpage(urlparse.urljoin(url, mir_url), headers=headers).data.replace('\n', '')

            for media_label, media_url in re.compile(patron_media).findall(data):
                urls.append(support.url_decode(media_url))

    itemlist = servertools.find_video_items(data='\n'.join(urls))
    for videoitem in itemlist:
        server = re.sub(r'[-\[\]\s]+', '', videoitem.title)
        videoitem.text_color = "azure"
        videoitem.title = "".join(["[%s] " % ("[COLOR orange]%s[/COLOR]" % server.capitalize()), item.title])
        videoitem.fulltitle = item.fulltitle
        videoitem.show = item.show
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel

    return itemlist


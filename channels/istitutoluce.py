# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale istitutoluce
# ------------------------------------------------------------

import re
import urlparse

from core import httptools, scrapertools, servertools
from core.item import Item
from platformcode import logger, config

host = "https://patrimonio.archivioluce.com"
host2 = "https://www.archivioluce.com"

headers = [['Referer', host]]

PERPAGE = 7


def mainlist(item):
    logger.info("kod.istitutoluce mainlist")
    itemlist = [
        Item(
            channel=item.channel,
            title="[COLOR azure]Archivio - Tutti i Filmati[/COLOR]",
            action="peliculas",
            url="%s/luce-web/search/result.html?query=&perPage=7" % host,
            thumbnail="http://www.archivioluce.com/wp-content/themes/wpbootstrap/bootstrap/img/luce-logo.png"
        ),
        Item(
            channel=item.channel,
            title="[COLOR azure]Categorie Tematiche[/COLOR]",
            action="categorie",
            url="%s/navigazione-tematica/" % host2,
            thumbnail="http://www.archivioluce.com/wp-content/themes/wpbootstrap/bootstrap/img/luce-logo.png"
        ),
        Item(
            channel=item.channel,
            title="[COLOR yellow]Cerca...[/COLOR]",
            action="search",
            thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search"
        )
    ]

    return itemlist


def categorie(item):
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    bloque = scrapertools.find_single_match(data, '<section class="container directory">(.*?)<footer class="main">')
    patron = '<a class="label label-white" href="(.*?)">\s*(.*?)</a>'
    matches = re.compile(patron, re.DOTALL).findall(bloque)

    for scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapedtitle.title()
        itemlist.append(
            Item(channel=item.channel,
                 action="cat_results",
                 fulltitle=scrapedtitle,
                 title=scrapedtitle,
                 url=scrapedurl,
                 viewmode="movie_with_plot",
                 Folder=True))

    return itemlist


def cat_results(item):
    logger.info("kod.istitutoluce cat_results")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    # Estrae i contenuti 
    patron = '<a href="([^"]+)" class="thumbnail">\s*<h1>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl in matches:
        scrapedtitle = scrapedurl
        scrapedtitle = scrapedtitle.rsplit('/', 1)[-1].rsplit(".", 1)[0].replace("-", " ").title()
        scrapedurl = host + scrapedurl
        scrapedplot = ""
        # html = scrapertools.cache_page(scrapedurl)
        # start = html.find('<p class="abstract">')
        # end = html.find('</p>', start)
        # scrapedplot = html[start:end]
        # scrapedplot = re.sub(r'<[^>]*>', '', scrapedplot)
        # scrapedplot = scrapertools.decodeHtmlentities(scrapedplot)
        scrapedthumbnail = ""
        # cache = httptools.downloadpage(scrapedurl, headers=headers).data
        # patron = 'image: "(.*?)"'
        # matches = re.compile(patron, re.DOTALL).findall(cache)
        # for scrapedthumbnail in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 title=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 folder=True))

    # Paginazione 
    patron = r'</span></td>\s*<td>\s*<a href="([^"]+)" class="btn-pag-luce">'
    next_page = scrapertools.find_single_match(data, patron)

    if next_page > 0:
        scrapedurl = urlparse.urljoin(item.url, next_page)
        itemlist.append(
            Item(channel=item.channel,
                 action="cat_results",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))

    return itemlist


def peliculas(item):
    logger.info("kod.istitutoluce peliculas")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    # Estrae i contenuti 
    patron = '<a href="([^"]+)" class="thumbnail">\s*<h1>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl in matches:
        scrapedtitle = scrapedurl
        scrapedtitle = scrapedtitle.rsplit('/', 1)[-1].rsplit(".", 1)[0].replace("-", " ").title()
        scrapedurl = host + scrapedurl

        html = scrapertools.cache_page(scrapedurl)
        start = html.find('<p class="abstract">')
        end = html.find('</p>', start)
        scrapedplot = html[start:end]
        scrapedplot = re.sub(r'<[^>]*>', '', scrapedplot)
        scrapedplot = scrapertools.decodeHtmlentities(scrapedplot)

        html = httptools.downloadpage(scrapedurl, headers=headers).data
        patron = 'image: "(.*?)"'
        scrapedthumbnail = scrapertools.find_single_match(html, patron)

        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 title=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 folder=True))

    # Paginazione 
    patron = r'</span></td>\s*<td>\s*<a href="([^"]+)" class="btn-pag-luce">'
    next_page = scrapertools.find_single_match(data, patron)

    if next_page:
        scrapedurl = urlparse.urljoin(item.url, next_page)
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))

    return itemlist


def peliculas_src(item):
    logger.info("kod.istitutoluce peliculas")
    itemlist = []

    p = 1
    if '{}' in item.url:
        item.url, p = item.url.split('{}')
        p = int(p)

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    # Estrae i contenuti 
    patron = '<a href="([^"]+)" class="thumbnail">\s*<h1>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for i, (scrapedurl) in enumerate(matches):
        if (p - 1) * PERPAGE > i: continue
        if i >= p * PERPAGE: break
        scrapedtitle = scrapedurl
        scrapedtitle = scrapedtitle.rsplit('/', 1)[-1].rsplit(".", 1)[0].replace("-", " ").title()
        scrapedurl = urlparse.urljoin(host, scrapedurl)

        html = httptools.downloadpage(scrapedurl, headers=headers).data
        start = html.find('<p class="abstract">')
        end = html.find('</p>', start)
        scrapedplot = html[start:end]
        scrapedplot = re.sub(r'<[^>]*>', '', scrapedplot)
        scrapedplot = scrapertools.decodeHtmlentities(scrapedplot)

        html = httptools.downloadpage(scrapedurl, headers=headers).data
        patron = 'image: "(.*?)"'
        scrapedthumbnail = scrapertools.find_single_match(html, patron)

        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 title=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 folder=True))

    # Paginazione 
    if len(matches) >= p * PERPAGE:
        scrapedurl = item.url + '{}' + str(p + 1)
        itemlist.append(
            Item(channel=item.channel,
                 extra=item.extra,
                 action="peliculas_src",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))

    return itemlist


def search(item, texto):
    logger.info("[istitutoluce.py] search")

    item.url = host + '/luce-web/search/result.html?archiveType_string="xDamsCineLuce"&archiveName_string="luceFondoCinegiornali"&archiveName_string="luceFondoDocumentari"&archiveName_string="luceFondoRepertori"&titoloADV=&descrizioneADV="' + texto + '"'

    try:
        return peliculas_src(item)

    # Continua la ricerca in caso di errore .
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def findvideos(item):
    logger.info("kod.istitutoluce findvideos")

    data = httptools.downloadpage(item.url, headers=headers).data

    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.title + videoitem.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.show = item.show
        videoitem.plot = item.plot
        videoitem.channel = item.channel

    # Estrae i contenuti 
    patron = 'file: "rtsp:([^"]+)"\s*}'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for video in matches:
        video = "rtsp:" + video
        itemlist.append(
            Item(
                channel=item.channel,
                action="play",
                title=item.title + " [[COLOR orange]Diretto[/COLOR]]",
                url=video,
                folder=False))

    return itemlist

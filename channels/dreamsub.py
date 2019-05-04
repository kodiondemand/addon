# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per dreamsub
# ------------------------------------------------------------
import re, urlparse

from core import scrapertools, httptools, servertools, tmdb
from core.item import Item
from platformcode import logger, config



host = "https://www.dreamsub.co"


def mainlist(item):
    logger.info("kod.dreamsub mainlist")
    itemlist = [Item(channel=item.channel,
                     title="[COLOR azure]Anime / Cartoni[/COLOR]",
                     action="serietv",
                     url="%s/anime" % host,
                     thumbnail="http://orig09.deviantart.net/df5a/f/2014/169/2/a/fist_of_the_north_star_folder_icon_by_minacsky_saya-d7mq8c8.png"),
                Item(channel=item.channel,
                     title="[COLOR azure]Categorie[/COLOR]",
                     action="categorie",
                     url=host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR azure]Ultimi episodi Anime[/COLOR]",
                     action="ultimiep",
                     url=host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR yellow]Cerca...[/COLOR]",
                     action="search",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

    return itemlist


def newest(categoria):
    logger.info("kod.altadefinizione01 newest" + categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "anime":
            item.url = "https://www.dreamsub.tv"
            item.action = "ultimiep"
            itemlist = ultimiep(item)

            if itemlist[-1].action == "ultimiep":
                itemlist.pop()
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def serietv(item):
    logger.info("kod.dreamsub peliculas")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data,
                                    '<input type="submit" value="Vai!" class="blueButton">(.*?)<div class="footer">')

    # Estrae i contenuti 
    patron = 'Lingua[^<]+<br>\s*<a href="([^"]+)" title="([^"]+)">'
    matches = re.compile(patron, re.DOTALL).findall(bloque)

    for scrapedurl, scrapedtitle in matches:
        scrapedurl = host + scrapedurl
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = scrapedtitle.replace("Streaming", "")
        scrapedtitle = scrapedtitle.replace("Lista episodi ", "")
        itemlist.append(
            Item(channel=item.channel,
                 action="episodios",
                 contentType="tvshow",
                 title="[COLOR azure]%s[/COLOR]" % scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 show=scrapedtitle,
                 plot=scrapedplot,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Paginazione 
    patronvideos = '<li class="currentPage">[^>]+><li[^<]+<a href="([^"]+)">'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)

    if len(matches) > 0:
        scrapedurl = urlparse.urljoin(item.url, matches[0])
        itemlist.append(
            Item(channel=item.channel,
                 action="serietv",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))

    return itemlist


def ultimiep(item):
    logger.info("kod.dreamsub ultimiep")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, '<ul class="last" id="recentAddedEpisodesAnimeDDM">(.*?)</ul>')

    # Estrae i contenuti 
    patron = '<li><a href="([^"]+)"[^>]+>([^<]+)<br>'
    matches = re.compile(patron, re.DOTALL).findall(bloque)

    for scrapedurl, scrapedtitle in matches:
        ep = scrapertools.find_single_match(scrapedtitle, r'\d+$').zfill(2)
        scrapedtitle = re.sub(r'\d+$', ep, scrapedtitle)
        scrapedurl = host + scrapedurl
        scrapedplot = ""
        scrapedthumbnail = ""
        cleantitle = re.sub(r'\d*-?\d+$', '', scrapedtitle).strip()
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentType="tvshow",
                 title=scrapedtitle,
                 fulltitle=cleantitle,
                 text_color="azure",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 show=cleantitle,
                 plot=scrapedplot,
                 folder=True))
        
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    for itm in itemlist:
        itm.contentType = "episode"

    return itemlist


def categorie(item):
    logger.info("[dreamsub.py] categorie")
    itemlist = []

    data = httptools.downloadpage(item.url).data
    blocco = scrapertools.find_single_match(data,
                                            r'<select name="genere" id="genere" class="selectInput">(.*?)</select>')
    patron = r'<option value="([^"]+)">'
    matches = re.compile(patron, re.DOTALL).findall(blocco)

    for value in matches:
        url = host + '/filter?genere=' + value
        itemlist.append(
            Item(channel=item.channel,
                 action="serietv",
                 title="[COLOR azure]%s[/COLOR]" % value.capitalize(),
                 url=url,
                 extra="tv",
                 thumbnail=item.thumbnail,
                 folder=True))

    return itemlist

def search(item, texto):
    logger.info("[dreamsub.py] " + item.url + " search " + texto)
    item.url = "%s/search/%s" % (host, texto)
    try:
        return serietv(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def episodios(item):
    logger.info("kod.channels.dreamsub episodios")

    itemlist = []

    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, '<div class="seasonEp">(.*?)<div class="footer">')

    patron = '<li><a href="([^"]+)"[^<]+<b>(.*?)<\/b>[^>]+>([^<]+)<\/i>(.*?)<'
    matches = re.compile(patron, re.DOTALL).findall(bloque)

    for scrapedurl, title1, title2, title3 in matches:
        scrapedurl = host + scrapedurl
        scrapedtitle = title1 + " " + title2 + title3
        scrapedtitle = scrapedtitle.replace("Download", "")
        scrapedtitle = scrapedtitle.replace("Streaming", "")
        scrapedtitle = scrapedtitle.replace("& ", "")
        scrapedtitle = re.sub(r'\s+', ' ', scrapedtitle)

        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentType="episode",
                 fulltitle=scrapedtitle,
                 show=item.show,
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=item.thumbnail,
                 plot=item.plot,
                 folder=True))

    if config.get_videolibrary_support() and len(itemlist) != 0:
        itemlist.append(
            Item(channel=item.channel,
                 title="[COLOR lightblue]%s[/COLOR]" % config.get_localized_string(30161),
                 url=item.url,
                 action="add_serie_to_library",
                 extra="episodios",
                 show=item.show))

    return itemlist


def findvideos(item):
    logger.info()

    print item.url
    data = httptools.downloadpage(item.url).data

    itemlist = servertools.find_video_items(data=data)
    if 'keepem.online' in data:
        urls = scrapertools.find_multiple_matches(data, r'(https://keepem\.online/f/[^"]+)"')
        for url in urls:
            url = httptools.downloadpage(url).url
            itemlist += servertools.find_video_items(data=url)

    for videoitem in itemlist:
        server = re.sub(r'[-\[\]\s]+', '', videoitem.title)
        videoitem.title = "".join(
            ["[[COLOR orange]%s[/COLOR]] " % server.capitalize(), "[COLOR azure]%s[/COLOR]" % item.title])
        videoitem.fulltitle = item.fulltitle
        videoitem.show = item.show
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
        videoitem.contentType = item.contentType

    return itemlist

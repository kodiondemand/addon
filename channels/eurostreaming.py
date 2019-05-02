# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per eurostreaming
# ------------------------------------------------------------
import re, urlparse

from channels import autoplay
from core import scrapertools, httptools, servertools, tmdb, scrapertoolsV2
from core.item import Item
from lib import unshortenit
from platformcode import logger, config
from channelselector import thumb

host = "https://eurostreaming.cafe"
list_servers = ['verystream', 'openload', 'speedvideo', 'wstream', 'streamango' 'flashx', 'nowvideo']
list_quality = ['default']


def mainlist(item):
    logger.info("kod.eurostreaming mainlist")
    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = [
        Item(
            channel=item.channel,
            title="[B]Serie TV[/B]",
            action="serietv",
            extra="tvshow",
            url="%s/category/serie-tv-archive/" % host,
            thumbnail=
            "http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"
        ),
        Item(
            channel=item.channel,
            title="[B]Anime / Cartoni[/B]",
            action="serietv",
            extra="tvshow",
            url="%s/category/anime-cartoni-animati/" % host,
            thumbnail=
            "http://orig09.deviantart.net/df5a/f/2014/169/2/a/fist_of_the_north_star_folder_icon_by_minacsky_saya-d7mq8c8.png"
        ),
        Item(
            channel=item.channel,
            title="[COLOR blue]Cerca...[/COLOR]",
            action="search",
            extra="tvshow",
            thumbnail=
            "http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")
    ]

    autoplay.show_option(item.channel, itemlist)

    itemlist = thumb(itemlist)

    return itemlist


def serietv(item):
    logger.info("kod.eurostreaming peliculas")
    itemlist = []

    # Carica la pagina
    data = httptools.downloadpage(item.url).data

    # Estrae i contenuti
    patron = '<div class="post-thumb">\s*<a href="([^"]+)" title="([^"]+)">\s*<img src="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        scrapedplot = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle.replace("Streaming", ""))
        if scrapedtitle.startswith("Link to "):
            scrapedtitle = scrapedtitle[8:]
        # num = scrapertools.find_single_match(scrapedurl, '(-\d+/)')
        # if num:
        #     scrapedurl = scrapedurl.replace(num, "-episodi/")
        itemlist.append(
            Item(
                 channel=item.channel,
                 action="episodios",
                 contentType="tvshow",
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 text_color="azure",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 show=scrapedtitle,
                 extra=item.extra,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Paginazione
    patronvideos = '<a class="next page-numbers" href="?([^>"]+)">Avanti &raquo;</a>'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)

    if len(matches) > 0:
        scrapedurl = urlparse.urljoin(item.url, matches[0])
        itemlist.append(
            Item(
                channel=item.channel,
                action="serietv",
                title="[COLOR blue]" + config.get_localized_string(30992) + "[/COLOR]",
                url=scrapedurl,
                thumbnail=thumb(),
                extra=item.extra,
                folder=True))

    return itemlist

def search(item, texto):
    logger.info("[eurostreaming.py] " + item.url + " search " + texto)
    item.url = "%s/?s=%s" % (host, texto)
    try:
        return serietv(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def episodios(item):
    def load_episodios(html, item, itemlist, lang_title):
        patron = '((?:.*?<a[^h]+href="[^"]+"[^>]+>[^<][^<]+<(?:b|\/)[^>]+>)+)'
        matches = re.compile(patron).findall(html)
        for data in matches:
            # Estrazione

            scrapedtitle = data.split('<a ')[0]
            scrapedtitle = re.sub(r'<[^>]*>', '', scrapedtitle).strip()
            if scrapedtitle != 'Categorie':
                scrapedtitle = scrapedtitle.replace('&#215;', 'x')
                scrapedtitle = scrapedtitle.replace('×', 'x')
                itemlist.append(
                    Item(channel=item.channel,
                         action="findvideos",
                         contentType="episode",
                         title="[COLOR azure]%s[/COLOR]" % (scrapedtitle + " (" + lang_title + ")"),
                         url=data,
                         thumbnail=item.thumbnail,
                         extra=item.extra,
                         fulltitle=scrapedtitle + " (" + lang_title + ")" + ' - ' + item.show,
                         show=item.show))

    logger.info("[eurostreaming.py] episodios")

    itemlist = []

    # Download pagina
    data = httptools.downloadpage(item.url).data
    data = scrapertools.decodeHtmlentities(data)
    link = False

    if scrapertoolsV2.find_single_match(data, '<div class="nano_cp_container"><span.*?CLICCA QUI'):
        item.url = scrapertoolsV2.find_single_match(data, '<script type="text\/javascript">.*?var nano_ajax_object =.*?"go_to":"(.*?)"').replace('\\', '')
        link = True
    else:
        match = scrapertoolsV2.find_single_match(data, '<h3 style="text-align: center;">.*?<a href="(.*?)">.{0,5}<span.*?CLICCA QUI.*?</a></h3>')
        if match != '':
            item.url = match
            link = True
    if link:
        data = httptools.downloadpage(item.url).data
        data = scrapertools.decodeHtmlentities(data)

    data = scrapertoolsV2.find_single_match(data, '<div class="su-accordion">(.+?)<div class="clear">')

    lang_titles = []
    starts = []
    patron = r"STAGIONE.*?ITA"
    matches = re.compile(patron, re.IGNORECASE).finditer(data)

    for match in matches:
        season_title = match.group()

        if season_title != '':
            lang_titles.append('SUB ITA' if 'SUB' in season_title.upper() else 'ITA')
            starts.append(match.end())

    i = 1
    len_lang_titles = len(lang_titles)

    while i <= len_lang_titles:
        inizio = starts[i - 1]
        fine = starts[i] if i < len_lang_titles else -1

        html = data[inizio:fine]
        lang_title = lang_titles[i - 1]

        load_episodios(html, item, itemlist, lang_title)

        i += 1

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
    logger.info("kod.eurostreaming findvideos")
    itemlist = []

    # Carica la pagina 
    data = item.url

    matches = re.findall(r'<a href="([^"]+)"[^>]*>[^<]+</a>', data, re.DOTALL)

    data = []
    for url in matches:
        url, c = unshortenit.unshorten(url)
        data.append(url)

    itemlist = servertools.find_video_items(data=str(data))

    for videoitem in itemlist:
        videoitem.title = item.title + videoitem.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.show = item.show
        videoitem.plot = item.plot
        videoitem.channel = item.channel
        videoitem.contentType = item.contentType

    autoplay.start(itemlist, item)

    return itemlist

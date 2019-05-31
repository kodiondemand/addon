# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per guardaseriecc
#
# ----------------------------------------------------------
import re

from core import httptools, scrapertools, servertools
from core import tmdb
from core.item import Item
from lib import unshortenit
from platformcode import logger, config

host = 'https://guardaserie.site'
headers = [['Referer', host]]


def mainlist(item):
    logger.info("Alfa.leserietv mainlist")
    itemlist = [Item(channel=item.channel,
                     action="lista_serie",
                     title="[COLOR azure]Tutte le serie[/COLOR]",
                     url="%s/serietv/" % host,
                     thumbnail=thumbnail_lista,
                     fanart=FilmFanart),
                Item(channel=item.channel,
                     title="[COLOR azure]Categorie[/COLOR]",
                     action="categoria",
                     url=host,
                     thumbnail=thumbnail_categoria,
                     fanart=FilmFanart),
                Item(channel=item.channel,
                     action="search",
                     title="[COLOR orange]Cerca...[/COLOR]",
                     thumbnail=thumbnail_cerca,
                     fanart=FilmFanart)]
    return itemlist


def categoria(item):
    logger.info("[Alfa].[guardareseriecc] [categoria]")
    itemlist = []

    patron = '<li class="cat-item cat-item.*?"><a href="(.*?)".*?>(.*?)</a>'
    data = httptools.downloadpage(item.url, headers=headers).data
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(Item(channel=item.channel,
                             action="lista_serie",
                             title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                             url=scrapedurl,
                             thumbnail=item.thumbnail,
                             fulltitle=scrapedtitle,
                             show=scrapedtitle, viewmode="movie"))

    return itemlist


def lista_serie(item):
    logger.info("[Alfa].[guardareseriecc] [lista_serie]")
    itemlist = []
    patron = '<div.*?class="poster">[^<]+<img.*?src="(.*?)".*?alt="(.*?)"[^<]+<[^<]+<[^<]+<[^<]+<[^<]+<[^<]+<[^<]+<a.*?href="(.*?)">'
    data = httptools.downloadpage(item.url, headers=headers).data
    matches = re.compile(patron, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedthumbnail, scrapedtitle, scrapedurl in matches:
        scrapedtitle = scrapedtitle.split("(")[0]
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        itemlist.append(
            Item(channel=item.channel,
                 action="episodios",
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 fulltitle=scrapedtitle,
                 show=scrapedtitle, viewmode="movie"))

    # Paginazione
    # ===========================================================
    patron = 'class="current">.*?</span><a href=\'(.*?)\''
    matches = scrapertools.find_single_match(data, patron)
    logger.debug("pag " + matches)

    # ===========================================================
    if len(matches) > 0:
        itemlist.append(
            Item(channel=item.channel,
                 action="lista_serie",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=matches,
                 thumbnail=thumbnail_successivo,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def episodios(item):
    logger.info("[Alfa].[guardareseriecc] [stagione]")
    itemlist = []

    patron = '<iframe.*class="metaframe rptss".*?src="(.*?)".*?frameborder=".*?".*?scrolling=".*?".*?allowfullscreen>.*?</iframe>'
    data = httptools.downloadpage(item.url, headers=headers).data
    elenco = scrapertools.find_single_match(data, patron)

    patron = '</i>.*?Stagioni</a>.*?</ul>[^<]+<select.*?name="sea_select"'
    data = httptools.downloadpage(elenco, headers=headers).data
    select = scrapertools.find_single_match(data, patron)

    patron = '<a.*?href="(.*?)".*?><i.*?<\/i>(.*?)</a></li>'
    stagione = scrapertools.find_multiple_matches(select, patron)
    scrapertools.printMatches(stagione)

    for stagioneurl, stagionetitle in stagione:
        patron = '</i>.*?Episodio</a>(.*?)<select name="ep_select"'
        data = httptools.downloadpage(stagioneurl, headers=headers).data
        elenco = scrapertools.find_single_match(data, patron, 0)
        patron = '<a href="(.*?)" ><i class="fa.*?"></i>(.*?)</a></li>'
        episodi = scrapertools.find_multiple_matches(elenco, patron)

        for scrapedurl, scrapedtitle in episodi:
            scrapedtitle = stagionetitle + "x" + scrapedtitle.replace(" ", "").zfill(2)
            itemlist.append(Item(channel=item.channel,
                                 action="findvideos",
                                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                                 url=scrapedurl,
                                 thumbnail=item.thumbnail,
                                 fanart=item.fanart,
                                 plot=item.plot,
                                 fulltitle=scrapedtitle,
                                 contentType="episode",
                                 show=scrapedtitle, viewmode="movie"))

    if config.get_videolibrary_support() and len(itemlist) != 0:
        itemlist.append(
            Item(channel=item.channel,
                 title="[COLOR lightblue]%s[/COLOR]" % config.get_localized_string(30161),
                 url=item.url,
                 action="add_serie_to_library",
                 extra="episodios",
                 contentType="episode",
                 show=item.show))

    return itemlist


def findvideos(item):
    logger.info("[Alfa].[guardareseriecc] [findvideos]")
    itemlist = []
    listurl = set()

    patron = r'<select.*?style="width:100px;" class="dynamic_select">(.*?)</select>'
    data = httptools.downloadpage(item.url, headers=headers).data
    elenco = scrapertools.find_single_match(data, patron, 0)

    patron = '<a class="" href="(.*?)">(.*?)</a>'
    elenco_link = scrapertools.find_multiple_matches(elenco, patron)

    for scrapedurl, scrapedtitle in elenco_link:
        data = httptools.downloadpage(scrapedurl, headers=headers).data
        if 'protectlink' in data:
            urls = scrapertools.find_multiple_matches(data, r'<iframe src="[^=]+=(.*?)"')
            for url in urls:
                url = url.decode('base64')
                # tiro via l'ultimo carattere perchè non c'entra
                url = unshortenit.unwrap_30x_only(url[:-1])
                listurl.add(url)

    if listurl:
        itemlist = servertools.find_video_items(data=str(listurl))
        for videoitem in itemlist:
            videoitem.title = item.title + '[COLOR orange][B]' + videoitem.title + '[/B][/COLOR]'
            videoitem.fulltitle = item.fulltitle
            videoitem.thumbnail = item.thumbnail
            videoitem.show = item.show
            videoitem.plot = item.plot
            videoitem.channel = item.channel
            videoitem.contentType = item.contentType

    return itemlist


def search(item, texto):
    logger.info("[Alfa].[guardareseriecc][search] " + texto)

    item.url = host + "/?s=" + texto

    try:
        return ricerca(item)

    # Continua la ricerca in caso di errore .
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def ricerca(item):
    logger.info("[Alfa].[guardareseriecc][ricerca] ")
    itemlist = []

    patron = '<div class="result-item">[^>]+>[^>]+>[^>]+>[^<]+<a href="(.*?)">[^<]+<img src="(.*?)" alt="(.*?)" '
    data = httptools.downloadpage(item.url, headers=headers).data
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        scrapedtitle = scrapedtitle.split("(")[0]
        itemlist.append(
            Item(channel=item.channel,
                 action="episodios",
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 fulltitle=scrapedtitle,
                 show=scrapedtitle, viewmode="movie"))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


FilmFanart = "https://superrepo.org/static/images/fanart/original/script.artwork.downloader.jpg"
ThumbnailHome = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/81/Dynamic-blue-up.svg/580px-Dynamic-blue-up.svg.png"
thumbnail_novita = "http://www.ilmioprofessionista.it/wp-content/uploads/2015/04/TVSeries3.png"
thumbnail_lista = "http://www.ilmioprofessionista.it/wp-content/uploads/2015/04/TVSeries3.png"
thumbnail_categoria = "https://farm8.staticflickr.com/7562/15516589868_13689936d0_o.png"
thumbnail_top = "http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"
thumbnail_cerca = "http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search"
thumbnail_successivo = "http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png"

'''


def search(item, texto):
    logger.info("[Alfa].[guardareseriecc][search] " + texto)
    itemlist = []

    item.url = host + "/?s=" + texto
    patron = '<div class="result-item">[^>]+>[^>]+>[^>]+>[^<]+<a href="(.*?)">[^<]+<img src="(.*?)" alt="(.*?)" '
    data = httptools.downloadpage(item.url, headers=headers).data
    matches = scrapertools.find_multiple_matches(data,patron)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedthumbnail,scrapedtitle  in matches:
        scrapedtitle = scrapedtitle.split("(")[0]
        itemlist.append(
            Item(channel=item.channel,
                 action="stagione",
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 fulltitle=scrapedtitle,
                 show=scrapedtitle, viewmode="movie")))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


'''

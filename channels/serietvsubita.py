# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Serie Tv Sub ITA
# Ringraziamo Icarus crew
# ----------------------------------------------------------
import inspect
import re
import time

import channelselector
from channels import autoplay, support, filtertools
from core import httptools, tmdb, scrapertools
from core.item import Item
from platformcode import logger, config

host = config.get_setting("channel_host", 'serietvsubita')
headers = [['Referer', host]]

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['gounlimited','verystream','streamango','openload']
list_quality = ['default']



def mainlist(item):
    support.log(item.channel + 'mainlist')
    itemlist = []
    support.menu(itemlist, 'Serie TV bold', 'lista_serie', host,'tvshow')
    support.menu(itemlist, 'Novità submenu', 'peliculas_tv', host,'tvshow')
    support.menu(itemlist, 'Archivio A-Z submenu', 'list_az', host,'tvshow')
    support.menu(itemlist, 'Cerca', 'search', host,'tvshow')


    autoplay.init(item.channel, list_servers, list_quality)
    autoplay.show_option(item.channel, itemlist)

    itemlist.append(
        Item(channel='setting',
             action="channel_config",
             title=support.typo("Configurazione Canale color lime"),
             config=item.channel,
             folder=False,
             thumbnail=channelselector.get_thumb('setting_0.png'))
    )

    return itemlist


# ----------------------------------------------------------------------------------------------------------------
def cleantitle(scrapedtitle):
    scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle.strip())
    scrapedtitle = scrapedtitle.replace('[HD]', '').replace('’', '\'').replace('Game of Thrones –','')
    year = scrapertools.find_single_match(scrapedtitle, '\((\d{4})\)')
    if year:
        scrapedtitle = scrapedtitle.replace('(' + year + ')', '')


    return scrapedtitle.strip()


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def lista_serie(item):
    support.log(item.channel + " lista_serie")
    itemlist = []

    PERPAGE = 15

    p = 1
    if '{}' in item.url:
        item.url, p = item.url.split('{}')
        p = int(p)

    # Descarga la pagina
    data = httptools.downloadpage(item.url).data

    # Extrae las entradas
    patron = '<li class="cat-item cat-item-\d+"><a href="([^"]+)" >([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for i, (scrapedurl, scrapedtitle) in enumerate(matches):
        scrapedplot = ""
        scrapedthumbnail = ""
        if (p - 1) * PERPAGE > i: continue
        if i >= p * PERPAGE: break
        title = cleantitle(scrapedtitle)
        itemlist.append(
            Item(channel=item.channel,
                 extra=item.extra,
                 action="episodes",
                 title=title,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 fulltitle=title,
                 show=title,
                 plot=scrapedplot,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Paginazione
    if len(matches) >= p * PERPAGE:
        scrapedurl = item.url + '{}' + str(p + 1)
        itemlist.append(
            Item(channel=item.channel,
                 action='lista_serie',
                 contentType=item.contentType,
                 title=support.typo(config.get_localized_string(30992), 'color kod bold'),
                 url=scrapedurl,
                 args=item.args,
                 thumbnail=support.thumb()))

    return itemlist

# ================================================================================================================


# ----------------------------------------------------------------------------------------------------------------
def episodes(item):
    support.log(item.channel + " episodes")
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = '<div class="post-meta">\s*<a href="([^"]+)"\s*title="([^"]+)"\s*class=".*?"></a>.*?'
    patron += '<p><a href="([^"]+)">'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        scrapedplot = ""
        scrapedtitle = cleantitle(scrapedtitle)
        title = scrapedtitle.split(" S0")[0].strip()
        title = title.split(" S1")[0].strip()
        title = title.split(" S2")[0].strip()

        itemlist.append(
            Item(channel=item.channel,
                 extra=item.extra,
                 action="findvideos",
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 title=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 contentSerieName=title,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Paginazionazione
    patron = '<strong class=\'on\'>\d+</strong>\s*<a href="([^<]+)">\d+</a>'
    next_page = scrapertools.find_single_match(data, patron)
    if next_page != "":
        itemlist.append(
            Item(channel=item.channel,
                 action='episodes',
                 contentType=item.contentType,
                 title=support.typo(config.get_localized_string(30992), 'color kod bold'),
                 url=next_page,
                 args=item.args,
                 thumbnail=support.thumb()))

    # support.videolibrary(itemlist,item,'bold color kod')

    return itemlist

# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def findvideos(item):
    support.log(item.channel + " findvideos")

    data = httptools.downloadpage(item.url).data

    patron = 'href="(https?://www\.keeplinks\.(?:co|eu)/p(?:[0-9]*)/([^"]+))"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for keeplinks, id in matches:
        headers = [['Cookie', 'flag[' + id + ']=1; defaults=1; nopopatall=' + str(int(time.time()))],
                   ['Referer', keeplinks]]

        html = httptools.downloadpage(keeplinks, headers=headers).data
        data += str(scrapertools.find_multiple_matches(html, '</lable><a href="([^"]+)" target="_blank"'))

    itemlist = support.server(item, data=data)
    itemlist = filtertools.get_links(itemlist, item, list_language)

    autoplay.start(itemlist, item)

    return itemlist

# ================================================================================================================


# ----------------------------------------------------------------------------------------------------------------
def peliculas_tv(item):
    logger.info("icarus serietvsubita peliculas_tv")
    itemlist = []

    data = httptools.downloadpage(item.url).data
    logger.debug(data)
    patron = '<div class="post-meta">\s*<a href="([^"]+)"\s*title="([^"]+)"\s*class=".*?"></a>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        if "FACEBOOK" in scrapedtitle or "RAPIDGATOR" in scrapedtitle:
            continue
        if scrapedtitle == "WELCOME!":
            continue
        scrapedthumbnail = ""
        scrapedplot = ""
        scrapedtitle = cleantitle(scrapedtitle)
        title = scrapedtitle.split(" S0")[0].strip()
        title = title.split(" S1")[0].strip()
        title = title.split(" S2")[0].strip()
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 title=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 contentSerieName=title,
                 plot=scrapedplot,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)


    # Paginazione
    patron = '<strong class=\'on\'>\d+</strong>\s*<a href="([^<]+)">\d+</a>'
    next_page = scrapertools.find_single_match(data, patron)
    if next_page != "":
        if item.extra == "search_tv":
            next_page = next_page.replace('&#038;', '&')
        itemlist.append(
            Item(channel=item.channel,
                 action='peliculas_tv',
                 contentType=item.contentType,
                 title=support.typo(config.get_localized_string(30992), 'color kod bold'),
                 url=next_page,
                 args=item.args,
                 extra=item.extra,
                 thumbnail=support.thumb()))


    return itemlist


# ================================================================================================================



# ----------------------------------------------------------------------------------------------------------------
def newest(categoria):
    logger.info('serietvsubita' + " newest" + categoria)
    itemlist = []
    item = Item()
    item.url = host;
    item.extra = 'serie';
    try:
        if categoria == "series":
            itemlist = peliculas_tv(item)

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def search(item, texto):
    logger.info(item.channel + " search")
    itemlist = []
    item.extra = "search_tv"

    item.url = host + "/?s=" + texto + "&op.x=0&op.y=0"

    try:
        return peliculas_tv(item)

    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def list_az(item):
    support.log(item.channel+" list_az")
    itemlist = []
    PERPAGE = 50

    p = 1
    if '{}' in item.url:
        item.url, p = item.url.split('{}')
        p = int(p)

    # Scarico la pagina
    data = httptools.downloadpage(item.url).data

    # Articoli
    patron = '<li class="cat-item cat-item-\d+"><a href="([^"]+)" >([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for i, (scrapedurl, scrapedtitle) in enumerate(matches):
        scrapedplot = ""
        scrapedthumbnail = ""
        if (p - 1) * PERPAGE > i: continue
        if i >= p * PERPAGE: break
        title = cleantitle(scrapedtitle)
        itemlist.append(
            Item(channel=item.channel,
                 extra=item.extra,
                 action="episodes",
                 title=title,
                 url=scrapedurl,
                 fulltitle=title,
                 show=title,
                 plot=scrapedplot,
                 folder=True))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Paginazione
    if len(matches) >= p * PERPAGE:
        scrapedurl = item.url + '{}' + str(p + 1)
        itemlist.append(
            Item(channel=item.channel,
                 action='list_az',
                 contentType=item.contentType,
                 title=support.typo(config.get_localized_string(30992), 'color kod bold'),
                 url=scrapedurl,
                 args=item.args,
                 extra=item.extra,
                 thumbnail=support.thumb()))

    return itemlist

# ================================================================================================================

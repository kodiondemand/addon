# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per AnimeSaturn
# Thanks to me
# ----------------------------------------------------------
import inspect
import re
import time

import channelselector
from channels import autoplay, support, filtertools
from core import httptools, tmdb, scrapertools, servertools
from core.item import Item
from platformcode import logger, config
__channel__ = "animesaturn"
host = config.get_setting("channel_host", __channel__)
headers = [['Referer', host]]

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['openload','fembed']
list_quality = ['default']

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', __channel__)
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', __channel__)


def mainlist(item):
    support.log(item.channel + 'mainlist')
    itemlist = []
    support.menu(itemlist, 'Anime bold', 'lista_serie',  "%sanimelist?load_all=1" % host,'anime')
    support.menu(itemlist, 'Novità submenu', 'peliculas_tv', "%s/animelist?load_all=1" % host,'anime')
    itemlist.append(
        Item(channel=item.channel,
             action="peliculas_tv",
             url="%sanimelist?load_all=1" % host,
             title=support.typo("In corso submenu"),
             extra="anime",
             contentType='anime',
             folder=True,
             thumbnail=channelselector.get_thumb('on_the_air.png'))
    )
    itemlist.append(
        Item(channel=item.channel,
             action="lista_serie",
             url="%sanimelist?load_all=1" % host,
             title=support.typo("Archivio A-Z submenu"),
             extra="anime",
             contentType='anime',
             folder=True,
             thumbnail=channelselector.get_thumb('channels_tvshow_az.png'))
    )
    support.menu(itemlist, 'Cerca', 'search', host,'anime')


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
    scrapedtitle = scrapedtitle.replace('[HD]', '').replace('’', '\'').replace('×','x')
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
    patron = r'<a href="([^"]*)"[^>]+><[^>]+>([^<]+)</span>'
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
                 action="episodios",
                 title=title,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 fulltitle=title,
                 show=title,
                 plot=scrapedplot,
                 contentType='episode',
                 originalUrl=scrapedurl,
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
def episodios(item):
    support.log(item.channel + " episodios")
    itemlist = []

    data = httptools.downloadpage(item.url).data

    id = scrapertools.find_single_match(data,"<meta content='(\d*)' itemprop='postId'/>")

    data = httptools.downloadpage("%loading_anime?anime_id=%s" % host, id).data




    patron = '<div class="post-meta">\s*<a href="([^"]+)"\s*title="([^"]+)"\s*class=".*?"></a>.*?'
    patron += '<p><a href="([^"]+)">'

    matches = re.compile(patron, re.DOTALL).findall(data)
    # logger.debug(itemlist)
    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        scrapedplot = ""
        scrapedtitle = cleantitle(scrapedtitle)
        infoLabels = {}

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
                 contentSerieName=scrapedtitle,
                 infoLabels=infoLabels,
                 folder=True))

    # tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # support.videolibrary(itemlist,item,'bold color kod')

    return itemlist

# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def findvideos(item):
    support.log(item.channel + " findvideos")

    data = httptools.downloadpage(item.url).data

    # recupero il blocco contenente i link
    blocco = scrapertools.find_single_match(data,'<div class="entry">[\s\S.]*?<div class="post')
    # logger.debug(item);

    episodio = item.title.replace(str(item.contentSeason)+"x",'')
    patron = r'\.\.:: Episodio %s([\s\S]*?)(<div class="post|..:: Episodio)' % episodio
    matches = re.compile(patron, re.DOTALL).findall(data)
    if len(matches):
        data = matches[0][0]

    patron = 'href="(https?://www\.keeplinks\.(?:co|eu)/p(?:[0-9]*)/([^"]+))"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for keeplinks, id in matches:
        headers = [['Cookie', 'flag[' + id + ']=1; defaults=1; nopopatall=' + str(int(time.time()))],
                   ['Referer', keeplinks]]

        html = httptools.downloadpage(keeplinks, headers=headers).data
        data += str(scrapertools.find_multiple_matches(html, '</lable><a href="([^"]+)" target="_blank"'))

    itemlist = support.server(item, data=data)
    # itemlist = filtertools.get_links(itemlist, item, list_language)


    # Controlla se i link sono validi
    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)

    autoplay.start(itemlist, item)

    return itemlist

# ================================================================================================================


# ----------------------------------------------------------------------------------------------------------------
def peliculas_tv(item):
    logger.info(item.channel+" peliculas_tv")
    itemlist = []

    data = httptools.downloadpage(item.url).data
    # logger.debug(data)
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
    logger.info(__channel__ + " newest" + categoria)
    itemlist = []
    item = Item()
    item.url = host
    item.extra = 'serie'
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

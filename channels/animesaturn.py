# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per AnimeSaturn
# Thanks to me
# ----------------------------------------------------------
import inspect
import re
import time
import urlparse

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
    support.menu(itemlist, 'Anime bold', 'lista_anime',  "%s/animelist?load_all=1" % host,'anime')
    support.menu(itemlist, 'Novità submenu', 'peliculas_tv', "%s/animelist?load_all=1" % host,'anime')
    itemlist.append(
        Item(channel=item.channel,
             action="peliculas_tv",
             url="%s/animelist?load_all=1" % host,
             title=support.typo("In corso submenu"),
             extra="anime",
             contentType='anime',
             folder=True,
             thumbnail=channelselector.get_thumb('on_the_air.png'))
    )
    itemlist.append(
        Item(channel=item.channel,
             action="lista_serie",
             url="%s/animelist?load_all=1" % host,
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
def lista_anime(item):
    support.log(item.channel + " lista_anime")
    itemlist = []

    PERPAGE = 15

    p = 1
    if '{}' in item.url:
        item.url, p = item.url.split('{}')
        p = int(p)

    # Carica la pagina
    data = httptools.downloadpage(item.url).data

    # Estrae i contenuti
    patron = r'<a href="([^"]+)"[^>]*?>[^>]*?>(.+?)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    scrapedplot = ""
    scrapedthumbnail = ""
    for i, (scrapedurl, scrapedtitle) in enumerate(matches):
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

    anime_id = scrapertools.find_single_match(data, r'\?anime_id=(\d+)')

    data = httptools.downloadpage(
        host + "/loading_anime?anime_id=" + anime_id,
        headers={
            'X-Requested-With': 'XMLHttpRequest'
        }).data

    patron = r'<td style="[^"]+"><b><strong" style="[^"]+">(.+?)</b></strong></td>\s*'
    patron += r'<td style="[^"]+"><a href="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedtitle, scrapedurl in matches:
        scrapedtitle = cleantitle(scrapedtitle)
        scrapedtitle = re.sub(r'<[^>]*?>', '', scrapedtitle)
        scrapedtitle = '[COLOR azure][B]' + scrapedtitle + '[/B][/COLOR]'
        itemlist.append(
            Item(
                channel=item.channel,
                action="findvideos",
                contentType="episode",
                title=scrapedtitle,
                url=urlparse.urljoin(host, scrapedurl),
                fulltitle=scrapedtitle,
                show=scrapedtitle,
                plot=item.plot,
                fanart=item.thumbnail,
                thumbnail=item.thumbnail))


    # tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # support.videolibrary(itemlist,item,'bold color kod')

    return itemlist

# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def findvideos(item):
    support.log(item.channel + " findvideos")
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = r'<a href="([^"]+)"><div class="downloadestreaming">'
    url = scrapertools.find_single_match(data, patron)

    data = httptools.downloadpage(url).data
    patron = r"""<source\s*src=(?:"|')([^"']+?)(?:"|')\s*type=(?:"|')video/mp4(?:"|')>"""
    matches = re.compile(patron, re.DOTALL).findall(data)
    for video in matches:
        itemlist.append(
            Item(
                channel=item.channel,
                action="play",
                fulltitle=item.fulltitle,
                title="".join([item.title, ' ', support.typo(video.title, 'color kod []')]),
                url=video,
                contentType=item.contentType,
                folder=False))

    itemlist = support.server(item, data=data)
    # itemlist = filtertools.get_links(itemlist, item, list_language)


    # Controlla se i link sono validi
    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)

    autoplay.start(itemlist, item)

    return itemlist

# ================================================================================================================


# ----------------------------------------------------------------------------------------------------------------

def ultimiep(item):
    logger.info(item.channel + "ultimiep")
    itemlist = []

    post = "page=%s" % item.extra if item.extra else None

    data = httptools.downloadpage(
        item.url, post=post, headers={
            'X-Requested-With': 'XMLHttpRequest'
        }).data

    patron = r"""<a href='[^']+'><div class="locandina"><img alt="[^"]+" src="([^"]+)" title="[^"]+" class="grandezza"></div></a>\s*"""
    patron += r"""<a href='([^']+)'><div class="testo">(.+?)</div></a>\s*"""
    patron += r"""<a href='[^']+'><div class="testo2">(.+?)</div></a>"""
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedurl, scrapedtitle1, scrapedtitle2 in matches:
        scrapedtitle1 = scrapertools.decodeHtmlentities(scrapedtitle1)
        scrapedtitle2 = scrapertools.decodeHtmlentities(scrapedtitle2)
        scrapedtitle = scrapedtitle1 + ' - [COLOR azure]' + scrapedtitle2 + '[/COLOR]'
        itemlist.append(
            Item(channel=item.channel,
                 contentType="tvshow",
                 action="findvideos",
                 title=scrapedtitle,
                 url=scrapedurl,
                 fulltitle=scrapedtitle1,
                 show=scrapedtitle1,
                 thumbnail=scrapedthumbnail))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Pagine
    patronvideos = r'data-page="(\d+)" title="Next">Pagina Successiva'
    next_page = scrapertools.find_single_match(data, patronvideos)

    if next_page:
        itemlist.append(
            Item(
                channel=item.channel,
                action="ultimiep",
                title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                url=host + "/fetch_pages?request=episodes",
                thumbnail=
                "http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                extra=next_page,
                folder=True))

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
        if categoria == "anime":
            item.url = "%s/fetch_pages?request=episodes" % host
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


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def search_anime(item):
    logger.info(item.channel + " search_anime")
    itemlist = []

    data = httptools.downloadpage(host + "/animelist?load_all=1").data
    data = scrapertools.decodeHtmlentities(data)

    texto = item.url.lower().split('+')

    patron = r'<a href="([^"]+)"[^>]*?>[^>]*?>(.+?)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in [(scrapedurl, scrapedtitle)
                                     for scrapedurl, scrapedtitle in matches
                                     if all(t in scrapedtitle.lower()
                                            for t in texto)]:
        itemlist.append(
            Item(
                channel=item.channel,
                contentType="tvshow",
                action="episodios",
                title=scrapedtitle,
                url=scrapedurl,
                fulltitle=scrapedtitle,
                show=scrapedtitle,
                thumbnail=""))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def search(item, texto):
    logger.info(item.channel + " search")
    itemlist = []
    item.url = texto

    try:
        return search_anime(item)

    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


# ================================================================================================================

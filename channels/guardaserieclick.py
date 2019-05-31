# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per guardaserie.click
# Thanks to Icarus crew & Alfa addon
# ------------------------------------------------------------

import re

import channelselector
from core import httptools, scrapertools, servertools, support
from core import tmdb
from core.item import Item
from platformcode import logger, config
from specials import autoplay

__channel__ = 'guardaserieclick'
host = config.get_setting("channel_host", __channel__)
headers = [['Referer', host]]

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['speedvideo','openload']
list_quality = ['default']

headers = [['Referer', host]]


# ----------------------------------------------------------------------------------------------------------------
def mainlist(item):
    support.log(item.channel+" mainlist")

    itemlist = []
    # support.menu(itemlist, 'Serie TV bold')
    support.menu(itemlist, 'Novità bold', 'serietvaggiornate', "%s/lista-serie-tv" % host,'tvshow')
    support.menu(itemlist, 'Nuove serie', 'nuoveserie', "%s/lista-serie-tv" % host,'tvshow')
    support.menu(itemlist, 'Serie inedite Sub-ITA', 'nuoveserie', "%s/lista-serie-tv" % host,'tvshow',args=['inedite'])
    support.menu(itemlist, 'Da non perdere bold', 'nuoveserie', "%s/lista-serie-tv" % host,'tvshow',args=['tv','da non perdere'])
    support.menu(itemlist, 'Classiche bold', 'nuoveserie', "%s/lista-serie-tv" % host,'tvshow',args=['tv','classiche'])
    support.menu(itemlist, 'Anime', 'lista_serie', "%s/category/animazione/" % host,'tvshow')
    support.menu(itemlist, 'Categorie', 'categorie', host,'tvshow',args=['serie'])
    support.menu(itemlist, 'Cerca', 'search', host,'tvshow',args=['serie'])

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


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def newest(categoria):
    support.log(__channel__+" newest" + categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "series":
            item.url = "%s/lista-serie-tv" % host
            item.action = "serietvaggiornate"
            itemlist = serietvaggiornate(item)

            if itemlist[-1].action == "serietvaggiornate":
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
def search(item, texto):
    support.log(item.channel+" search")
    item.url = host + "/?s=" + texto
    try:
        return lista_serie(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


# ================================================================================================================
# ----------------------------------------------------------------------------------------------------------------
def cleantitle(scrapedtitle):
    scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle.strip()).replace('"',"'")

    return scrapedtitle.strip()


# ================================================================================================================
# ----------------------------------------------------------------------------------------------------------------
def nuoveserie(item):
    support.log(item.channel+" nuoveserie")
    itemlist = []

    patron_block = ''
    if 'inedite' in item.args:
        patron_block = r'<div\s*class="container container-title-serie-ined container-scheda" meta-slug="ined">(.*?)</div></div><div'
    elif 'da non perder' in item.args:
        patron_block = r'<div\s*class="container container-title-serie-danonperd container-scheda" meta-slug="danonperd">(.*?)</div></div><div'
    elif 'classiche' in item.args:
        patron_block = r'<div\s*class="container container-title-serie-classiche container-scheda" meta-slug="classiche">(.*?)</div></div><div'
    else:
        patron_block = r'<div\s*class="container container-title-serie-new container-scheda" meta-slug="new">(.*?)</div></div><div'

    patron = r'<a\s*href="([^"]+)".*?>\s*<img\s*.*?src="([^"]+)" />[^>]+>[^>]+>[^>]+>[^>]+>'
    patron += r'[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)</p>'

    matches = support.match(item, patron, patron_block, headers)[0]

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        scrapedtitle = cleantitle(scrapedtitle)

        itemlist.append(
            Item(channel=item.channel,
                 action="episodios",
                 contentType="episode",
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 show=scrapedtitle,
                 thumbnail=scrapedthumbnail,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def serietvaggiornate(item):
    support.log(item.channel+" serietvaggiornate")
    itemlist = []

    patron_block = r'<div\s*class="container container-title-serie-lastep  container-scheda" meta-slug="lastep">(.*?)</div></div><div'
    patron = r'<a\s*rel="nofollow" href="([^"]+)"[^>]+> <img\s*.*?src="([^"]+)"[^>]+>[^>]+>'
    patron += r'[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)<[^>]+>'

    matches = support.match(item,patron, patron_block, headers)[0]

    for scrapedurl, scrapedthumbnail, scrapedep, scrapedtitle in matches:
        episode = re.compile(r'^(\d+)x(\d+)', re.DOTALL).findall(scrapedep)  # Prendo stagione ed episodioso
        scrapedtitle = cleantitle(scrapedtitle)

        contentlanguage = ""
        if 'sub-ita' in scrapedep.strip().lower():
            contentlanguage = 'Sub-ITA'

        extra = r'<span\s*.*?meta-stag="%s" meta-ep="%s" meta-embed="([^"]+)"\s*.*?embed2="([^"]+)?"\s*.*?embed3="([^"]+)?"[^>]*>' % (
            episode[0][0], episode[0][1].lstrip("0"))

        infoLabels = {}
        infoLabels['episode'] = episode[0][1].lstrip("0")
        infoLabels['season'] = episode[0][0]

        title = str("%s - %sx%s %s" % (scrapedtitle,infoLabels['season'],infoLabels['episode'],contentlanguage)).strip()

        itemlist.append(
            Item(channel=item.channel,
                 action="findepvideos",
                 contentType="episode",
                 title=title,
                 show=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 extra=extra,
                 thumbnail=scrapedthumbnail,
                 contentLanguage=contentlanguage,
                 infoLabels=infoLabels,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def categorie(item):
    support.log(item.channel+" categorie")
    itemlist = []

    matches = support.match(item, r'<li>\s*<a\s*href="([^"]+)"[^>]+>([^<]+)</a></li>', r'<ul\s*class="dropdown-menu category">(.*?)</ul>', headers)[0]

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action="lista_serie",
                 title=scrapedtitle,
                 contentType="tvshow",
                 url="".join([host, scrapedurl]),
                 thumbnail=item.thumbnail,
                 extra="tv",
                 folder=True))

    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def lista_serie(item):
    support.log(item.channel+" lista_serie")
    itemlist = []

    # data = httptools.downloadpage(item.url, headers=headers).data
    #
    # patron = r'<a\s*href="([^"]+)".*?>\s*<img\s*.*?src="([^"]+)" />[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)</p></div>'
    # blocco = scrapertools.find_single_match(data,
    #                                 r'<div\s*class="col-xs-\d+ col-sm-\d+-\d+">(.*?)<div\s*class="container-fluid whitebg" style="">')
    # matches = re.compile(patron, re.DOTALL).findall(blocco)

    patron_block = r'<div\s*class="col-xs-\d+ col-sm-\d+-\d+">(.*?)<div\s*class="container-fluid whitebg" style="">'
    patron = r'<a\s*href="([^"]+)".*?>\s*<img\s*.*?src="([^"]+)" />[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)</p></div>'

    matches, data = support.match(item, patron, patron_block, headers)


    for scrapedurl, scrapedimg, scrapedtitle in matches:
        scrapedtitle = cleantitle(scrapedtitle)

        if scrapedtitle not in ['DMCA','Contatti','Lista di tutte le serie tv']:
            itemlist.append(
                Item(channel=item.channel,
                     action="episodios",
                     contentType="episode",
                     title=scrapedtitle,
                     fulltitle=scrapedtitle,
                     url=scrapedurl,
                     thumbnail=scrapedimg,
                     extra=item.extra,
                     show=scrapedtitle,
                     folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    support.nextPage(itemlist,item,data,r"<link\s.*?rel='next'\shref='([^']*)'")

    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def episodios(item):
    support.log(item.channel+" episodios")
    itemlist = []

    # data = httptools.downloadpage(item.url, headers=headers).data

    patron = r'<div\s*class="[^"]+">\s*([^<]+)<\/div>[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)?[^>]+>[^>]+>[^>]+>[^>]+>[^>]+><p[^>]+>([^<]+)<[^>]+>[^>]+>[^>]+>'
    patron += r'[^<]+[^"]+".*?serie="([^"]+)".*?stag="([0-9]*)".*?ep="([0-9]*)"\s*'
    patron += r'.*?embed="([^"]+)"\s*.*?embed2="([^"]+)?"\s*.*?embed3="([^"]+)?"?[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s*'
    patron += r'(?:<img\s*class="[^"]+" meta-src="([^"]+)"[^>]+>|<img\s*class="[^"]+" src="" data-original="([^"]+)"[^>]+>)?'
    # matches = re.compile(patron, re.DOTALL).findall(data)

    # logger.debug(matches)

    matches = support.match(item, patron, headers=headers)[0]


    for scrapedtitle, scrapedepisodetitle, scrapedplot, scrapedserie, scrapedseason, scrapedepisode, scrapedurl, scrapedurl2,scrapedurl3,scrapedthumbnail,scrapedthumbnail2 in matches:
        scrapedtitle = cleantitle(scrapedtitle)
        scrapedepisode = scrapedepisode.zfill(2)
        scrapedepisodetitle = cleantitle(scrapedepisodetitle)
        title = str("%sx%s %s" % (scrapedseason, scrapedepisode, scrapedepisodetitle)).strip()
        if 'SUB-ITA' in scrapedtitle:
            title +=" Sub-ITA"

        infoLabels = {}
        infoLabels['season'] = scrapedseason
        infoLabels['episode'] = scrapedepisode
        itemlist.append(
                Item(channel=item.channel,
                     action="findvideos",
                     title=title,
                     fulltitle=scrapedtitle,
                     url=scrapedurl+"\r\n"+scrapedurl2+"\r\n"+scrapedurl3,
                     contentType="episode",
                     plot=scrapedplot,
                     contentSerieName=scrapedserie,
                     contentLanguage='Sub-ITA' if 'Sub-ITA' in title else '',
                     infoLabels=infoLabels,
                     thumbnail=scrapedthumbnail2 if scrapedthumbnail2 != '' else scrapedthumbnail,
                     folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    support.videolibrary(itemlist, item)

    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def findepvideos(item):
    support.log(item.channel+" findepvideos")
    data = httptools.downloadpage(item.url, headers=headers).data
    matches = scrapertools.find_multiple_matches(data, item.extra)
    data = "\r\n".join(matches[0])
    item.contentType = 'movie'
    itemlist = support.server(item, data=data)

    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def findvideos(item):
    support.log(item.channel+" findvideos")
    logger.debug(item.url)
    itemlist = support.server(item, data=item.url)

    return itemlist

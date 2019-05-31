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
from core.support import log
from platformcode import logger, config
from specials import autoplay

__channel__ = 'guardaserieclick'
host = config.get_setting("channel_host", __channel__)
headers = [['Referer', host]]

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['speedvideo', 'openload']
list_quality = ['default']

headers = [['Referer', host]]


# ----------------------------------------------------------------------------------------------------------------
def mainlist(item):
    log()

    itemlist = []

    support.menu(itemlist, 'Novità bold', 'serietvaggiornate', "%s/lista-serie-tv" % host, 'tvshow')
    support.menu(itemlist, 'Nuove serie', 'nuoveserie', "%s/lista-serie-tv" % host, 'tvshow')
    support.menu(itemlist, 'Serie inedite Sub-ITA', 'nuoveserie', "%s/lista-serie-tv" % host, 'tvshow', args=['inedite'])
    support.menu(itemlist, 'Da non perdere bold', 'nuoveserie', "%s/lista-serie-tv" % host, 'tvshow', args=['tv', 'da non perdere'])
    support.menu(itemlist, 'Classiche bold', 'nuoveserie', "%s/lista-serie-tv" % host, 'tvshow', args=['tv', 'classiche'])
    support.menu(itemlist, 'Anime', 'lista_serie', "%s/category/animazione/" % host, 'tvshow')
    support.menu(itemlist, 'Categorie', 'categorie', host, 'tvshow', args=['serie'])
    support.menu(itemlist, 'Cerca', 'search', host, 'tvshow', args=['serie'])
    support.aplay(item, itemlist, list_servers, list_quality)
    support.channel_config(item, itemlist)

    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def newest(categoria):
    log()
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
    log(texto)
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
    scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle.strip()).replace('"', "'")
    return scrapedtitle.strip()


# ================================================================================================================
# ----------------------------------------------------------------------------------------------------------------
def nuoveserie(item):
    log()
    itemlist = []

    patron_block = ''
    if 'inedite' in item.args:
        patron_block = r'<div\sclass="container container-title-serie-ined container-scheda" meta-slug="ined">(.*?)</div></div><div'
    elif 'da non perdere' in item.args:
        patron_block = r'<div\sclass="container container-title-serie-danonperd container-scheda" meta-slug="danonperd">(.*?)</div></div><div'
    elif 'classiche' in item.args:
        patron_block = r'<div\sclass="container container-title-serie-classiche container-scheda" meta-slug="classiche">(.*?)</div></div><div'
    else:
        patron_block = r'<div\sclass="container container-title-serie-new container-scheda" meta-slug="new">(.*?)</div></div><div'

    patron = r'<a\shref="([^"]+)".*?>\s<img\s.*?src="([^"]+)" />[^>]+>[^>]+>[^>]+>[^>]+>'
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
    log()
    itemlist = []

    patron_block = r'<div\sclass="container container-title-serie-lastep container-scheda" meta-slug="lastep">(.*?)</div></div><div'
    patron = r'<a\srel="nofollow" href="([^"]+)"[^>]+> <img\s*.*?src="([^"]+)"[^>]+>[^>]+>'
    patron += r'[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)<[^>]+>'

    matches = support.match(item, patron, patron_block, headers)[0]

    for scrapedurl, scrapedthumbnail, scrapedep, scrapedtitle in matches:
        episode = re.compile(r'^(\d+)x(\d+)', re.DOTALL).findall(scrapedep)  # Prendo stagione ed episodioso
        scrapedtitle = cleantitle(scrapedtitle)

        contentlanguage = ""
        if 'sub-ita' in scrapedep.strip().lower():
            contentlanguage = 'Sub-ITA'

        extra = r'<span\s.*?meta-stag="%s" meta-ep="%s" meta-embed="([^"]+)"\s.*?embed2="([^"]+)?"\s.*?embed3="([^"]+)?"[^>]*>' % (
            episode[0][0], episode[0][1].lstrip("0"))

        infoLabels = {}
        infoLabels['episode'] = episode[0][1].zfill(2)
        infoLabels['season'] = episode[0][0]

        title = str(
            "%s - %sx%s %s" % (scrapedtitle, infoLabels['season'], infoLabels['episode'], contentlanguage)).strip()

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
    log()
    return support.scrape(item, r'<li>\s<a\shref="([^"]+)"[^>]+>([^<]+)</a></li>', ['url', 'title'], patron_block=r'<ul\sclass="dropdown-menu category">(.*?)</ul>', headers=headers, action="lista_serie")


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def lista_serie(item):
    log()
    itemlist = []

    patron_block = r'<div\sclass="col-xs-\d+ col-sm-\d+-\d+">(.*?)<div\sclass="container-fluid whitebg" style="">'
    patron = r'<a\shref="([^"]+)".*?>\s<img\s.*?src="([^"]+)" />[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)</p></div>'

    matches, data = support.match(item, patron, patron_block, headers)

    for scrapedurl, scrapedimg, scrapedtitle in matches:
        scrapedtitle = cleantitle(scrapedtitle)

        if scrapedtitle not in ['DMCA', 'Contatti', 'Lista di tutte le serie tv']:
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

    support.nextPage(itemlist, item, data, r"<link\s.*?rel='next'\shref='([^']*)'")

    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def episodios(item):
    log()
    itemlist = []

    patron = r'<div\sclass="[^"]+">\s([^<]+)<\/div>[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)?[^>]+>[^>]+>[^>]+>[^>]+>[^>]+><p[^>]+>([^<]+)<[^>]+>[^>]+>[^>]+>'
    patron += r'[^<]+[^"]+".*?serie="([^"]+)".*?stag="([0-9]*)".*?ep="([0-9]*)"\s'
    patron += r'.*?embed="([^"]+)"\s.*?embed2="([^"]+)?"\s.*?embed3="([^"]+)?"?[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s?'
    patron += r'(?:<img\sclass="[^"]+" meta-src="([^"]+)"[^>]+>|<img\sclass="[^"]+" src="" data-original="([^"]+)"[^>]+>)?'

    matches = support.match(item, patron, headers=headers)[0]

    for scrapedtitle, scrapedepisodetitle, scrapedplot, scrapedserie, scrapedseason, scrapedepisode, scrapedurl, scrapedurl2, scrapedurl3, scrapedthumbnail, scrapedthumbnail2 in matches:
        scrapedtitle = cleantitle(scrapedtitle)
        scrapedepisode = scrapedepisode.zfill(2)
        scrapedepisodetitle = cleantitle(scrapedepisodetitle)
        title = str("%sx%s %s" % (scrapedseason, scrapedepisode, scrapedepisodetitle)).strip()
        if 'SUB-ITA' in scrapedtitle:
            title += " Sub-ITA"

        infoLabels = {}
        infoLabels['season'] = scrapedseason
        infoLabels['episode'] = scrapedepisode
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 title=title,
                 fulltitle=scrapedtitle,
                 url=scrapedurl + "\r\n" + scrapedurl2 + "\r\n" + scrapedurl3,
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
    log()
    data = httptools.downloadpage(item.url, headers=headers).data
    matches = scrapertools.find_multiple_matches(data, item.extra)
    data = "\r\n".join(matches[0])
    item.contentType = 'movie'
    return support.server(item, data=data)


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def findvideos(item):
    log()
    logger.debug(item.url)
    return support.server(item, data=item.url)

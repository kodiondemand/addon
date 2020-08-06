# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Serietvsubita
# Thanks to Icarus crew & Alfa addon & 4l3x87
# ----------------------------------------------------------

import re
import time

from core import httptools, tmdb, scrapertools, support
from core.item import Item
from core.support import log
from platformcode import logger, config

host = config.get_channel_url()
headers = [['Referer', host]]

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()



@support.menu
def mainlist(item):
    log()
    itemlist = []
    tvshowSub = [
        ('Novità {bold}',[ '', 'peliculas_tv', '', 'tvshow']),
        ('Serie TV {bold}',[ '', 'lista_serie', '', 'tvshow']),
        ('Per Lettera', ['', 'list_az', 'serie', 'tvshow'])
    ]
    cerca = [(support.typo('Cerca...', 'bold'),[ '', 'search', '', 'tvshow'])]
##    support.aplay(item, itemlist, list_servers, list_quality)
##    support.channel_config(item, itemlist)

    return locals()



# ----------------------------------------------------------------------------------------------------------------
def cleantitle(scrapedtitle):
    scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle.strip())
    scrapedtitle = scrapedtitle.replace('[HD]', '').replace('’', '\'').replace('×', 'x').replace('Game of Thrones –','')\
        .replace('In The Dark 2019', 'In The Dark (2019)').replace('"', "'").strip()
    year = scrapertools.find_single_match(scrapedtitle, r'\((\d{4})\)')
    if year:
        scrapedtitle = scrapedtitle.replace('(' + year + ')', '')

    return scrapedtitle.strip()


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def findvideos(item):
    log()
    data = httptools.downloadpage(item.url, headers=headers, ignore_response_code=True).data
    data = re.sub(r'\n|\t|\s+', ' ', data)
    # recupero il blocco contenente i link
    blocco = scrapertools.find_single_match(data, r'<div class="entry">([\s\S.]*?)<div class="post').replace('..:: Episodio ', 'Episodio ').strip()
    matches = scrapertools.find_multiple_matches(blocco, r'(S(\d*)E(\d*))\s')
    if len(matches) > 0:
        for fullseasonepisode, season, episode in matches:
            blocco = blocco.replace(fullseasonepisode + ' ', 'Episodio ' + episode + ' ')

    blocco = blocco.replace('Episodio ', '..:: Episodio ')

    episodio = item.infoLabels['episode']
    patron = r'\.\.:: Episodio %s([\s\S]*?)(<div class="post|..:: Episodio)' % episodio
    log(patron)
    log(blocco)

    matches = scrapertools.find_multiple_matches(blocco, patron)
    if len(matches):
        data = matches[0][0]

    patron = r'href="(https?://www\.keeplinks\.(?:co|eu)/p(?:[0-9]*)/([^"]+))"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for keeplinks, id in matches:
        headers2 = [['Cookie', 'flag[' + id + ']=1; defaults=1; nopopatall=' + str(int(time.time()))],
                   ['Referer', keeplinks]]

        html = httptools.downloadpage(keeplinks, headers=headers2).data
        data += str(scrapertools.find_multiple_matches(html, '</lable><a href="([^"]+)" target="_blank"'))

    return support.server(item, data=data)

# ================================================================================================================


# ----------------------------------------------------------------------------------------------------------------
def lista_serie(item):
    log()
    itemlist = []

    PERPAGE = 15

    p = 1
    if '{}' in item.url:
        item.url, p = item.url.split('{}')
        p = int(p)

    if '||' in item.url:
        series = item.url.split('\n\n')
        matches = []
        for i, serie in enumerate(series):
            matches.append(serie.split('||'))
    else:
        # Extrae las entradas
        patron = r'<li class="cat-item cat-item-\d+"><a href="([^"]+)"\s?>([^<]+)</a>'
        matches = support.match(item, patron=patron, headers=headers).matches
    for i, (scrapedurl, scrapedtitle) in enumerate(matches):
        scrapedplot = ""
        scrapedthumbnail = ""
        if (p - 1) * PERPAGE > i: continue
        if i >= p * PERPAGE: break
        title = cleantitle(scrapedtitle)
        itemlist.append(
            item.clone(action="episodios",
                       title=title,
                       url=scrapedurl,
                       thumbnail=scrapedthumbnail,
                       fulltitle=title,
                       show=title,
                       plot=scrapedplot,
                       contentType='episode',
                       originalUrl=scrapedurl))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Paginazione
    if len(matches) >= p * PERPAGE:
        support.nextPage(itemlist, item, next_page=(item.url + '{}' + str(p + 1)))

    return itemlist


# ================================================================================================================


# ----------------------------------------------------------------------------------------------------------------
def episodios(item, itemlist=[]):
    log()
    patron = r'<div class="post-meta">\s*<a href="([^"]+)"\s*title="([^"]+)"\s*class=".*?"></a>.*?'
    patron += r'<p><a href="([^"]+)">'


    html = support.match(item, patron=patron, headers=headers)
    matches = html.matches
    data = html.data

    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        scrapedplot = ""
        scrapedtitle = cleantitle(scrapedtitle)
        if "(Completa)" in scrapedtitle:
            data = httptools.downloadpage(scrapedurl, headers=headers).data
            scrapedtitle = scrapedtitle.replace(" – Miniserie", " – Stagione 1")
            title = scrapedtitle.split(" – Stagione")[0].strip()

            # recupero la stagione
            season = scrapertools.find_single_match(scrapedtitle, 'Stagione ([0-9]*)')
            blocco = scrapertools.find_single_match(data, r'<div class="entry">[\s\S.]*?<div class="post')
            blocco = blocco.replace('<strong>Episodio ', '<strong>Episodio ').replace(' </strong>', ' </strong>')
            blocco = blocco.replace('<strong>Episodio ', '<strong>S' + season.zfill(2) + 'E')
            matches = scrapertools.find_multiple_matches(blocco, r'(S(\d*)E(\d*))\s')
            episodes = []
            if len(matches) > 0:
                for fullepisode_s, season, episode in matches:
                    season = season.lstrip("0")

                    episodes.append([
                        "".join([season, "x", episode]),
                        season,
                        episode
                    ])

        else:
            title = scrapedtitle.split(" S0")[0].strip()
            title = title.split(" S1")[0].strip()
            title = title.split(" S2")[0].strip()
            episodes = scrapertools.find_multiple_matches(scrapedtitle, r'((\d*)x(\d*))')

        for fullepisode, season, episode in episodes:
            infoLabels = {}
            infoLabels['season'] = season
            infoLabels['episode'] = episode
            fullepisode += ' ' + support.typo("Sub-ITA", '_ [] color kod')
            itemlist.append(
                item.clone(action="findvideos",
                           fulltitle=scrapedtitle,
                           show=scrapedtitle,
                           title=fullepisode,
                           url=scrapedurl,
                           thumbnail=scrapedthumbnail,
                           plot=scrapedplot,
                           contentSerieName=title,
                           infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Paginazionazione
    patron = r'<strong class="on">\d+</strong>\s*<a href="([^<]+)">\d+</a>'
    next_page = scrapertools.find_single_match(data, patron)
    if next_page != "":
        item.url = next_page
        itemlist = episodios(item, itemlist)
    else:
        item.url = item.originalUrl
        support.videolibrary(itemlist, item, 'bold color kod')

    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def peliculas_tv(item):
    log()
    itemlist = []

    patron = r'<div class="post-meta">\s*<a href="([^"]+)"\s*title="([^"]+)"\s*class=".*?"></a>'

    html = support.match(item, patron=patron, headers=headers)
    matches = html.matches
    data = html.data

    for scrapedurl, scrapedtitle in matches:
        if scrapedtitle in ["FACEBOOK", "RAPIDGATOR", "WELCOME!"]:
            continue

        scrapedthumbnail = ""
        scrapedplot = ""
        scrapedtitle = cleantitle(scrapedtitle)
        infoLabels = {}
        episode = scrapertools.find_multiple_matches(scrapedtitle, r'((\d*)x(\d*))')
        if episode:  # workaround per quando mettono le serie intere o altra roba, sarebbero da intercettare TODO
            episode = episode[0]
            title = scrapedtitle.split(" S0")[0].strip()
            title = title.split(" S1")[0].strip()
            title = title.split(" S2")[0].strip()

            infoLabels['season'] = episode[1]
            infoLabels['episode'] = episode[2].zfill(2)

            itemlist.append(
                item.clone(action="findvideos",
                           fulltitle=scrapedtitle,
                           show=scrapedtitle,
                           title=title + " - " + episode[0] + " " + support.typo("Sub-ITA", '_ [] color kod'),
                           url=scrapedurl,
                           thumbnail=scrapedthumbnail,
                           contentSerieName=title,
                           contentLanguage='Sub-ITA',
                           plot=scrapedplot,
                           infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Paginazione
    patron = r'<strong class="on">\d+</strong>\s?<a href="([^<]+)">\d+</a>'
    support.nextPage(itemlist, item, data, patron)

    return itemlist


# ================================================================================================================


# ----------------------------------------------------------------------------------------------------------------
def newest(categoria):
    log(categoria)
    itemlist = []
    item = Item()
    item.url = host
    item.extra = 'serie'
    try:
        if categoria == "series":
            itemlist = peliculas_tv(item)
            if itemlist[-1].action == 'peliculas_tv':
                itemlist.pop(-1)

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
    itemlist = []

    patron = r'<li class="cat-item cat-item-\d+"><a href="([^"]+)"\s?>([^<]+)</a>'
    matches = support.match(item, patron=patron, headers=headers).matches
    for i, (scrapedurl, scrapedtitle) in enumerate(matches):
        if texto.upper() in scrapedtitle.upper():
            scrapedthumbnail = ""
            scrapedplot = ""
            title = cleantitle(scrapedtitle)
            itemlist.append(
                item.clone(action="episodios",
                           title=title,
                           url=scrapedurl,
                           thumbnail=scrapedthumbnail,
                           fulltitle=title,
                           show=title,
                           plot=scrapedplot,
                           contentType='episode',
                           originalUrl=scrapedurl))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------


def list_az(item):
    log()
    itemlist = []

    alphabet = dict()
    patron = r'<li class="cat-item cat-item-\d+"><a href="([^"]+)"\s?>([^<]+)</a>'
    matches = support.match(item, patron=patron, headers=headers).matches
    for i, (scrapedurl, scrapedtitle) in enumerate(matches):
        letter = scrapedtitle[0].upper()
        if letter not in alphabet:
            alphabet[letter] = []
        alphabet[letter].append(scrapedurl + '||' + scrapedtitle)

    for letter in sorted(alphabet):
        itemlist.append(
            item.clone(action="lista_serie",
                       url='\n\n'.join(alphabet[letter]),
                       title=letter,
                       fulltitle=letter))

    return itemlist

# ================================================================================================================
 

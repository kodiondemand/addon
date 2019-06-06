# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per fastsubita
# Thanks Icarus crew & Alfa addon & 4l3x87
# ------------------------------------------------------------

from core import scrapertools, httptools, tmdb, support
from core.item import Item
from core.support import log
from platformcode import config, logger

__channel__ = 'fastsubita'
host = config.get_setting("channel_host", __channel__)
IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['verystream', 'openload', 'speedvideo', 'wstream', 'flashx', 'vidoza', 'vidtome']
list_quality = ['default']

headers = [
    ['Host', host.split("//")[-1].split("/")[0]],
    ['User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0'],
    ['Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'],
    ['Accept-Language', 'en-US,en;q=0.5'],
    ['Accept-Encoding', 'gzip, deflate'],
    ['Referer', host],
    ['DNT', '1'],
    ['Connection', 'keep-alive'],
    ['Upgrade-Insecure-Requests', '1'],
    ['Cache-Control', 'max-age=0']
]

PERPAGE = 15


def mainlist(item):
    log()
    itemlist = []

    support.menu(itemlist, 'Novità bold', 'pelicuals_tv', host, 'tvshow')
    support.menu(itemlist, 'Serie TV bold', 'lista_serie', host, 'tvshow')
    support.menu(itemlist, 'Archivio A-Z submenu', 'list_az', host, 'tvshow', args=['serie'])
    support.menu(itemlist, 'Cerca', 'search', host, 'tvshow')
    support.aplay(item, itemlist, list_servers, list_quality)
    support.channel_config(item, itemlist)

    return itemlist


# ----------------------------------------------------------------------------------------------------------------
def cleantitle(scrapedtitle):
    scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle.strip())
    scrapedtitle = scrapedtitle.replace('’', '\'').replace('&#215;', 'x').replace('×', 'x').replace('"', "'")

    return scrapedtitle.strip()


# ================================================================================================================


def newest(categoria):
    log()
    itemlist = []
    item = Item()
    try:
        if categoria == "series":
            item.url = host
            # item.action = "serietv"
            itemlist = pelicuals_tv(item)

            if itemlist[-1].action == "serietv":
                itemlist.pop()

    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def pelicuals_tv(item):
    log()
    itemlist = []

    matches, data = support.match(item, r'<h3 class="entry-title title-font"><a href="([^"]+)" rel="bookmark">(.*?)<',
                                  headers=headers)

    for scrapedurl, scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scraped_1 = scrapedtitle.split("&#215;")[0][:-2]
        scrapedtitle = cleantitle(scrapedtitle)
        episode = scrapertools.find_multiple_matches(scrapedtitle, r'((\d*)x(\d*))')[0]
        scrapedtitle = scrapedtitle.replace(scraped_1, "")

        infoLabels = {}
        infoLabels['season'] = episode[1]
        infoLabels['episode'] = episode[2]

        if "http:" in scrapedurl:
            scrapedurl = scrapedurl
        else:
            scrapedurl = "http:" + scrapedurl


        serie = cleantitle(scraped_1)
        title = serie + " - " + infoLabels['season'] + "x" + infoLabels['episode'] + " "+support.typo('Sub-ITA', '_ [] color kod')

        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentTpye="tvshow",
                 title=title,
                 fulltitle=title,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 show=serie,
                 extra=item.extra,
                 contentSerieName=serie,
                 contentLanguage='Sub-ITA',
                 infoLabels=infoLabels,
                 folder=True))
    support.checkHost(item, itemlist)
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Paginazione
    support.nextPage(itemlist, item, data, '<a class="next page-numbers" href="(.*?)">Successivi')

    return itemlist


def serietv():
    log()

    itemlist = []
    matches = support.match(Item(), r'<option class="level-([0-9]?)" value="([^"]+)">([^<]+)</option>',
                            r'<select\s*?name="cat"\s*?id="cat"\s*?class="postform"\s*?>(.*?)</select>', headers,
                            url="%s/" % host)[0]
    index = 0

    for level, cat, title in matches:
        title = cleantitle(title)
        url = '%s?cat=%s' % (host, cat)
        if int(level) > 0:
            itemlist[index - 1][0] += '{|}' + url
            continue

        itemlist.append([url, title])

        index += 1
    return itemlist


def lista_serie(item):
    log()
    itemlist = []

    p = 1
    if '{}' in item.url:
        item.url, p = item.url.split('{}')
        p = int(p)

    if '||' in item.url:
        series = item.url.split('\n\n')
        matches = []
        for i, serie in enumerate(series):
            matches.append(serie.split('||'))
        series = matches
    else:
        series = serietv()

    for i, (scrapedurl, scrapedtitle) in enumerate(series):
        if (p - 1) * PERPAGE > i: continue
        if i >= p * PERPAGE: break

        scrapedplot = ""
        scrapedthumbnail = ""

        itemlist.append(
            Item(channel=item.channel,
                 action="episodios",
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 show=scrapedtitle,
                 extra=item.extra,
                 contentType='episode',
                 originalUrl=scrapedurl,
                 folder=True))

    support.checkHost(item, itemlist)
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if len(series) >= p * PERPAGE:
        next_page = item.url + '{}' + str(p + 1)
        support.nextPage(itemlist, item, next_page=next_page)

    return itemlist


def findvideos(item):
    log()
    itemlist = []

    # data = httptools.downloadpage(item.url, headers=headers).data
    patron_block = '<div class="entry-content">(.*?)<footer class="entry-footer">'
    # bloque = scrapertools.find_single_match(data, patron_block)

    patron = r'<a href="([^"]+)">'
    # matches = re.compile(patron, re.DOTALL).findall(bloque)

    matches, data = support.match(item, patron, patron_block, headers)

    for scrapedurl in matches:
        if 'is.gd' in scrapedurl:
            resp = httptools.downloadpage(
                scrapedurl, follow_redirects=False)
            data += resp.headers.get("location", "") + '\n'

    return support.server(item, data)


def search(item, texto):
    log(texto)

    itemlist = []
    try:
        series = serietv()
        for i, (scrapedurl, scrapedtitle) in enumerate(series):
            if texto.upper() in scrapedtitle.upper():
                scrapedthumbnail = ""
                scrapedplot = ""
                itemlist.append(
                    Item(channel=item.channel,
                         extra=item.extra,
                         action="episodios",
                         title=scrapedtitle,
                         url=scrapedurl,
                         thumbnail=scrapedthumbnail,
                         fulltitle=scrapedtitle,
                         show=scrapedtitle,
                         plot=scrapedplot,
                         contentType='episode',
                         originalUrl=scrapedurl,
                         folder=True))
        return itemlist
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


# ----------------------------------------------------------------------------------------------------------------

def list_az(item):
    log()
    itemlist = []

    alphabet = dict()

    for i, (scrapedurl, scrapedtitle) in enumerate(serietv()):
        letter = scrapedtitle[0].upper()
        if letter not in alphabet:
            alphabet[letter] = []
        alphabet[letter].append(scrapedurl + '||' + scrapedtitle)

    for letter in sorted(alphabet):
        itemlist.append(
            Item(channel=item.channel,
                 action="lista_serie",
                 url='\n\n'.join(alphabet[letter]),
                 title=letter,
                 fulltitle=letter))

    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def episodios(item, itemlist=[]):
    log()
    urls = item.url.split('{|}')
    patron = r'<h3 class="entry-title title-font"><a href="([^"]+)" rel="bookmark">(.*?)<'
    matches, data = support.match(item, patron, headers=headers, url=urls[0])
    urls.pop(0)

    for scrapedurl, scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = cleantitle(scrapedtitle)
        episode = scrapertools.find_multiple_matches(scrapedtitle, r'((\d*)x(\d*))')[0]

        season = episode[1].lstrip('0').zfill(2)

        infoLabels = {}
        infoLabels['season'] = season
        infoLabels['episode'] = episode[2]
        title = infoLabels['season'] + 'x' + infoLabels['episode'] + " "+support.typo('Sub-ITA', '_ [] color kod')

        if "http:" not in scrapedurl:
            scrapedurl = "http:" + scrapedurl

        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentTpye="episode",
                 title=title,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 show=item.show,
                 extra=item.extra,
                 infoLabels=infoLabels,
                 folder=True))

    next_page = scrapertools.find_single_match(data, r'<a class="next page-numbers" href="(.*?)">Successivi')
    if next_page != "":
        urls.insert(0, next_page)

    if len(urls) > 0:
        item.url = '{|}'.join(urls)
        itemlist = episodios(item, itemlist)
    else:
        cleanItemlist = []
        episodes = []
        for episode in itemlist:
            if episode.title in episodes: continue
            cleanItemlist.append(episode)
            episodes.append(episode.title)
        itemlist = cleanItemlist

        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
        item.url = item.originalUrl
        support.videolibrary(itemlist, item, 'bold color kod')

    return itemlist

# ================================================================================================================

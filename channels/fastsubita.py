# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Thanks Icarus crew & Alfa addon
# Canale per fastsubita
# ------------------------------------------------------------

import re

import channelselector
from core import scrapertools, httptools, tmdb, support
from core.item import Item
from platformcode import config, logger
from specials import autoplay

__channel__ = 'fastsubita'
host = config.get_setting("channel_host", __channel__)
IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['verystream', 'openload', 'speedvideo', 'wstream', 'flashx', 'vidoza', 'vidtome']
list_quality = ['default']

# checklinks = config.get_setting('checklinks', 'fastsubita')
# checklinks_number = config.get_setting('checklinks_number', 'fastsubita')

headers = [
    ['Host', 'fastsubita.com'],
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
    logger.info(item.channel+" mainlist")
    itemlist = []

    support.menu(itemlist, 'Serie TV bold', 'lista_serie', host,'tvshow')
    support.menu(itemlist, 'Novità submenu', 'pelicuals_tv', host,'tvshow')
    support.menu(itemlist, 'Archivio A-Z submenu', 'list_az', host,'tvshow',args=['serie'])
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
    scrapedtitle = scrapedtitle.replace('’', '\'').replace('&#215;','x').replace('×','x')

    return scrapedtitle.strip()


# ================================================================================================================


def newest(categoria):
    logger.info(__channel__+" newest" + categoria)
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
    logger.info(item.channel+" pelicuals_tv")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    # Estrae i contenuti 
    patron = r'<h3 class="entry-title title-font"><a href="([^"]+)" rel="bookmark">(.*?)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

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

        title = scraped_1+" - "+infoLabels['season']+"x"+infoLabels['episode']+" Sub-ITA"

        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentTpye="tvshow",
                 title=title,
                 fulltitle=title,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 show=scraped_1,
                 extra=item.extra,
                 contentSerieName=scraped_1,
                 contentLanguage='Sub-ITA',
                 infoLabels=infoLabels,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Paginazione
    support.nextPage(itemlist,item,data,'<a class="next page-numbers" href="(.*?)">Successivi')

    return itemlist

def serietv():
    logger.info(__channel__+" serietv")

    itemlist = []
    data = httptools.downloadpage("%s/" % host, headers=headers).data
    # block = scrapertools.find_single_match(data, r'<div class="entry-content">(.*?)</div>')
    block = scrapertools.find_single_match(data, r"<select\s*?name='cat'\s*?id='cat'\s*?class='postform'\s*?>(.*?)</select>")
    # block = data
    # Estrae i contenuti
    # patron = r'<a style.*?href="([^"]+)">([^<]+)<\/a>'
    # patron = r'<a.*?href="([^"]+)">([^<]+)<\/a>'
    # matches = re.compile(patron, re.DOTALL).findall(block)
    matches = re.compile(r'<option class="level-([0-9]?)" value="([^"]+)">([^<]+)</option>', re.DOTALL).findall(block)
    index = 0
    # for scrapedurl, scrapedtitle  in matches:
    #     scrapedtitle = cleantitle(scrapedtitle)
    #     if "http:" not in scrapedurl:
    #         scrapedurl = "http:" + scrapedurl
    #
    #     if ('S' in scrapedtitle.strip().upper()[0] and len(scrapedtitle.strip()) == 3) or '02' == scrapedtitle:
    #         # itemlist[index -1][0]+='{|}'+scrapedurl
    #         continue
    #
    #     itemlist.append([scrapedurl,scrapedtitle])
    #     index += 1
    for level, cat, title in matches:
        title = cleantitle(title)
        url = '%s?cat=%s' % (host, cat)
        if int(level) > 0:
            itemlist[index - 1][0] += '{|}' + url
            continue

        itemlist.append([url, title])

        index += 1

    logger.debug(itemlist)
    return itemlist

def lista_serie(item):
    logger.info(item.channel+" lista_serie")
    itemlist = []

    p = 1
    if '{}' in item.url:
        item.url, p = item.url.split('{}')
        p = int(p)

    # logger.debug(p)
    # Carica la pagina 
    # data = httptools.downloadpage(item.url, headers=headers).data
    #
    # block = scrapertools.find_single_match(data,r'<div class="entry-content">(.*?)</div>')
    #
    # # Estrae i contenuti
    # # patron = r'<a style.*?href="([^"]+)">([^<]+)<\/a>'
    # patron = r'<a.*?href="([^"]+)">([^<]+)<\/a>'
    # matches = re.compile(patron, re.DOTALL).findall(block)
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
        # ii += 1

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if len(series) >= p * PERPAGE:
        scrapedurl = item.url + '{}' + str(p + 1)
        itemlist.append(
            Item(channel=item.channel,
                 action='lista_serie',
                 contentType=item.contentType,
                 title=support.typo(config.get_localized_string(30992), 'color kod bold'),
                 url=scrapedurl,
                 args=item.args,
                 extra=item.extra,
                 thumbnail=support.thumb()))

    return itemlist

def findvideos(item):
    logger.info(item.channel+" findvideos")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    bloque = scrapertools.find_single_match(data, '<div class="entry-content">(.*?)<footer class="entry-footer">')

    patron = r'<a href="([^"]+)">'
    matches = re.compile(patron, re.DOTALL).findall(bloque)
    for scrapedurl in matches:
        if 'is.gd' in scrapedurl:
            resp = httptools.downloadpage(
                 scrapedurl, follow_redirects=False)
            data += resp.headers.get("location", "") + '\n'


    itemlist = support.server(item,data)

    # itemlist = servertools.find_video_items(data=data)
    #
    # for videoitem in itemlist:
    #     videoitem.title = item.title + videoitem.title
    #     videoitem.fulltitle = item.fulltitle
    #     videoitem.thumbnail = item.thumbnail
    #     videoitem.show = item.show
    #     videoitem.plot = item.plot
    #     videoitem.channel = item.channel
    #     videoitem.contentType = item.contentType
    #     videoitem.language = IDIOMAS['Italiano']
    #
    # # Requerido para Filtrar enlaces
    #
    # if checklinks:
    #     itemlist = servertools.check_list_links(itemlist, checklinks_number)
    #
    # # Requerido para FilterTools
    #
    # # itemlist = filtertools.get_links(itemlist, item, list_language)
    #
    # # Requerido para AutoPlay
    #
    # autoplay.start(itemlist, item)



    return itemlist


def search(item, texto):
    logger.info(item.channel + " " + item.url + " search " + texto)
    # item.url = "%s/?s=%s" % (host, texto)
    # item.url = "%s/elenco-serie-tv/" % host
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
    support.log(item.channel + " list_az")
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
def episodios(item,itemlist = []):
    support.log(item.channel + " episodios")
    urls = item.url.split('{|}')
    # logger.debug(urls)
    # Carica la pagina
    data = httptools.downloadpage(urls[0], headers=headers).data
    urls.pop(0)
    # Estrae i contenuti
    patron = r'<h3 class="entry-title title-font"><a href="([^"]+)" rel="bookmark">(.*?)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    # logger.debug(matches)
    for scrapedurl, scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = cleantitle(scrapedtitle)
        episode = scrapertools.find_multiple_matches(scrapedtitle,r'((\d*)x(\d*))')[0]

        season = episode[1].lstrip('0')
        # if season in seasons and '/page/' not in item.url: break
        # logger.debug(scrapedtitle)
        # logger.debug(episode)
        # return False

        infoLabels = {}
        infoLabels['season'] = season
        infoLabels['episode'] = episode[2]
        title = infoLabels['season']+'x'+infoLabels['episode']+" Sub-ITA"

        if "http:" not in scrapedurl:
            scrapedurl = "http:" + scrapedurl

        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentTpye="tvshow",
                 title=title,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 show=item.show,
                 extra=item.extra,
                 infoLabels=infoLabels,
                 folder=True))


    next_page = scrapertools.find_single_match(data,r'<a class="next page-numbers" href="(.*?)">Successivi')
    if next_page != "":
        urls.insert(0,next_page)

    # logger.debug(urls)

    if(len(urls) > 0):
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

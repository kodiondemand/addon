# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Serie Tv Sub ITA
# Thanks to Icarus crew & Alfa addon
# ----------------------------------------------------------
import re
import time

import channelselector
from core import httptools, tmdb, scrapertools, support
from core.item import Item
from platformcode import logger, config
from specials import autoplay

__channel__ = "serietvsubita"
host = config.get_setting("channel_host", __channel__)
headers = [['Referer', host]]

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['gounlimited','verystream','streamango','openload']
list_quality = ['default']

# __comprueba_enlaces__ = config.get_setting('comprueba_enlaces', __channel__)
# __comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', __channel__)


def mainlist(item):
    support.log(item.channel + 'mainlist')
    itemlist = []
    support.menu(itemlist, 'Serie TV bold', 'lista_serie', host,'tvshow')
    support.menu(itemlist, 'Novità submenu', 'peliculas_tv', host,'tvshow')
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
    scrapedtitle = scrapedtitle.replace('[HD]', '').replace('’', '\'').replace('×','x').replace('Game of Thrones –','')
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

    if '||' in item.url:
        series = item.url.split('\n\n')
        matches = []
        for i, serie in enumerate(series):
            matches.append(serie.split('||'))
    else:
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
def episodios(item, itemlist=[]):
    support.log(item.channel + " episodios")
    # itemlist = []

    data = httptools.downloadpage(item.url).data


    patron = '<div class="post-meta">\s*<a href="([^"]+)"\s*title="([^"]+)"\s*class=".*?"></a>.*?'
    patron += '<p><a href="([^"]+)">'

    matches = re.compile(patron, re.DOTALL).findall(data)
    logger.debug(itemlist)
    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        scrapedplot = ""
        scrapedtitle = cleantitle(scrapedtitle)
        if "(Completa)" in scrapedtitle:
            data = httptools.downloadpage(scrapedurl).data
            scrapedtitle = scrapedtitle.replace(" – Miniserie"," – Stagione 1")
            title = scrapedtitle.split(" – Stagione")[0].strip()

            # recupero la stagione
            season = scrapertools.find_single_match(scrapedtitle,'Stagione ([0-9]*)')
            blocco = scrapertools.find_single_match(data, '<div class="entry">[\s\S.]*?<div class="post')
            # blocco = scrapertools.decodeHtmlentities(blocco)
            blocco = blocco.replace('<strong>Episodio ','<strong>Episodio ').replace(' </strong>',' </strong>')
            blocco = blocco.replace('<strong>Episodio ','<strong>S'+season.zfill(2)+'E')
            # logger.debug(blocco)
            # controllo se gli episodi son nel formato S0XE0X
            matches = scrapertools.find_multiple_matches(blocco,r'(S(\d*)E(\d*))\s')
            episodes = []
            if len(matches) > 0:
                for fullepisode_s, season, episode in matches:

                    season = season.lstrip("0")
                    # episode = episode.lstrip("0")

                    episodes.append([
                        "".join([season, "x", episode]),
                        season,
                        episode
                    ])
            # else:
            #     # blocco = blocco.replace('>Episodio 0','>Episodio-0')
            #     matches = scrapertools.find_multiple_matches(blocco, r'Episodio[^\d](\d*)')
            #     logger.debug(blocco)
            #     logger.debug(matches)
            #     episodes = []
            #     if len(matches) > 0:
            #         for string, episode in matches:
            #             episodes.append([
            #                 "".join([season, "x", episode]),
            #                 season,
            #                 episode
            #             ])

        else:
            title = scrapedtitle.split(" S0")[0].strip()
            title = title.split(" S1")[0].strip()
            title = title.split(" S2")[0].strip()
            episodes = scrapertools.find_multiple_matches(scrapedtitle,r'((\d*)x(\d*))')
        # logger.debug(scrapedtitle)
        # logger.debug(episodes)

        for fullepisode, season, episode in episodes:
            infoLabels = {}
            infoLabels['season'] = season
            infoLabels['episode'] = episode

            itemlist.append(
                Item(channel=item.channel,
                     extra=item.extra,
                     action="findvideos",
                     fulltitle=scrapedtitle,
                     show=scrapedtitle,
                     title=fullepisode,
                     url=scrapedurl,
                     thumbnail=scrapedthumbnail,
                     plot=scrapedplot,
                     contentSerieName=title,
                     infoLabels=infoLabels,
                     folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Paginazionazione
    patron = '<strong class=\'on\'>\d+</strong>\s*<a href="([^<]+)">\d+</a>'
    next_page = scrapertools.find_single_match(data, patron)
    if next_page != "":
        item.url = next_page
        itemlist = episodios(item,itemlist)
    else:
        item.url = item.originalUrl
        support.videolibrary(itemlist,item,'bold color kod')

    return itemlist

# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def findvideos(item):
    support.log(item.channel + " findvideos")

    data = httptools.downloadpage(item.url).data

    # recupero il blocco contenente i link
    blocco = scrapertools.find_single_match(data,'<div class="entry">[\s\S.]*?<div class="post')
    blocco = blocco.replace('..:: Episodio ','Episodio ')

    matches = scrapertools.find_multiple_matches(blocco, '(S(\d*)E(\d*))\s')
    if len(matches) > 0:
        for fullseasonepisode, season, episode in matches:
            blocco = blocco.replace(fullseasonepisode+' ','Episodio '+episode+' ')

    blocco = blocco.replace('Episodio ', '..:: Episodio ')
    logger.debug(blocco)

    episodio = item.title.replace(str(item.contentSeason)+"x",'')
    patron = r'\.\.:: Episodio %s([\s\S]*?)(<div class="post|..:: Episodio)' % episodio
    matches = re.compile(patron, re.DOTALL).findall(blocco)
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
    # if __comprueba_enlaces__:
    #     itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)
    #
    # autoplay.start(itemlist, item)

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
        episode = scrapertools.find_multiple_matches(scrapedtitle, r'((\d*)x(\d*))')[0]
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
                 contentSerieName=title+" ("+episode[0]+" Sub-Ita)",
                 plot=scrapedplot,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)


    # Paginazione
    patron = '<strong class=\'on\'>\d+</strong>\s*<a href="([^<]+)">\d+</a>'
    support.nextPage(itemlist,item,data,patron)
    # next_page = scrapertools.find_single_match(data, patron)
    # if next_page != "":
    #     if item.extra == "search_tv":
    #         next_page = next_page.replace('&#038;', '&')
    #     itemlist.append(
    #         Item(channel=item.channel,
    #              action='peliculas_tv',
    #              contentType=item.contentType,
    #              title=support.typo(config.get_localized_string(30992), 'color kod bold'),
    #              url=next_page,
    #              args=item.args,
    #              extra=item.extra,
    #              thumbnail=support.thumb()))


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

    # Scarico la pagina
    data = httptools.downloadpage(item.url).data

    # Articoli
    patron = '<li class="cat-item cat-item-\d+"><a href="([^"]+)" >([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for i, (scrapedurl, scrapedtitle) in enumerate(matches):
        if texto.upper() in scrapedtitle.upper():
            scrapedthumbnail = ""
            scrapedplot = ""
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

    return itemlist

    # item.extra = "search_tv"
    #
    # item.url = host + "/?s=" + texto + "&op.x=0&op.y=0"
    #
    # try:
    #     return peliculas_tv(item)
    #
    # except:
    #     import sys
    #     for line in sys.exc_info():
    #         logger.error("%s" % line)
    #     return []


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------


def list_az(item):
    support.log(item.channel+" list_az")
    itemlist = []

    alphabet = dict()

    # Scarico la pagina
    data = httptools.downloadpage(item.url).data

    # Articoli
    patron = '<li class="cat-item cat-item-\d+"><a href="([^"]+)" >([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for i, (scrapedurl, scrapedtitle) in enumerate(matches):
        letter = scrapedtitle[0].upper()
        if letter not in alphabet:
            alphabet[letter] = []
        alphabet[letter].append(scrapedurl+'||'+scrapedtitle)

    for letter in sorted(alphabet):
        itemlist.append(
            Item(channel=item.channel,
                 action="lista_serie",
                 url='\n\n'.join(alphabet[letter]),
                 title=letter,
                 fulltitle=letter))

    return itemlist

# ================================================================================================================

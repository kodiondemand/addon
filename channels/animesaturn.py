# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per AnimeSaturn
# Thanks to me
# ----------------------------------------------------------
import re

import urlparse

import channelselector
from core import httptools, tmdb, support, scrapertools, jsontools
from core.item import Item
from platformcode import logger, config
from specials import autoplay, autorenumber

__channel__ = "animesaturn"
host = config.get_setting("channel_host", __channel__)
headers = [['Referer', host]]

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['openload','fembed']
list_quality = ['default']


def mainlist(item):
    support.log(item.channel + 'mainlist')
    itemlist = []
    support.menu(itemlist, 'Anime bold', 'lista_anime',  "%s/animelist?load_all=1" % host)
    support.menu(itemlist, 'Novità submenu', 'ultimiep',  "%s/fetch_pages.php?request=episodes" % host,'tvshow')
    support.menu(itemlist, 'Archivio A-Z submenu', 'list_az', '%s/animelist?load_all=1' % host,args=['tvshow','alfabetico'])
    support.menu(itemlist, 'Cerca', 'search', host)


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

    if '||' in item.url:
        series = item.url.split('\n\n')
        matches = []
        for i, serie in enumerate(series):
            matches.append(serie.split('||'))
    else:
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
        title = cleantitle(scrapedtitle).replace('(ita)','(ITA)')
        movie = False
        showtitle = title
        if '(ITA)' in title:
            title = title.replace('(ITA)','').strip()
            showtitle = title
            title += ' '+support.typo(' (ITA)')

        infoLabels = {}
        if 'Akira' in title:
            movie = True
            infoLabels['year']= 1988

        if 'Dragon Ball Super Movie' in title:
            movie = True
            infoLabels['year'] = 2019


        itemlist.append(
            Item(channel=item.channel,
                 extra=item.extra,
                 action="episodios" if movie == False else 'findvideos',
                 title=title,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 fulltitle=showtitle,
                 show=showtitle,
                 contentTitle=showtitle,
                 plot=scrapedplot,
                 contentType='episode' if movie == False else 'movie',
                 originalUrl=scrapedurl,
                 infoLabels=infoLabels,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    autorenumber.renumber(itemlist)

    # Paginazione
    if len(matches) >= p * PERPAGE:
        scrapedurl = item.url + '{}' + str(p + 1)
        itemlist.append(
            Item(channel=item.channel,
                 action='lista_anime',
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

    #movie or series
    movie = scrapertools.find_single_match(data, r'\Episodi:</b>\s(\d*)\sMovie')


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
        scrapedtitle = '[B]' + scrapedtitle + '[/B]'

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

    if(((len(itemlist) == 1 and 'Movie' in itemlist[0].title) or movie) and item.contentType!='movie'):
        item.url = itemlist[0].url
        item.contentType = 'movie'
        return findvideos(item)



    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    autorenumber.renumber(itemlist, item)
    support.videolibrary(itemlist,item,'bold color kod')

    return itemlist

# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def findvideos(item):
    support.log(item.channel + " findvideos")
    originalItem = item

    if(item.contentType == 'movie'):
        episodes = episodios(item)

        if(len(episodes)>0):
            item.url = episodes[0].url


    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = r'<a href="([^"]+)"><div class="downloadestreaming">'
    url = scrapertools.find_single_match(data, patron)

    data = httptools.downloadpage(url).data

    itemlist = support.server(item, data=data)

    if item.contentType == 'movie':
        support.videolibrary(itemlist, item, 'color kod')
    # Controlla se i link sono validi
    # if checklinks:
    #     itemlist = servertools.check_list_links(itemlist, checklinks_number)
    #
    # autoplay.start(itemlist, item)

    return itemlist

# ================================================================================================================


# ----------------------------------------------------------------------------------------------------------------

def ultimiep(item):
    logger.info(item.channel + "ultimiep")
    itemlist = []

    post = "page=%s" % item.args['page'] if item.args and item.args['page'] else None

    data = httptools.downloadpage(
        item.url, post=post, headers={
            'X-Requested-With': 'XMLHttpRequest'
        }).data

    patron = r"""<a href='[^']+'><div class="locandina"><img alt="[^"]+" src="([^"]+)" title="[^"]+" class="grandezza"></div></a>\s*"""
    patron += r"""<a href='([^']+)'><div class="testo">(.+?)</div></a>\s*"""
    patron += r"""<a href='[^']+'><div class="testo2">(.+?)</div></a>"""
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedurl, scrapedtitle1, scrapedtitle2 in matches:
        scrapedtitle1 = cleantitle(scrapedtitle1)
        scrapedtitle2 = cleantitle(scrapedtitle2)
        scrapedtitle = scrapedtitle1 + ' - ' + scrapedtitle2 + ''

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
                title=support.typo(config.get_localized_string(30992), 'color kod bold'),
                url=item.url,
                thumbnail= support.thumb(),
                args={'page':next_page},
                folder=True))

    return itemlist



# ================================================================================================================



# ----------------------------------------------------------------------------------------------------------------
def newest(categoria):
    logger.info(__channel__ + " newest" + categoria)
    itemlist = []
    item = Item()
    item.url = host
    item.extra = ''
    try:
        if categoria == "anime":
            item.url = "%s/fetch_pages?request=episodios" % host
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
def search_anime(item, texto):
    logger.info(item.channel + " search_anime: "+texto)
    itemlist = []

    # data = httptools.downloadpage(host + "/animelist?load_all=1").data
    # data = scrapertools.decodeHtmlentities(data)
    #
    # texto = texto.lower().split('+')
    #
    # patron = r'<a href="([^"]+)"[^>]*?>[^>]*?>(.+?)<'
    # matches = re.compile(patron, re.DOTALL).findall(data)
    #
    # for scrapedurl, scrapedtitle in [(scrapedurl, scrapedtitle)
    #                                  for scrapedurl, scrapedtitle in matches
    #                                  if all(t in scrapedtitle.lower()
    #                                         for t in texto)]:
    #
    #     title = cleantitle(scrapedtitle).replace('(ita)','(ITA)')
    #     showtitle = title
    #     if '(ITA)' in title:
    #         title = title.replace('(ITA)','').strip()
    #         showtitle = title
    #         title += ' '+support.typo(' [ITA] color kod')
    #
    #     itemlist.append(
    #         Item(
    #             channel=item.channel,
    #             contentType="episode",
    #             action="episodios",
    #             title=title,
    #             url=scrapedurl,
    #             fulltitle=title,
    #             show=showtitle,
    #             thumbnail=""))
    #
    # tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    data = httptools.downloadpage(host + "/index.php?search=1&key=%s" % texto).data
    jsondata = jsontools.load(data)

    for title in jsondata:
        data = str(httptools.downloadpage("%s/templates/header?check=1" % host, post="typeahead=%s" % title).data)

        if 'Anime non esistente' in data:
            continue
        else:
            title = title.replace('(ita)','(ITA)')
            showtitle = title
            if '(ITA)' in title:
                title = title.replace('(ITA)', '').strip()
                showtitle = title
                title += ' ' + support.typo(' (ITA)')

            url = "%s/anime/%s" % (host, data)
            logger.debug(title)
            logger.debug(url)

            itemlist.append(
                Item(
                    channel=item.channel,
                    contentType="episode",
                    action="episodios",
                    title=title,
                    url=url,
                    fulltitle=title,
                    show=showtitle,
                    thumbnail=""))

    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def search(item, texto):
    logger.info(item.channel + " search")
    itemlist = []

    try:
        return search_anime(item, texto)

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

    alphabet = dict()

    # Scarico la pagina
    data = httptools.downloadpage(item.url).data

    # Articoli
    patron = r'<a href="([^"]+)"[^>]*?>[^>]*?>(.+?)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for i, (scrapedurl, scrapedtitle) in enumerate(matches):
        letter = scrapedtitle[0].upper()
        if letter not in alphabet:
            alphabet[letter] = []
        alphabet[letter].append(scrapedurl+'||'+scrapedtitle)

    for letter in sorted(alphabet):
        itemlist.append(
            Item(channel=item.channel,
                 action="lista_anime",
                 url='\n\n'.join(alphabet[letter]),
                 title=letter,
                 fulltitle=letter))

    return itemlist

# ================================================================================================================
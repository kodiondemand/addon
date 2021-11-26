# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per cineblog01
# ------------------------------------------------------------

import re

from core import scrapertools, httptools, servertools, support
from platformcode import logger, config


# def findhost(url):
#     host = httptools.downloadpage(url, follow_redirect=True).url
#     if host == 'https://cb01.uno/':
#         host = support.match(host, patron=r'<a href="([^"]+)').match
#     return host


host = config.get_channel_url()
headers = [['Referer', host]]


@support.menu
def mainlist(item):
    film = [
        ('HD', ['', 'menu', 'Film HD Streaming']),
        ('Generi', ['', 'menu', 'Film per Genere']),
        ('Anni', ['', 'menu', 'Film per Anno']),
        ('Paese', ['', 'menu', 'Film per Paese']),
        ('Ultimi Aggiornati', ['/ultimi-100-film-aggiornati/', 'movies', 'newest']),
        ('Ultimi Aggiunti', ['/lista-film-ultimi-100-film-aggiunti/', 'movies', 'newest'])
    ]
    tvshow = ['/serietv/',
              ('Per Lettera', ['/serietv/', 'menu', 'Serie-Tv per Lettera']),
              ('Per Genere', ['/serietv/', 'menu', 'Serie-Tv per Genere']),
              ('Per anno', ['/serietv/', 'menu', 'Serie-Tv per Anno']),
              ('Ultime Aggiornate', ['/serietv/ultime-100-serie-tv-aggiornate/', 'movies', 'newest'])
              ]
    docu = [('Documentari {bullet bold}', ['/category/documentario/', 'movies']),
            ('HD {submenu} {documentari}', ['/category/hd-alta-definizione/documentario-hd/', 'movies'])
            ]

    return locals()


@support.scrape
def menu(item):
    patronBlock = item.args + r'<span.*?><\/span>.*?<ul.*?>(?P<block>.*?)<\/ul>'
    patronMenu = r'href="?(?P<url>[^">]+)"?>(?P<title>.*?)<\/a>'
    if 'genere' in item.args.lower():
        patronGenreMenu = patronMenu
    action = 'movies'

    return locals()


def newest(category):
    logger.debug(category)

    item = support.Item()
    try:
        if category == 'tvshow':
            item.contentType = 'tvshow'
            item.url = host + '/serietv/'  # aggiornamento-quotidiano-serie-tv/'
        else:
            item.contentType = 'movie'
            item.url = host + '/lista-film-ultimi-100-film-aggiunti/'
            item.args = "newest"
        return movies(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []


def search(item, text):

    logger.info("search", item, text)
    if item.contentType == 'tvshow': item.url = host + '/serietv'
    else: item.url = host
    try:
        item.url = item.url + "/search/" + text.replace(' ', '+')
        return movies(item)

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


@support.scrape
def movies(item):
    # debug = True
    # esclusione degli articoli 'di servizio'
    # curYear = datetime.date.today().year
    # blacklist = ['BENVENUTI', 'Richieste Serie TV', 'CB01.UNO &#x25b6; TROVA L&#8217;INDIRIZZO UFFICIALE ',
    #              'Aggiornamento Quotidiano Serie TV', 'AVVISO!!!',
    #              'Openload: la situazione. Benvenuto Verystream', 'Openload: lo volete ancora?',
    #              'OSCAR ' + str(curYear) + ' &#x25b6; VOTA IL TUO FILM PREFERITO! &#x1f3ac;',
    #              'Auguri di Buon Natale e Felice Anno Nuovo! &#8211; ' + str(curYear) + '!']

    if 'newest' in item.args:
        pagination = True
        patronBlock = r'sequex-page-left(?P<block>.*?)sequex-page-right'
        if '/serietv/' not in item.url:
            patron = r'src="?(?P<thumb>[^ "]+)"? alt="?(?P<title>.*?)(?:\[(?P<quality>[a-zA-Z/]+)\]\s*)?(?:\[(?P<lang>Sub-ITA|ITA)\]\s*)?(?:\[(?P<quality2>[a-zA-Z/]+)\]\s*)?\((?P<year>\d{4})[^\)]*\)[^>]*>.*?<a href=(?:")?(?P<url>[^" ]+)(?:")?.*?rpwe-summary[^>]*>(?P<genre>\w+) [^ ]+ DURATA (?P<duration>[0-9]+)[^ ]+ [^ ]+ [A-Z ]+ (?P<plot>[^<]+)<'
            action = 'findvideos'
        else:
            patron = r'src=(?:")?(?P<thumb>[^ "]+)(?:")? alt=(?:")?(?P<title>.*?)(?: &#8211; \d+&#215;\d+)?(?:>|"| &#8211; )(?:(?P<lang>Sub-ITA|ITA))?[^>]*>.*?<a href=(?:")?(?P<url>[^" ]+)(?:")?.*?rpwe-summary[^>]*>(?P<genre>[^\(]*)\((?P<year>\d{4})[^\)]*\) (?P<plot>[^<]+)<'
            action = 'episodes'

    elif '/serietv/' not in item.url:
        patron = r'(?<!sticky )hentry.*?<div class="card-image">\s*<a[^>]+>\s*<img src="(?P<thumb>[^" ]+)" alt[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+><a href="?(?P<url>[^" >]+)(?:\/|"|\s+)>(?P<title>[^<[(]+)(?:\[(?P<quality>[a-zA-Z/]+)\]\s*)?(?:\[(?P<lang>Sub-ITA|ITA)\]\s*)?(?:\[(?P<quality2>[a-zA-Z/]+)\]\s*)? (?:\((?P<year>[0-9]{4})\))?[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<genre>[^<>&ÃÂ¢ÃÂÃÂ–]+)(?:[^ ]+\s*DURATA\s*(?P<duration>[0-9]+)[^>]+>[^>]+>[^>]+>(?P<plot>[^<>]+))?'
        action = 'findvideos'

    else:
        patron = r'(?<!sticky )hentry.*?card-image[^>]*>\s*<a href=(?:")?(?P<url>[^" >]+)(?:")?\s*>\s*<img src=(?:")?(?P<thumb>[^" ]+)(?:")? alt="(?P<title>.*?)(?: &#8211; \d+&#215;\d+)?(?:"| &#8211; )(?:(?P<lang>Sub-ITA|ITA))?[^>]*>[^>]+>[^>]+>[^>]*>[^>]+>[^>]+>[^>]*>[^>]+>[^>]+>[^>]*>[^>]+>[^>]+>[^>]*>(?P<genre>[^\(]+)\((?P<year>\d{4})[^>]*>[^>]+>[^>]+>[^>]+>(?:<p>)?(?P<plot>[^<]+)'
        action = 'episodes'
        item.contentType = 'tvshow'

    patronNext = '<a class="?page-link"? href="?([^>"]+)"?><i class="fa fa-angle-right">'
    patronTotalPages = '(\d+[\.]?\d+)</option>\s*</sele'

    def itemHook(item):
        if item.quality2:
            item.quality = item.quality2
            item.title += support.typo(item.quality2, '_ [] color kod')
        return item

    return locals()



def episodes(item):
    @support.scrape
    def listed(item, data):
        actLike = 'episodes'
        disableAll = True

        patronBlock = r'(?P<block>sp-head[^>]+>\s*(?:STAGION[EI]\s*(?:(?:DA)?\s*[0-9]+\s*A)?\s*[0-9]+|MINISSERIE)(?::\s*PARTE\s*[0-9]+)? - (?P<lang>[^-<]+)(?:- (?P<quality>[^-<]+))?.*?<\/div>.*?)spdiv[^>]*>'
        patron = r'(?:/>|<p>|<strong>)(?P<data>.*?(?P<episode>[0-9]+(?:&#215;|ÃÂ)[0-9]+)\s*(?P<title2>.*?)?(?:\s*&#8211;|\s*-|\s*<).*?)(?:<\/p>|<br)'

        return locals()

    @support.scrape
    def folder(item, data):
         # Quando c'è un link ad una cartella contenente più stagioni

        actLike = 'episodes'
        disableAll = True
        sceneTitle = True

        folderUrl = scrapertools.find_single_match(data, r'TUTT[EA] L[EA] \w+\s+(?:&#8211;|-)\s+<a href="?([^" ]+)')
        data = httptools.downloadpage(folderUrl, disable_directIP=True).data
        patron = r'<td>(?P<title>[^<]+)<td><a [^>]+href="(?P<folderdata>[^"]+)[^>]+>'

        return locals()


    data = support.match(item.url, headers=headers).data

    itemlist = listed(item, data)
    itemlist.extend(folder(item, data) if 'TUTTE LE' in data or 'TUTTA LA' in data else [])

    itemDict = {'ITA':{}, 'Sub-ITA':{}}
    seasons = []

    for it in itemlist:
        it.contentType = 'episode'
        if it.contentSeason and it.contentSeason not in seasons:
            seasons.append(it.contentSeason)
            itemDict['ITA'][it.contentSeason] = []
            itemDict['Sub-ITA'][it.contentSeason] = []
        if it.contentSeason:
            if not it.contentLanguage: it.contentLanguage = 'ITA'
            itemDict[it.contentLanguage][it.contentSeason].append(it)


    itlist = []
    for season in sorted(seasons):
        itlist.extend(sorted(itemDict['ITA'].get(season, []), key=lambda it: (it.contentSeason, it.contentEpisodeNumber)))
        itlist.extend(sorted(itemDict['Sub-ITA'].get(season, []), key=lambda it: (it.contentSeason, it.contentEpisodeNumber)))
    itemlist = itlist

    if not support.stackCheck(['add_tvshow', 'get_episodes', 'update', 'find_episodes']):
        if len(seasons) > 1:
            itemlist = support.season_pagination(itemlist, item, [], 'episodes')
        else:
            itemlist = support.pagination(itemlist, item, 'episodes')
        if config.getSetting('episode_info'):
            support.tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
        support.videolibrary(itemlist, item)
        support.download(itemlist, item)

    return itemlist


def findvideos(item):
    logger.debug()
    if item.folderdata:
        return support.server(item, data=item.folderdata)
    elif item.data:
        return support.server(item, data=re.sub(r'((?:<p>|<strong>)?[^\d]*\d*(?:&#215;|Ã)[0-9]+[^<]+)', '', item.data))
    else:

        def load_links(itemlist, re_txt, desc_txt, quality=""):
            streaming = scrapertools.find_single_match(data, re_txt).replace('"', '')
            logger.debug('STREAMING', streaming)
            logger.debug('STREAMING=', streaming)
            matches = support.match(streaming, patron = r'<td><a.*?href=([^ ]+) [^>]+>([^<]+)<').matches
            for scrapedurl, scrapedtitle in matches:
                logger.debug("##### findvideos %s ## %s ## %s ##" % (desc_txt, scrapedurl, scrapedtitle))
                itemlist.append(item.clone(action="play", title=scrapedtitle, url=scrapedurl, server=scrapedtitle, quality=quality))

        logger.debug()

        itemlist = []

        # Carica la pagina
        data = httptools.downloadpage(item.url).data
        data = re.sub('\n|\t', '', data)

        # Estrae i contenuti - Streaming
        load_links(itemlist, '<strong>Streamin?g:</strong>(.*?)cbtable', "Streaming", "SD")

        # Estrae i contenuti - Streaming HD
        load_links(itemlist, '<strong>Streamin?g HD[^<]+</strong>(.*?)cbtable', "Streaming HD", "HD")

        # Estrae i contenuti - Streaming 3D
        load_links(itemlist, '<strong>Streamin?g 3D[^<]+</strong>(.*?)cbtable', "Streaming 3D")

        itemlist = support.server(item, itemlist=itemlist)
        # Extract the quality format
        patronvideos = r'([\w.]+)</strong></div></td>'
        support.addQualityTag(item, itemlist, data, patronvideos)

        return itemlist

        # Estrae i contenuti - Download
        # load_links(itemlist, '<strong>Download:</strong>(.*?)<tableclass=cbtable height=30>', "aqua", "Download")

        # Estrae i contenuti - Download HD
        # load_links(itemlist, '<strong>Download HD[^<]+</strong>(.*?)<tableclass=cbtable width=100% height=20>', "azure", "Download HD")


def play(item):
    logger.debug()
    return servertools.find_video_items(item, data=item.url)

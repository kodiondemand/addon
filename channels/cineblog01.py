# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per cineblog01
# ------------------------------------------------------------
import re

from core import scrapertools, httptools, servertools, support
from platformcode import logger, config


def findhost(url):
    host = httptools.downloadpage(url, follow_redirect=True).url
    if host == 'https://cb01.uno/':
        host = support.match(host, patron=r'<a href="([^"]+)').match
    return host


host = config.get_channel_url(findhost)
headers = [['Referer', host]]


@support.menu
def mainlist(item):
    film = [
        ('HD', ['', 'menu', 'Film HD Streaming']),
        ('Genere', ['', 'menu', 'Film per Genere']),
        ('Anni', ['', 'menu', 'Film per Anno']),
        ('Popolari per Genere', ['', 'menu', 'Film Popolari']),
        ('Ultimi Aggiunti', ['/ultimi-100-film-aggiunti/', 'peliculas', 'newest']),
        ('Popolari', ['/category/film-popolari/']),
        ('Italiani', ['/category/nazione/italia/'])
        # ('Film in Lista', ['/lista-film/', 'peliculas', 'newest'])
    ]
    tvshow = ['/serietv/',
              ('Per Lettera', ['/serietv/', 'menu', 'Serie-TV x Lettera']),
              ('Per Genere', ['/serietv/', 'menu', 'Serie-TV x Genere']),
              ('Per anno', ['/serietv/', 'menu', 'Serie-TV x Anno']),
              ('Ultime Aggiunte', ['/serietv/ultime-100-serie-tv-aggiunte/', 'peliculas', 'newest'])
              ]
    docu = [('Documentari {bullet bold}', ['/category/documentario/', 'peliculas']),
            ('HD {submenu} {documentari}', ['/category/hd-alta-definizione/documentario-hd/', 'peliculas'])
            ]

    return locals()


@support.scrape
def menu(item):
    # debug = True
    patronBlock = item.args + r'<span.*?><\/span>.*?<ul.*?>(?P<block>.*?)<\/ul>'
    patronMenu = r'href="?(?P<url>[^">]+)"?[^>]+>(?P<title>[^<Â»]+)'
    action = 'peliculas'

    return locals()


def newest(categoria):
    support.info(categoria)

    item = support.Item()
    try:
        if categoria == "series":
            item.contentType = 'tvshow'
            item.url = host + '/serietv/'  # aggiornamento-quotidiano-serie-tv/'
        else:
            item.contentType = 'movie'
            item.url = host + '/ultimi-100-film-aggiunti/'
            item.args = "newest"
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []


def search(item, text):
    logger.info("search", text)
    if item.contentType == 'tvshow': item.url = host + '/serietv'
    else: item.url = host
    try:
        item.url = item.url + "/search/" + text.replace(' ', '+')
        return peliculas(item)

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


@support.scrape
def peliculas(item):
    # debug = True
    # esclusione degli articoli 'di servizio'
    # curYear = datetime.date.today().year
    # blacklist = ['BENVENUTI', 'Richieste Serie TV', 'CB01.UNO &#x25b6; TROVA L&#8217;INDIRIZZO UFFICIALE ',
    #              'Aggiornamento Quotidiano Serie TV', 'AVVISO!!!',
    #              'Openload: la situazione. Benvenuto Verystream', 'Openload: lo volete ancora?',
    #              'OSCAR ' + str(curYear) + ' &#x25b6; VOTA IL TUO FILM PREFERITO! &#x1f3ac;',
    #              'Auguri di Buon Natale e Felice Anno Nuovo! &#8211; ' + str(curYear) + '!']

    if 'newest' in item.args:
        pagination = ''
        patronBlock = r'sequex-page-left(?P<block>.*?)sequex-page-right'
        if '/serietv/' not in item.url:
            patron = r'src="?(?P<thumb>[^ "]+)"? alt="?(?P<title>.*?)(?:\[(?P<quality>[a-zA-Z]+(?:[/]?3D)?)\]\s*)?(?:\[(?P<lang>Sub-ITA|ITA)\]\s*)?(?:\[(?P<quality2>[a-zA-Z]+(?:[/]?3D)?)\]\s*)?\((?P<year>\d{4})[^\)]*\)[^>]*>.*?<a href=(?:")?(?P<url>[^" ]+)(?:")?.*?rpwe-summary[^>]*>(?P<genre>\w+) [^ ]+ DURATA (?P<duration>[0-9]+)[^ ]+ [^ ]+ [A-Z ]+ (?P<plot>[^<]+)<'
            action = 'findvideos'
        else:
            patron = r'src=(?:")?(?P<thumb>[^ "]+)(?:")? alt=(?:")?(?P<title>.*?)(?: &#8211; \d+&#215;\d+)?(?:>|"| &#8211; )(?:(?P<lang>Sub-ITA|ITA))?[^>]*>.*?<a href=(?:")?(?P<url>[^" ]+)(?:")?.*?rpwe-summary[^>]*>(?P<genre>[^\(]*)\((?P<year>\d{4})[^\)]*\) (?P<plot>[^<]+)<'
            action = 'episodios'

    elif '/serietv/' not in item.url:
        patron = r'(?<!sticky )hentry.*?<div class="card-image">\s*<a[^>]+>\s*<img src="(?P<thumb>[^" ]+)" alt[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+><a href="?(?P<url>[^" >]+)(?:\/|"|\s+)>(?P<title>[^<[(]+)(?:\[(?P<quality>[a-zA-Z]+(?:[/]?3D)?)\]\s*)?(?:\[(?P<lang>Sub-ITA|ITA)\]\s*)?(?:\[(?P<quality2>[a-zA-Z/]+)\]\s*)? (?:\((?P<year>[0-9]{4})\))?[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<genre>[^<>&ÃÂ¢ÃÂÃÂ–]+)(?:[^ ]+\s*DURATA\s*(?P<duration>[0-9]+)[^>]+>[^>]+>[^>]+>(?P<plot>[^<>]+))?'
        action = 'findvideos'

    else:
        patron = r'(?<!sticky )hentry.*?card-image[^>]*>\s*<a href=(?:")?(?P<url>[^" >]+)(?:")?\s*>\s*<img src=(?:")?(?P<thumb>[^" ]+)(?:")? alt="(?P<title>.*?)(?: &#8211; \d+&#215;\d+)?(?:"| &#8211; )(?:(?P<lang>Sub-ITA|ITA))?[^>]*>[^>]+>[^>]+>[^>]*>[^>]+>[^>]+>[^>]*>[^>]+>[^>]+>[^>]*>[^>]+>[^>]+>[^>]*>(?P<genre>[^\(]+)\((?P<year>\d{4})[^>]*>[^>]+>[^>]+>[^>]+>(?:<p>)?(?P<plot>[^<]+)'
        action = 'episodios'
        item.contentType = 'tvshow'

    patronNext = '<a class="?page-link"? href="?([^>"]+)"?><i class="fa fa-angle-right">'

    def itemHook(item):
        if item.quality2:
            item.quality = item.quality2
            item.title += support.typo(item.quality2, '_ [] color kod')
        return item

    return locals()


@support.scrape
def episodios(item):
    @support.scrape
    def folder(item, url):
        """
            Quando c'è un link ad una cartella contenente più stagioni
        """
        if url:
            data = support.match(url).data
            actLike = 'episodios'
            addVideolibrary = False
            downloadEnabled = False

            patron = r'<td>(?P<title>[^<]+)<td><a [^>]+href="(?P<url>[^"]+)[^>]+>'
            sceneTitle = True
            # debug = True

            def itemHook(item):
                item.serieFolder = True
                return item
        return locals()

    # debugBlock=True
    data = support.match(item.url, headers=headers).data
    folderItemlist = folder(item, scrapertools.find_single_match(data, r'TUTT[EA] L[EA] \w+\s+(?:&#8211;|-)\s+<a href="?([^" ]+)'))

    patronBlock = r'(?P<block>sp-head[^>]+>\s*(?:STAGION[EI]\s*(?:(?:DA)?\s*[0-9]+\s*A)?\s*[0-9]+|MINISSERIE)(?::\s*PARTE\s*[0-9]+)? - (?P<lang>[^-<]+)(?:- (?P<quality>[^-<]+))?.*?<\/div>.*?)spdiv[^>]*>'
    patron = r'(?:/>|<p>|<strong>)(?P<other>.*?(?P<episode>[0-9]+(?:&#215;|ÃÂ)[0-9]+)\s*(?P<title2>.*?)?(?:\s*&#8211;|\s*-|\s*<).*?)(?:<\/p>|<br)'
    def itemlistHook(itemlist):
        title_dict = {}
        itlist = []
        for i in itemlist:
            i.url = item.url
            i.title = re.sub(r'\.(\D)',' \\1', i.title)
            match = support.match(i.title, patron=r'(\d+.\d+)').match.replace('x','')
            i.order = match
            if match not in title_dict:
                title_dict[match] = i
            elif match in title_dict and i.contentLanguage == title_dict[match].contentLanguage \
                or i.contentLanguage == 'ITA' and not title_dict[match].contentLanguage \
                or title_dict[match].contentLanguage == 'ITA' and not i.contentLanguage:
                title_dict[match].url = i.url
            else:
                title_dict[match + '1'] = i

        for key, value in title_dict.items():
            itlist.append(value)

        itlist = sorted(itlist, key=lambda it: (it.contentLanguage, int(it.order)))

        itlist.extend(folderItemlist)

        return itlist
    return locals()


def findvideos(item):
    if item.serieFolder:
        return support.server(item, data=item.url)
    if item.contentType == "episode":
        return findvid_serie(item)

    def load_links(itemlist, re_txt, desc_txt, quality=""):
        streaming = scrapertools.find_single_match(data, re_txt).replace('"', '')
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

    # Extract the quality format
    patronvideos = r'([\w.]+)</strong></div></td>'
    return support.server(item, itemlist=itemlist, patronTag=patronvideos)

    # Estrae i contenuti - Download
    # load_links(itemlist, '<strong>Download:</strong>(.*?)<tableclass=cbtable height=30>', "aqua", "Download")

    # Estrae i contenuti - Download HD
    # load_links(itemlist, '<strong>Download HD[^<]+</strong>(.*?)<tableclass=cbtable width=100% height=20>', "azure", "Download HD")


def findvid_serie(item):
    logger.debug()
    data = re.sub(r'((?:<p>|<strong>)?[^\d]*\d*(?:&#215;|Ã)[0-9]+[^<]+)', '', item.other)

    return support.server(item, data=data)


def play(item):
    logger.debug()
    return servertools.find_video_items(item, data=item.url)

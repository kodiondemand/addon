# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per cineblog01
# ------------------------------------------------------------

import re

from core import scrapertools, httptools, servertools, tmdb, support
from core.item import Item
from lib import unshortenit
from platformcode import logger, config


def findhost():
    host = httptools.downloadpage('https://cb01.uno/', follow_redirect=True).url
    if host == 'https://cb01.uno/':
        host = support.match(host, patron=r'<a href="([^"]+)', debug=True).match
    return host


host = config.get_channel_url(findhost)
headers = [['Referer', host]]


@support.menu
def mainlist(item):
    film = [
        ('HD', ['', 'menu', 'Film HD Streaming']),
        ('Generi', ['', 'menu', 'Film per Genere']),
        ('Anni', ['', 'menu', 'Film per Anno']),
        ('Paese', ['', 'menu', 'Film per Paese']),
        ('Ultimi Aggiornati', ['/lista-film-ultimi-100-film-aggiornati/', 'peliculas', 'newest']),
        ('Ultimi Aggiunti', ['/lista-film-ultimi-100-film-aggiunti/', 'peliculas', 'newest'])
    ]
    tvshow = ['/serietv/',
              ('Per Lettera', ['/serietv/', 'menu', 'Serie-Tv per Lettera']),
              ('Per Genere', ['/serietv/', 'menu', 'Serie-Tv per Genere']),
              ('Per anno', ['/serietv/', 'menu', 'Serie-Tv per Anno']),
              ('Ultime Aggiornate', ['/serietv/', 'peliculas', 'newest'])
              ]
    docu = [('Documentari {bullet bold}', ['/category/documentario/', 'peliculas']),
            ('HD {submenu} {documentari}', ['category/hd-alta-definizione/documentario-hd/', 'peliculas'])
            ]

    return locals()


@support.scrape
def menu(item):
    patronBlock = item.args + r'<span.*?><\/span>.*?<ul.*?>(?P<block>.*?)<\/ul>'
    patronMenu = r'href="?(?P<url>[^">]+)"?>(?P<title>.*?)<\/a>'
    action = 'peliculas'

    return locals()


def newest(categoria):
    support.log(categoria)

    item = support.Item()
    try:
        if categoria == "series":
            item.contentType = 'tvshow'
            item.url = host + '/serietv/'  # aggiornamento-quotidiano-serie-tv/'
        else:
            item.contentType = 'movie'
            item.url = host + '/lista-film-ultimi-100-film-aggiunti/'
        item.args = "newest"
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("{0}".format(line))
        return []


def search(item, text):
    support.log(item.url, "search", text)

    try:
        item.url = item.url + "/?s=" + text.replace(' ', '+')
        return peliculas(item)

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


@support.scrape
def peliculas(item):
    # esclusione degli articoli 'di servizio'
    blacklist = ['BENVENUTI', 'Richieste Serie TV', 'CB01.UNO &#x25b6; TROVA L&#8217;INDIRIZZO UFFICIALE ',
                 'Aggiornamento Quotidiano Serie TV', 'OSCAR 2019 ▶ CB01.UNO: Vota il tuo film preferito! 🎬',
                 'Openload: la situazione. Benvenuto Verystream', 'Openload: lo volete ancora?',
                 'OSCAR 2020 &#x25b6; VOTA IL TUO FILM PREFERITO! &#x1f3ac;']
    # debug= True
    if 'newest' in item.args:
        if '/serietv/' not in item.url:
            pagination = ''
            patronBlock = r'Ultimi 100 film [^:]+:(?P<block>.*?)<\/td>'
            patron = r'<a href="?(?P<url>[^">]+)"?>(?P<title>[^<([]+)(?:\[(?P<lang>Sub-ITA|B/N|SUB-ITA)\])?\s*(?:\[(?P<quality>HD|SD|HD/3D)\])?\s*\((?P<year>[0-9]{4})\)<\/a>'
            action = 'findvideos'
        else:
            patronBlock = r'Ultime SerieTv aggiornate(?P<block>.*?)Lista'
            patron = r'src=(?:")?(?P<thumb>[^ "]+)(?:")? alt=(?:")?(?P<title>.*?)(?: &#8211; \d+&#215;\d+)?(?:>|"| &#8211; )(?:(?P<lang>Sub-ITA|ITA))?[^>]*>.*?<a href=(?:")?(?P<url>[^" ]+)(?:")?.*?rpwe-summary[^>]*>(?P<genre>[^\(]*)\((?P<year>\d{4})[^\)]*\) (?P<plot>[^<]+)<'
            action = 'episodios'

    elif '/serietv/' not in item.url:
        patron = r'<div class="card-image">\s*<a[^>]+>\s*<img src="(?P<thumb>[^" ]+)" alt[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+><a href="?(?P<url>[^" >]+)(?:\/|"|\s+)>(?P<title>[^<[(]+)(?:\[(?P<quality>[A-Za-z0-9/-]+)])? (?:\((?P<year>[0-9]{4})\))?[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<genre>[^<>&ÃÂ¢ÃÂÃÂ]+)(?:[^ ]+\s*DURATA\s*(?P<duration>[0-9]+)[^>]+>[^>]+>[^>]+>(?P<plot>[^<>]+))?'
        action = 'findvideos'

    else:
        patron = r'card-image[^>]*>\s*<a href=(?:")?(?P<url>[^" >]+)(?:")?\s*>\s*<img src=(?:")?(?P<thumb>[^" ]+)(?:")? alt="(?P<title>.*?)(?: &#8211; \d+&#215;\d+)?(?:"| &#8211; )(?:(?P<lang>Sub-ITA|ITA))?[^>]*>[^>]+>[^>]+>[^>]*>[^>]+>[^>]+>[^>]*>[^>]+>[^>]+>[^>]*>[^>]+>[^>]+>[^>]*>(?P<genre>[^\(]+)\((?P<year>\d{4})[^>]*>[^>]+>[^>]+>[^>]+>(?:<p>)?(?P<plot>[^<]+)'
        action = 'episodios'
        item.contentType = 'tvshow'

    patronNext = '<a class="?page-link"? href="?([^>"]+)"?><i class="fa fa-angle-right">'

    return locals()


@support.scrape
def episodios(item):
    # support.dbg()
    data = support.match(item.url, headers=headers).data
    support.log(data)
    if 'TUTTA LA ' in data:
        folderUrl = scrapertools.find_single_match(data, r'TUTTA LA \w+\s+(?:&#8211;|-)\s+<a href="?([^" ]+)')
        data = httptools.downloadpage(folderUrl).data
        patron = r'<a href="(?P<url>[^"]+)[^>]+>(?P<title>[^<]+)'
        sceneTitle = True
        def itemHook(item):
            item.serieFolder = True
            return item
    else:
        patronBlock = r'(?P<block>sp-head[^>]+>\s*(?:STAGION[EI]\s*(?:DA\s*[0-9]+\s*A)?\s*[0-9]+|MINISERIE) - (?P<lang>[^-<]+)(?:- (?P<quality>[^-<]+))?.*?<\/div>.*?)spdiv[^>]*>'
        patron = r'(?:/>|<p>|<strong>)(?P<url>.*?(?P<episode>[0-9]+(?:&#215;|ÃÂ)[0-9]+)\s*(?P<title2>.*?)?(?:\s*&#8211;|\s*-|\s*<).*?)(?:<\/p>|<br)'
        def itemlistHook(itemlist):
            title_dict = {}
            itlist = []
            for item in itemlist:
                item.title = re.sub(r'\.(\D)',' \\1', item.title)
                match = support.match(item.title, patron=r'(\d+.\d+)').match.replace('x','')
                item.order = match
                if match not in title_dict:
                    title_dict[match] = item
                elif match in title_dict and item.contentLanguage == title_dict[match].contentLanguage \
                    or item.contentLanguage == 'ITA' and not title_dict[match].contentLanguage \
                    or title_dict[match].contentLanguage == 'ITA' and not item.contentLanguage:
                    title_dict[match].url = item.url
                else:
                    title_dict[match + '1'] = item

            for key, value in title_dict.items():
                itlist.append(value)

            return sorted(itlist, key=lambda it: (it.contentLanguage, int(it.order)))
    return locals()


def findvideos(item):
    if item.serieFolder:
        return support.server(item, data=item.url)
    if item.contentType == "episode":
        return findvid_serie(item)

    def load_links(itemlist, re_txt, desc_txt, quality=""):
        streaming = scrapertools.find_single_match(data, re_txt).replace('"', '')
        support.log('STREAMING', streaming)
        support.log('STREAMING=', streaming)
        matches = support.match(streaming, patron = r'<td><a.*?href=([^ ]+) [^>]+>([^<]+)<').matches
        for scrapedurl, scrapedtitle in matches:
            logger.debug("##### findvideos %s ## %s ## %s ##" % (desc_txt, scrapedurl, scrapedtitle))
            itemlist.append(item.clone(action="play", title=scrapedtitle, url=scrapedurl, server=scrapedtitle, quality=quality))

    support.log()

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


def findvid_serie(item):
    def load_vid_series(html, item, itemlist, blktxt):
        support.log('HTML',html)
        # Estrae i contenuti
        matches = support.match(html, patron=r'<a href=(?:")?([^ "]+)[^>]+>(?!<!--)(.*?)(?:</a>|<img)').matches
        for url, server in matches:
            item = item.clone(action="play", title=server, url=url, server=server, quality=blktxt)
            if 'swzz' in item.url: item.url = support.swzz_get_url(item)
            itemlist.append(item)

    support.log()

    itemlist = []

    data = re.sub(r'((?:<p>|<strong>)?[^\d]*\d*(?:&#215;|Ã)[0-9]+[^<]+)', '' ,item.url)

    # Blocks with split
    blk = re.split(r"(?:>\s*)?([A-Za-z\s0-9]*):\s*<", data, re.S)
    blktxt = ""
    for b in blk:
        if b[0:3] == "a h" or b[0:4] == "<a h":
            load_vid_series("<%s>" % b, item, itemlist, blktxt)
            blktxt = ""
        elif len(b.strip()) > 1:
            blktxt = b.strip()

    return support.server(item, itemlist=itemlist)


def play(item):
    support.log()
    return servertools.find_video_items(item, data=item.url)

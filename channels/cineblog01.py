# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per cineblog01
# ------------------------------------------------------------

import re

from core import scrapertoolsV2, httptools, servertools, tmdb, support
from core.item import Item
from lib import unshortenit
from platformcode import logger, config
from specials import autoplay

#impostati dinamicamente da getUrl()
host = ""
headers = ""


def findhost():
    global host, headers
    permUrl = httptools.downloadpage('https://www.cb01.uno/', follow_redirects=False).headers
    host = 'https://www.'+permUrl['location'].replace('https://www.google.it/search?q=site:', '')
    headers = [['Referer', host]]

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['verystream', 'openload', 'streamango', 'wstream']
list_quality = ['HD', 'SD', 'default']

checklinks = config.get_setting('checklinks', 'cineblog01')
checklinks_number = config.get_setting('checklinks_number', 'cineblog01')

# esclusione degli articoli 'di servizio'
blacklist = ['BENVENUTI', 'Richieste Serie TV', 'CB01.UNO &#x25b6; TROVA L&#8217;INDIRIZZO UFFICIALE ',
             'Aggiornamento Quotidiano Serie TV', 'OSCAR 2019 ▶ CB01.UNO: Vota il tuo film preferito! 🎬',
             'Openload: la situazione. Benvenuto Verystream', 'Openload: lo volete ancora?']


@support.menu
def mainlist(item):
    findhost()
    film = ''
    filmSub = [
        ('HD', ['', 'menu', 'Film HD Streaming']),
        ('Generi', ['', 'menu', 'Film per Genere']),
        ('Anni', ['', 'menu', 'Film per Anno'])
    ]
    tvshow = '/serietv/'
    tvshowSub = [
        ('Aggiornamenti serie tv', ['/serietv/aggiornamento-quotidiano-serie-tv/', 'last']),
        ('Per Lettera', ['/serietv/', 'menu', 'Serie-Tv per Lettera']),
        ('Per Genere', ['/serietv/aggiornamento-quotidiano-serie-tv/', 'menu', 'Serie-Tv per Genere']),
        ('Per anno', ['/serietv/aggiornamento-quotidiano-serie-tv/', 'menu', 'Serie-Tv per Anno'])
    ]

    return locals()


def menu(item):
    findhost()
    itemlist= []
    data = httptools.downloadpage(item.url, headers=headers).data
    data = re.sub('\n|\t', '', data)
    block = scrapertoolsV2.find_single_match(data, item.args + r'<span.*?><\/span>.*?<ul.*?>(.*?)<\/ul>')
    support.log('MENU BLOCK= ',block)
    patron = r'href="?([^">]+)"?>(.*?)<\/a>'
    matches = re.compile(patron, re.DOTALL).findall(block)
    for scrapedurl, scrapedtitle in matches:
        itemlist.append(
            Item(
                channel=item.channel,
                title=scrapedtitle,
                contentType=item.contentType,
                action='peliculas',
                url=host + scrapedurl
            )
        )
    
    return support.thumb(itemlist)


def search(item, text):
    support.log(item.url, "search" ,text)

    try:
        item.url = item.url + "/?s=" + text
        return peliculas(item)

    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    findhost()
    itemlist = []
    item = Item()
    item.contentType = 'movie'
    item.url = host + '/lista-film-ultimi-100-film-aggiunti/'
    return support.scrape(item, r'<a href=([^>]+)>([^<([]+)(?:\[([A-Z]+)\])?\s\(([0-9]{4})\)<\/a>',
                   ['url', 'title', 'quality', 'year'],
                   patronBlock=r'Ultimi 100 film aggiunti:.*?<\/td>')


def last(item):
    support.log()
    
    itemlist = []
    infoLabels = {}
    quality = ''
    PERPAGE = 20
    page = 1
    if item.page:
        page = item.page

    if item.contentType == 'tvshow':
        matches = support.match(item, r'<a href="([^">]+)".*?>([^(:(|[)]+)([^<]+)<\/a>', '<article class="sequex-post-content.*?</article>', headers)[0]
    else:
        matches = support.match(item, r'<a href=([^>]+)>([^(:(|[)]+)([^<]+)<\/a>', r'<strong>Ultimi 100 film Aggiornati:<\/a><\/strong>(.*?)<td>', headers)[0]

    for i, (url, title, info) in enumerate(matches):
        if (page - 1) * PERPAGE > i: continue
        if i >= page * PERPAGE: break
        add = True
        title = title.rstrip()
        if item.contentType == 'tvshow':
            for i in itemlist:
                if i.url == url: # togliamo i doppi
                    add = False
        else:
            infoLabels['year'] = scrapertoolsV2.find_single_match(info, r'\(([0-9]+)\)')
            quality = scrapertoolsV2.find_single_match(info, r'\[([A-Z]+)\]')

        if quality:
            longtitle = title + support.typo(quality,'_ [] color kod')
        else:
            longtitle = title

        if add:
            itemlist.append(
                    Item(channel=item.channel,
                        action='findvideos' if item.contentType == 'movie' else 'episodios',
                        contentType=item.contentType,
                        title=longtitle,
                        fulltitle=title,
                        show=title,
                        quality=quality,
                        url=url,
                        infoLabels=infoLabels
                        )
                )
    support.pagination(itemlist, item, page, PERPAGE)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


@support.scrape
def peliculas(item):
    support.log()
    if item.contentType == 'movie' or '/serietv/' not in item.url:
        patron = r'<div class="?card-image"?>.*?<img src="?(?P<thumb>[^" ]+)"? alt.*?<a href="?(?P<url>[^" >]+)(?:\/|")>(?P<title>[^<[(]+)(?:\[(?P<quality>[A-Za-z0-9/-]+)])? (?:\((?P<year>[0-9]{4})\))?.*?<strong>(?P<genre>[^<>&]+).*?DURATA (?P<duration>[0-9]+).*?<br(?: /)?>(?P<plot>[^<>]+)'
        action = 'findvideos'
    else:
        patron = r'div class="card-image">.*?<img src="(?P<thumb>[^ ]+)" alt.*?<a href="(?P<url>[^ >]+)">(?P<title>[^<[(]+)<\/a>.*?<strong><span style="[^"]+">(?P<genre>[^<>0-9(]+)\((?P<year>[0-9]{4}).*?</(?:p|div)>(?P<plot>.*?)</div'
        listGroups = ['thumb', 'url', 'title', 'genre', 'year', 'plot']
        action = 'episodios'

    patronBlock=[r'<div class="?sequex-page-left"?>(.*?)<aside class="?sequex-page-right"?>',
                                              '<div class="?card-image"?>.*?(?=<div class="?card-image"?>|<div class="?rating"?>)']
    patronNext='<a class="?page-link"? href="?([^>]+)"?><i class="fa fa-angle-right">'

    return locals()


def episodios(item):
    itemlist = []

    data = httptools.downloadpage(item.url).data
    matches = scrapertoolsV2.find_multiple_matches(data,
                                                   r'(<div class="sp-head[a-z ]*?" title="Espandi">[^<>]*?</div>.*?)<div class="spdiv">\[riduci\]</div>')

    for match in matches:
        support.log(match)
        blocks = scrapertoolsV2.find_multiple_matches(match, '(?:<p>)(.*?)(?:</p>|<br)')
        season = scrapertoolsV2.find_single_match(match, r'title="Espandi">.*?STAGIONE\s+\d+([^<>]+)').strip()

        for block in blocks:
            episode = scrapertoolsV2.find_single_match(block, r'([0-9]+(?:&#215;|×)[0-9]+)').strip()
            seasons_n = scrapertoolsV2.find_single_match(block, r'<strong>STAGIONE\s+\d+([^<>]+)').strip()

            if seasons_n:
                season = seasons_n

            if not episode: continue

            season = re.sub(r'&#8211;|–', "-", season)
            itemlist.append(
                Item(channel=item.channel,
                     action="findvideos",
                     contentType='episode',
                     title="[B]" + episode + "[/B] " + season,
                     fulltitle=episode + " " + season,
                     show=episode + " " + season,
                     url=block,
                     extra=item.extra,
                     thumbnail=item.thumbnail,
                     infoLabels=item.infoLabels
                     ))

    support.videolibrary(itemlist, item)

    return itemlist


def findvideos(item):
    findhost()

    if item.contentType == "episode":
        return findvid_serie(item)

    def load_links(itemlist, re_txt, color, desc_txt, quality=""):
        streaming = scrapertoolsV2.find_single_match(data, re_txt).replace('"', '')
        support.log('STREAMING=', streaming)
        patron = '<td><a.*?href=(.*?) (?:target|rel)[^>]+>([^<]+)<'
        matches = re.compile(patron, re.DOTALL).findall(streaming)
        for scrapedurl, scrapedtitle in matches:
            logger.debug("##### findvideos %s ## %s ## %s ##" % (desc_txt, scrapedurl, scrapedtitle))
            itemlist.append(
                Item(channel=item.channel,
                     action="play",
                     title=scrapedtitle,
                     url=scrapedurl,
                     server=scrapedtitle,
                     fulltitle=item.fulltitle,
                     thumbnail=item.thumbnail,
                     show=item.show,
                     quality=quality,
                     contentType=item.contentType,
                     folder=False))

    support.log()

    itemlist = []

    # Carica la pagina
    data = httptools.downloadpage(item.url).data
    data = re.sub('\n|\t','',data)

    # Extract the quality format
    patronvideos = '>([^<]+)</strong></div>'
    matches = re.compile(patronvideos, re.DOTALL).finditer(data)
    QualityStr = ""
    for match in matches:
        QualityStr = scrapertoolsV2.decodeHtmlentities(match.group(1))[6:]

    # Estrae i contenuti - Streaming
    load_links(itemlist, '<strong>Streaming:</strong>(.*?)<tableclass=cbtable height=30>', "orange", "Streaming", "SD")

    # Estrae i contenuti - Streaming HD
    load_links(itemlist, '<strong>Streaming HD[^<]+</strong>(.*?)<tableclass=cbtable height=30>', "yellow", "Streaming HD", "HD")

    # Estrae i contenuti - Streaming 3D
    load_links(itemlist, '<strong>Streaming 3D[^<]+</strong>(.*?)<tableclass=cbtable height=30>', "pink", "Streaming 3D")

    return support.server(item, itemlist=itemlist)

    # Estrae i contenuti - Download
    # load_links(itemlist, '<strong>Download:</strong>(.*?)<tableclass=cbtable height=30>', "aqua", "Download")

    # Estrae i contenuti - Download HD
    # load_links(itemlist, '<strong>Download HD[^<]+</strong>(.*?)<tableclass=cbtable width=100% height=20>', "azure", "Download HD")


def findvid_serie(item):
    def load_vid_series(html, item, itemlist, blktxt):
        logger.info('HTML' + html)
        patron = '<a href="([^"]+)"[^=]+="_blank"[^>]+>(.*?)</a>'
        # Estrae i contenuti
        matches = re.compile(patron, re.DOTALL).finditer(html)
        for match in matches:
            scrapedurl = match.group(1)
            scrapedtitle = match.group(2)
            # title = item.title + " [COLOR blue][" + scrapedtitle + "][/COLOR]"
            itemlist.append(
                Item(channel=item.channel,
                     action="play",
                     title=scrapedtitle,
                     url=scrapedurl,
                     server=scrapedtitle,
                     fulltitle=item.fulltitle,
                     show=item.show,
                     contentType=item.contentType,
                     folder=False))

    support.log()

    itemlist = []
    lnkblk = []
    lnkblkp = []

    data = item.url

    # First blocks of links
    if data[0:data.find('<a')].find(':') > 0:
        lnkblk.append(data[data.find(' - ') + 3:data[0:data.find('<a')].find(':') + 1])
        lnkblkp.append(data.find(' - ') + 3)
    else:
        lnkblk.append(' ')
        lnkblkp.append(data.find('<a'))

    # Find new blocks of links
    patron = r'<a\s[^>]+>[^<]+</a>([^<]+)'
    matches = re.compile(patron, re.DOTALL).finditer(data)
    for match in matches:
        sep = match.group(1)
        if sep != ' - ':
            lnkblk.append(sep)

    i = 0
    if len(lnkblk) > 1:
        for lb in lnkblk[1:]:
            lnkblkp.append(data.find(lb, lnkblkp[i] + len(lnkblk[i])))
            i = i + 1

    for i in range(0, len(lnkblk)):
        if i == len(lnkblk) - 1:
            load_vid_series(data[lnkblkp[i]:], item, itemlist, lnkblk[i])
        else:
            load_vid_series(data[lnkblkp[i]:lnkblkp[i + 1]], item, itemlist, lnkblk[i])

    return support.server(item, itemlist=itemlist)


def play(item):
    support.log()
    itemlist = []
    ### Handling new cb01 wrapper
    if host[9:] + "/film/" in item.url:
        iurl = httptools.downloadpage(item.url, only_headers=True, follow_redirects=False).headers.get("location", "")
        support.log("/film/ wrapper: ", iurl)
        if iurl:
            item.url = iurl

    if '/goto/' in item.url:
        item.url = item.url.split('/goto/')[-1].decode('base64')

    item.url = item.url.replace('http://cineblog01.uno', 'http://k4pp4.pw')

    logger.debug("##############################################################")
    if "go.php" in item.url:
        data = httptools.downloadpage(item.url).data
        if "window.location.href" in data:
            try:
                data = scrapertoolsV2.find_single_match(data, 'window.location.href = "([^"]+)";')
            except IndexError:
                data = httptools.downloadpage(item.url, only_headers=True, follow_redirects=False).headers.get("location", "")
            data, c = unshortenit.unwrap_30x_only(data)
        else:
            data = scrapertoolsV2.find_single_match(data, r'<a href="([^"]+)".*?class="btn-wrapper">.*?licca.*?</a>')
        
        logger.debug("##### play go.php data ##\n%s\n##" % data)
    else:
        data = support.swzz_get_url(item)

    return servertools.find_video_items(data=data)

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
    permUrl = httptools.downloadpage('https://www.cb01.uno/', follow_redirects=False).headers
    if 'google' in permUrl['location']:
        host = permUrl['location'].replace('https://www.google.it/search?q=site:', '')
    else:
        host = permUrl['location']
    return host

host = config.get_channel_url(findhost)
headers = [['Referer', host]]

list_servers = ['mixdrop', 'akstream', 'wstream', 'backin']
list_quality = ['HD', 'SD', 'default']

checklinks = config.get_setting('checklinks', 'cineblog01')
checklinks_number = config.get_setting('checklinks_number', 'cineblog01')


@support.menu
def mainlist(item):
    film = [
        ('HD', ['', 'menu', 'Film HD Streaming']),
        ('Generi', ['', 'menu', 'Film per Genere']),
        ('Anni', ['', 'menu', 'Film per Anno']),
        ('Paese', ['', 'menu', 'Film per Paese']),        
        ('Ultimi Aggiornati',['/lista-film-ultimi-100-film-aggiornati/', 'peliculas', 'newest']),
        ('Ultimi Aggiunti', ['/lista-film-ultimi-100-film-aggiunti/', 'peliculas', 'newest'])
    ]
    tvshow = ['/serietv/',
        ('Per Lettera', ['/serietv/', 'menu', 'Serie-Tv per Lettera']),
        ('Per Genere', ['/serietv/', 'menu', 'Serie-Tv per Genere']),
        ('Per anno', ['/serietv/', 'menu', 'Serie-Tv per Anno']),
        ('Ultime Aggiornate', ['/serietv/', 'peliculas', 'newest'])
    ]
    docu = [('Documentari bullet bold', ['/category/documentario/', 'peliculas']),
            ('HD submenu', ['category/hd-alta-definizione/documentario-hd/', 'peliculas'])
    ]

    return locals()


@support.scrape
def menu(item):
    patronBlock = item.args + r'<span.*?><\/span>.*?<ul.*?>(?P<block>.*?)<\/ul>'
    patronMenu = r'href="?(?P<url>[^">]+)"?>(?P<title>.*?)<\/a>'
    action = 'peliculas'

    return locals()


# @support.scrape
# def newest(categoria):
#     
#     # debug = True
#     patron = r'<a href="?(?P<url>[^">]+)"?>(?P<title>[^<([]+)(?:\[(?P<lang>Sub-ITA|B/N|SUB-ITA)\])?\s*(?:\[(?P<quality>HD|SD|HD/3D)\])?\s*\((?P<year>[0-9]{4})\)<\/a>'

#     if type(categoria) != Item:
#         item = Item()
#     else:
#         item = categoria
#         categoria = 'series' if item.contentType != 'movie' else 'movie'
#     pagination = 20

#     if categoria == 'series':
#         item.contentType = 'tvshow'
#         action = 'episodios'
#         item.url = host + 'serietv/aggiornamento-quotidiano-serie-tv/'
#         patronBlock = r'<article class="sequex-post-content">(?P<block>.*?)</article>'
#         patron = '<a href="(?P<url>[^"]+)".*?>(?P<title>[^<([|]+).*?(?P<lang>ITA|SUB-ITA)?</a'
#     else:
#         item.contentType = 'movie'
#         item.url = host + '/lista-film-ultimi-100-film-aggiunti/'
#         patronBlock = r'Ultimi 100 film aggiunti:(?P<block>.*?)<\/td>'
#     # else:
#     #     patronBlock = r'Ultimi 100 film Aggiornati:(?P<block>.*?)<\/td>'
#     #     item = categoria

#     return locals()


def newest(categoria):
    support.log(categoria)
    
    item = support.Item()
    try:
        if categoria == "series":
            item.contentType = 'tvshow'
            item.url = host + '/serietv/' # aggiornamento-quotidiano-serie-tv/'
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
                 'Openload: la situazione. Benvenuto Verystream', 'Openload: lo volete ancora?', 'OSCAR 2020 &#x25b6; VOTA IL TUO FILM PREFERITO! &#x1f3ac;']
    # debug = True
    if 'newest' in item.args:
        if '/serietv/' not in item.url:
            pagination = ''
            patronBlock = r'Ultimi 100 film [^:]+:(?P<block>.*?)<\/td>'
            patron = r'<a href="?(?P<url>[^">]+)"?>(?P<title>[^<([]+)(?:\[(?P<lang>Sub-ITA|B/N|SUB-ITA)\])?\s*(?:\[(?P<quality>HD|SD|HD/3D)\])?\s*\((?P<year>[0-9]{4})\)<\/a>'
            action = 'findvideos'
        else:
            patronBlock = r'Ultime SerieTv aggiornate(?P<block>.*?)Lista'
            patron = r'src="(?P<thumb>[^"]+)" alt="(?P<title>.*?)(?: &#8211; \d+&#215;\d+)?(?:"| &#8211; )(?:(?P<lang>Sub-ITA|ITA))?[^>]*>[^>]+>[^>]+><a href="(?P<url>[^"]+)".*?<div class="rpwe-summary">.*?\((?P<year>\d{4})[^\)]*\) (?P<plot>[^<]+)<'
            action = 'episodios'
    elif '/serietv/' not in item.url:
        patron = r'<div class="?card-image"?>.*?<img src="?(?P<thumb>[^" ]+)"? alt[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+><a href="?(?P<url>[^" >]+)(?:\/|"|\s+)>(?P<title>[^<[(]+)(?:\[(?P<quality>[A-Za-z0-9/-]+)])? (?:\((?P<year>[0-9]{4})\))?[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<genre>[^<>&â]+)(?:[^ ]+\s*DURATA\s*(?P<duration>[0-9]+)[^>]+>[^>]+>[^>]+>(?P<plot>[^<>]+))?'
        # patron = r'<div class="?card-image"?>.*?<img src="?(?P<thumb>[^" ]+)"? alt.*?<a href="?(?P<url>[^" >]+)(?:\/|"|\s+)>(?P<title>[^<[(]+)(?:\[(?P<quality>[A-Za-z0-9/-]+)])? (?:\((?P<year>[0-9]{4})\))?.*?<strong>(?P<genre>[^<>&–]+).*?DURATA (?P<duration>[0-9]+).*?<br(?: /)?>(?P<plot>[^<>]+)'
        action = 'findvideos'
    else:
        # debug = True
        patron = r'div class="card-image">.*?<img src="(?P<thumb>[^ ]+)" alt.*?<a href="(?P<url>[^ >]+)">(?P<title>.*?)(?:&#.*?)?(?P<lang>(?:[Ss][Uu][Bb]-)?[Ii][Tt][Aa])?<\/a>.*?(?:<strong><span style="[^"]+">(?P<genre>[^<>0-9(]+)\((?P<year>[0-9]{4}).*?</(?:p|div)>(?P<plot>.*?))?</div'
        action = 'episodios'
        item.contentType = 'tvshow'

    # patronBlock=[r'<div class="?sequex-page-left"?>(?P<block>.*?)<aside class="?sequex-page-right"?>',
    #                                           '<div class="?card-image"?>.*?(?=<div class="?card-image"?>|<div class="?rating"?>)']
    if 'newest' not in item.args: patronNext='<a class="?page-link"? href="?([^>]+)"?><i class="fa fa-angle-right">'

    return locals()


@support.scrape
def episodios(item):
    patronBlock = r'(?P<block><div class="sp-head[a-z ]*?" title="Espandi">\s*(?:STAGION[EI]\s*(?:DA\s*[0-9]+\s*A)?\s*[0-9]+|MINISERIE) - (?P<lang>[^-<]+)(?:- (?P<quality>[^-<]+))?.*?[^<>]*?<\/div>.*?)<div class="spdiv">\[riduci\]<\/div>'
    patron = '(?:<p>|<strong>)(?P<episode>[0-9]+(?:&#215;|×)[0-9]+)\s*(?P<title2>[^&<]*)?(?:&#8211;|-)?\s*(?P<url>.*?)(?:<\/p>|<br)'

    return locals()


def findvideos(item):
    

    if item.contentType == "episode":
        return findvid_serie(item)

    def load_links(itemlist, re_txt, color, desc_txt, quality=""):
        streaming = scrapertools.find_single_match(data, re_txt).replace('"', '')
        support.log('STREAMING',streaming)
        support.log('STREAMING=', streaming)
        # patron = '<td><a.*?href=(.*?) (?:target|rel)[^>]+>([^<]+)<'
        patron = '<td><a.*?href=([^ ]+) [^>]+>([^<]+)<'
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
        QualityStr = scrapertools.decodeHtmlentities(match.group(1))

    # Estrae i contenuti - Streaming
    load_links(itemlist, '<strong>Streamin?g:</strong>(.*?)cbtable', "orange", "Streaming", "SD")

    # Estrae i contenuti - Streaming HD
    load_links(itemlist, '<strong>Streamin?g HD[^<]+</strong>(.*?)cbtable', "yellow", "Streaming HD", "HD")

    # Estrae i contenuti - Streaming 3D
    load_links(itemlist, '<strong>Streamin?g 3D[^<]+</strong>(.*?)cbtable', "pink", "Streaming 3D")
    
    itemlist=support.server(item, itemlist=itemlist)
    if itemlist and QualityStr:
        itemlist.insert(0,
            Item(channel=item.channel,
                 action="",
                 title="[COLOR orange]%s[/COLOR]" % QualityStr,
                 folder=False))
    
    return itemlist

    # Estrae i contenuti - Download
    # load_links(itemlist, '<strong>Download:</strong>(.*?)<tableclass=cbtable height=30>', "aqua", "Download")

    # Estrae i contenuti - Download HD
    # load_links(itemlist, '<strong>Download HD[^<]+</strong>(.*?)<tableclass=cbtable width=100% height=20>', "azure", "Download HD")


def findvid_serie(item):
    def load_vid_series(html, item, itemlist, blktxt):
        logger.info('HTML' + html)
        patron = r'<a href="([^"]+)"[^=]+="_blank"[^>]+>(?!<!--)(.*?)</a>'
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
                data = scrapertools.find_single_match(data, 'window.location.href = "([^"]+)";')
            except IndexError:
                data = httptools.downloadpage(item.url, only_headers=True, follow_redirects=False).headers.get("location", "")
            data, c = unshortenit.unwrap_30x_only(data)
        else:
            data = scrapertools.find_single_match(data, r'<a href="([^"]+)".*?class="btn-wrapper">.*?licca.*?</a>')
        
        logger.debug("##### play go.php data ##\n%s\n##" % data)
    else:
        data = support.swzz_get_url(item)

    return servertools.find_video_items(data=data)

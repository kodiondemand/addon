# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per documentaristreamingda
# ------------------------------------------------------------
import re
import urlparse

from core import httptools, scrapertools, servertools
from core.item import Item
from platformcode import logger, config

host = "https://documentari-streaming-da.com"


def mainlist(item):
    logger.info("kod.documentaristreamingda mainlist")
    itemlist = [Item(channel=item.channel,
                     title="[COLOR azure]Aggiornamenti[/COLOR]",
                     action="peliculas",
                     url=host + "/?searchtype=movie&post_type=movie&sl=lasts&s=",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR azure]Categorie[/COLOR]",
                     action="categorias",
                     url=host + "/documentari-streaming-dataarchive/",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR yellow]Cerca...[/COLOR]",
                     action="search",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

    return itemlist


def newest(categoria):
    logger.info("kod.documentaristreamingda newest" + categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "documentales":
            item.url = host + "/?searchtype=movie&post_type=movie&sl=lasts&s="
            item.action = "peliculas"
            itemlist = peliculas(item)

            if itemlist[-1].action == "peliculas":
                itemlist.pop()

    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def categorias(item):
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, 'Categorie</a></li>(.*?)</ul>')

    # Estrae i contenuti 
    patron = '<a href="([^"]+)">([^<]+)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(bloque)

    for scrapedurl, scrapedtitle in matches:

        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle.replace("Documentari ", ""))

        html = httptools.downloadpage(scrapedurl).data

        patron = '>Ultime uscite[^<]+<\/h3><a href="([^"]+)"'
        matches = re.compile(patron, re.DOTALL).findall(html)
        for url in matches:
            url = url.replace("&#038;", "&")
            itemlist.append(
                Item(channel=item.channel,
                     action="peliculas",
                     title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                     url=url,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png",
                     folder=True))

    return itemlist


def search(item, texto):
    logger.info("kod.documentaristreamingda " + item.url + " search " + texto)
    item.url = host + "/?searchtype=movie&post_type=movie&s=" + texto
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def peliculas(item):
    logger.info("kod.documentaristreamingda peliculas")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data

    # Estrae i contenuti 
    patron = '<div class="movie-poster">\s*<img[^s]+src="([^"]+)"[^=]+=[^=]+="([^"]+)"[^>]+>[^<]+<a[^h]+href="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedtitle, scrapedurl in matches:
        # html = httptools.downloadpage(scrapedurl)
        # start = html.find("</div><h2>")
        # end = html.find("<p><strong>", start)
        # scrapedplot = html[start:end]
        # scrapedplot = re.sub(r'<[^>]*>', '', scrapedplot)
        # scrapedplot = scrapertools.decodeHtmlentities(scrapedplot)
        scrapedplot = ""
        scrapedtitle = scrapedtitle.replace("streaming", "")
        scrapedtitle = scrapedtitle.replace("_", " ")
        scrapedtitle = scrapedtitle.replace("-", " ")
        scrapedtitle = scrapedtitle.title()
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 viewmode="movie_with_plot",
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 folder=True))

    # Paginazione 
    patronvideos = '<a class="next page-numbers" href="(.*?)">'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)

    if len(matches) > 0:
        scrapedurl = urlparse.urljoin(item.url, matches[0])
        scrapedurl = scrapedurl.replace("&#038;", "&")
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))

    return itemlist


def findvideos(item):
    logger.info("kod.documentaristreamingda findvideos")

    data = httptools.downloadpage(item.url).data

    links = []
    begin = data.find('<div class="moview-details-text">')
    if begin != -1:
        end = data.find('<!-- //movie-details -->', begin)
        mdiv = data[begin:end]

        items = [[m.end(), m.group(1)] for m in re.finditer('<b style="color:#333333;">(.*?)<\/b>', mdiv)]
        if items:
            for idx, val in enumerate(items):
                if idx == len(items) - 1:
                    _data = mdiv[val[0]:-1]
                else:
                    _data = mdiv[val[0]:items[idx + 1][0]]

                for link in re.findall('<a.*?href="([^"]+)"[^>]+>.*?<b>(.*?)<\/b><\/a>+', _data):
                    if not link[0].strip() in [l[1] for l in links]: links.append(
                        [val[1], link[0].strip(), link[1].strip()])

        items = [[m.end(), m.group(1)] for m in re.finditer('<p><strong>(.*?)<\/strong><\/p>', mdiv)]
        if items:
            _title = ''
            for idx, val in enumerate(items):
                if idx == len(items) - 1:
                    _data = mdiv[val[0]:-1]
                else:
                    _data = mdiv[val[0]:items[idx + 1][0]]

                for link in re.findall('<a\s.*?href="([^"]+)".*?>(?:<span[^>]+>)*(?:<strong>)*([^<]+)', _data):
                    if not link[0].strip() in [l[1] for l in links]:
                        if not link[1].strip() in link[0]: _title = link[1].strip()
                        links.append([_title, link[0].strip(), 'unknown'])

        items = [[m.start(), m.group(1)] for m in re.finditer('<li><strong>([^<]+)<', mdiv)]
        if items:
            for idx, val in enumerate(items):
                if idx == len(items) - 1:
                    _data = mdiv[val[0]:-1]
                else:
                    _data = mdiv[val[0]:items[idx + 1][0]]

                for link in re.findall('<a\s.*?href="([^"]+)".*?>(?:<span[^>]+>)*(?:<strong>)*([^<]+)', _data):
                    if not link[0].strip() in [l[1] for l in links]: links.append(
                        [val[1], link[0].strip(), link[1].strip()])

    itemlist = []
    if links:
        for l in links:
            title = unicode(l[0], 'utf8', 'ignore')
            title = title.replace(u'\xa0', ' ').replace('Documentario ', '').replace(' doc ', ' ').replace(' streaming',
                                                                                                           '').replace(
                ' Streaming', '')
            url = l[1]
            action = "play"
            server = "unknown"
            folder = False

            if url == '#' or not title: continue

            logger.info('server: %s' % l[2])
            if l[2] != 'unknown':
                server = unicode(l[2], 'utf8', 'ignore')
            else:
                logger.info(url)
                match = re.search('https?:\/\/(?:www\.)*([^\.]+)\.', url)
                if match:
                    server = match.group(1)

                    if server == "documentari-streaming-db":
                        action = "findvideos"
                        folder = True
            logger.info('server: %s, action: %s' % (server, action))

            logger.info(title + ' - [COLOR blue]' + server + '[/COLOR]')

            itemlist.append(Item(
                channel=item.channel,
                title=title + ' - [COLOR blue]' + server + '[/COLOR]',
                action=action,
                server=server,  # servertools.get_server_from_url(url),
                url=url,
                thumbnail=item.thumbnail,
                fulltitle=title,
                show=item.show,
                plot=item.plot,
                parentContent=item,
                folder=folder)
            )
    else:
        itemlist = servertools.find_video_items(data=data)

        for videoitem in itemlist:
            videoitem.title = "".join([item.title, '[COLOR green][B]' + videoitem.title + '[/B][/COLOR]'])
            videoitem.fulltitle = item.fulltitle
            videoitem.show = item.show
            videoitem.thumbnail = item.thumbnail
            videoitem.channel = item.channel

    return itemlist


# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per cinemastreaming
# ------------------------------------------------------------
import re

from specials import filtertools, autoplay
from core import scrapertools, servertools, httptools, scrapertoolsV2, support
from core.item import Item

host = 'https://cinemastreaming.icu'

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['openload', 'streamango']
list_quality = ['1080p', '1080p 3D', 'SD', 'CAM', 'default']

headers = [['Referer', host]]


def mainlist(item):
    support.log()

    # Menu Principale
    itemlist = []
    support.menu(itemlist, 'Film bold', 'peliculas', host + '/film/')
    support.menu(itemlist, 'Per genere submenu', 'menu', host, args="Film per Genere")
    support.menu(itemlist, 'Anime bold', 'peliculas', host + '/category/anime/')
    support.menu(itemlist, 'Serie TV bold', 'peliculas', host + '/serie-tv/', contentType='episode')
    support.menu(itemlist, 'Ultime Uscite submenu', 'peliculas', host + "/stagioni/", "episode", args='latests')
    support.menu(itemlist, 'Ultimi Episodi submenu', 'peliculas_latest_ep', host + "/episodi/", "episode", args='lateste')
    support.menu(itemlist, '[COLOR blue]Cerca...[/COLOR]', 'search')

    autoplay.init(item.channel, list_servers, list_quality)
    autoplay.show_option(item.channel, itemlist)

    return itemlist


def peliculas(item):
    support.log()
    list_groups = ["url", "thumb", "title", "year", "rating", "duration"]

    patron = r'<article.*?"TPost C".*?href="([^"]+)".*?img.*?src="([^"]+)".*?<h3.*?>([^<]+).*?Year">'

    if item.args == "latests":
        patron += r'([^<]+)'
    else:
        patron += r'(\d{4}).*?AAIco-star.*?>([^<]+).*?AAIco-access_time">([^<]+).*?Qlty'

    patron_next = r'page-numbers current.*?href="([^"]+)"'

    if item.contentType == "movie":
        patron += r'\">([^<]+)'
        list_groups.append("quality")

    action = "findvideos" if item.contentType == "movie" else "episodios"

    return support.scrape(item, patron, list_groups, patronNext=patron_next, action=action)


def peliculas_latest_ep(item):

    patron = r'<article.*?"TPost C".*?href="([^"]+)".*?img.*?src="([^"]+)"'
    patron += r'.*?class="ClB">([^<]+)<\/span>([^<]+).*?<h3.*?>([^<]+)'

    data = httptools.downloadpage(item.url).data

    matches = re.compile(patron, re.DOTALL).findall(data)
    itemlist = []
    for scrapedurl, scrapedthumbnail, scrapednum, scrapedep, scrapedtitle in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentType=item.contentType,
                 title="[B]" + scrapednum + "[/B]" + scrapedep + " - " + scrapedtitle,
                 fulltitle=scrapedep + " " + scrapedtitle,
                 show=scrapedep + " " + scrapedtitle,
                 url=scrapedurl,
                 extra=item.extra,
                 thumbnail="http:" + scrapedthumbnail,
                 infoLabels=item.infoLabels
                 ))

    support.nextPage(itemlist, item, data, r'page-numbers current.*?href="([^"]+)"')

    return itemlist


def peliculas_menu(item):
    itemlist = peliculas(item)
    return itemlist[:-1]


def episodios(item):
    patron = r'<td class="MvTbTtl"><a href="([^"]+)">(.*?)<\/a>.*?>\d{4}<'
    list_groups = ["url", "title", "year"]

    itemlist = support.scrape(item, patron, list_groups)

    for itm in itemlist:
        fixedtitle = scrapertools.get_season_and_episode(itm.url)
        itm.title = fixedtitle + " - " + itm.title
        itm.fulltitle = fixedtitle + " - " + itm.fulltitle

    return itemlist


def menu(item):
    patron_block = r'<ul class="sub-menu">.*?</ul>'
    patron = r'menu-category-list"><a href="([^"]+)">([^<]+)<'
    list_groups = ["url", "title"]

    return support.scrape(item, patron, list_groups, blacklist="Anime", action="peliculas_menu", patron_block=patron_block)


def search(item, texto):
    support.log("s=", texto)
    item.url = host + "/?s=" + texto
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except Exception, e:
        import traceback
        traceback.print_stack()
        support.log(str(e))
        return []


def newest(categoria):
    support.log("newest" + categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "series":
            item.url = host + "/episodi/"
            item.action = "peliculas"
            item.args = "lateste"
            item.contentType = "episode"
            itemlist = peliculas(item)

            if itemlist[-1].action == "peliculas":
                itemlist.pop()

    # Continua la ricerca in caso di errore
    except Exception, e:
        import traceback
        traceback.print_stack()
        support.log(str(e))
        return []

    return itemlist


def findvideos(item):

    if item.quality.lower() in ["ended", "canceled", "returning series"]:
        return episodios(item)

    itemlist = []
    data = scrapertoolsV2.decodeHtmlentities(httptools.downloadpage(item.url).data)
    btns = re.compile(r'data-tplayernv="Opt.*?><span>([^<]+)</span><span>([^<]+)</span>', re.DOTALL).findall(data)
    matches = re.compile(r'<iframe.*?src="([^"]+trembed=[^"]+)', re.DOTALL).findall(data)
    for i, scrapedurl in enumerate(matches):

        scrapedurl = scrapertoolsV2.decodeHtmlentities(scrapedurl)
        patron = r'<iframe.*?src="([^"]+)"'
        link_data = httptools.downloadpage(scrapedurl).data
        url = scrapertoolsV2.find_single_match(link_data, patron)

        itemlist.append(
            Item(channel=item.channel,
                 action="play",
                 contentType=item.contentType,
                 title="[B]" + btns[i][0] + "[/B] - " + btns[i][1],
                 fulltitle=btns[i][0] + " " + btns[i][1],
                 show=btns[i][0] + " " + btns[i][1],
                 url=url,
                 extra=item.extra,
                 infoLabels=item.infoLabels,
                 server=btns[i][0],
                 contentQuality=btns[i][1].replace('Italiano - ', ''),
                 ))

    if item.contentType == "movie":
        support.videolibrary(itemlist, item)
    autoplay.start(itemlist, item)

    return itemlist


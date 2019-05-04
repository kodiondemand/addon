# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per italiaserie
# ------------------------------------------------------------
import re

import autoplay
import filtertools
import support
from core import httptools, scrapertools
from core import tmdb
from core.item import Item
from platformcode import logger

host = "https://italiaserie.org"

list_servers = ['speedvideo']

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()


def mainlist(item):
    support.log()
    itemlist = []

    support.menu(itemlist, 'Ultime Uscite', 'peliculas', host + "/category/serie-tv/", "episode")
    support.menu(itemlist, 'Ultimi Episodi', 'peliculas', host + "/ultimi-episodi/", "episode", 'latest')
    support.menu(itemlist, 'Categorie', 'menu', host, "episode", args="Serie-Tv per Genere")
    support.menu(itemlist, 'Cerca...', 'search', host, 'episode', args='serie')

    autoplay.init(item.channel, list_servers, [])
    autoplay.show_option(item.channel, itemlist)

    return itemlist


def newest(categoria):
    logger.info("[italiaserie.py]==> newest" + categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "series":
            item.url = host + "/ultimi-episodi/"
            item.action = "peliculas"
            item.args = "latest"
            item.contentType = "episode"
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


def peliculas(item):
    support.log()
    patron = r'<div class="post-thumb">\s*<a href="([^"]+)" title="([^"]+)">\s*<img src="([^"]+)"[^>]+>'
    list_groups = ["url", "title", "thumb"]

    if item.args == "latest":
        patron += r'.*?aj-eps">(.*?)</span>'
        data = httptools.downloadpage(item.url).data

        matches = re.compile(patron, re.S).findall(data)
        itemlist = []

        for scrapedurl, scrapedtitle, scrapedthumbnail, scrapedep in matches:
            s, ep = scrapertools.find_single_match(scrapedep, r'(\d+)x(\d+)\s')
            itemlist.append(
                Item(channel=item.channel,
                     action="episodios",
                     contentType=item.contentType,
                     title="[B]" + scrapedtitle + "[/B] " + scrapedep,
                     fulltitle=scrapedtitle,
                     show=scrapedtitle,
                     url=scrapedurl,
                     extra=item.extra,
                     args={"season": s, "episode": ep}
                     ))

        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
        return itemlist
    else:
        patron_next = r'<a class="next page-numbers" href="(.*?)">'
        itemlist = support.scrape(item, patron, list_groups, patronNext=patron_next, action="episodios")

        if itemlist[-1].action != "peliculas":
            itemlist.pop()

        return itemlist


def search(item, texto):
    support.log("s=", texto)
    item.url = host + "/?s=" + texto
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def menu(item):
    support.log()
    patron = r'<li class="cat-item.*?href="([^"]+)".*?>(.*?)</a>'
    return support.scrape(item, patron, ["url", "title"], action="peliculas")


def episodios(item):
    support.log()

    patron = r'<div class="su-spoiler.*?</i>(.*?)</div>\s+<div class="su-spoiler-content"(.*?)="clearfix">'
    data = httptools.downloadpage(item.url).data
    matches = re.compile(patron, re.S).findall(data)

    if item.args:
        s = (int(item.args["season"]))
        try:
            matches = [matches[s]]
        except:
            matches = [matches[(s - 1)]]

    itemlist = []

    for season, block in matches:
        patron = r'<div class="su-link-ep">\s+<a.*?href="([^"]+)".*?strong>(.*?)</'
        if item.args:
            ep = int(item.args["episode"])
            patron = r'<div class="su-link-ep">\s+<a.*?href="([^"]+)".*?strong>\s(Episodio ' + str(ep) + r') .*?</'
        episodes = re.compile(patron, re.MULTILINE).findall(block)
        for scrapedurl, scrapedtitle in episodes:
            fixedtitle = scrapertools.get_season_and_episode(season + " " + scrapedtitle)
            eptitle = re.sub(r"Episodio\s+\d+", "", scrapedtitle).strip()
            itemlist.append(
                Item(channel=item.channel,
                     action="findvideos",
                     contentType=item.contentType,
                     title="[B]" + fixedtitle + " " + eptitle + "[/B]",
                     fulltitle=fixedtitle + " " + eptitle,
                     show=fixedtitle + " " + eptitle,
                     url=scrapedurl,
                     extra=item.extra,
                     ))

    if not item.args:
        support.videolibrary(itemlist, item)

    return itemlist


def findvideos(item):
    support.log()

    itemlist = support.server(item, data=item.url)
    # itemlist = filtertools.get_links(itemlist, item, list_language)

    autoplay.start(itemlist, item)

    return itemlist

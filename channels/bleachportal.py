# -*- coding: utf-8 -*-
# Ringraziamo Icarus crew
# ------------------------------------------------------------
# XBMC Plugin
# Canale per http://bleachportal.it
# ------------------------------------------------------------

import re

from core import scrapertools, httptools
from core.item import Item
from platformcode import logger

host = "http://www.bleachportal.it"


def mainlist(item):
    logger.info("[BleachPortal.py]==> mainlist")
    itemlist = [Item(channel=item.channel,
                     action="episodi",
                     title="[COLOR azure] Bleach [/COLOR] - [COLOR deepskyblue]Lista Episodi[/COLOR]",
                     url=host + "/streaming/bleach/stream_bleach.htm",
                     thumbnail="http://i45.tinypic.com/286xp3m.jpg",
                     fanart="http://i40.tinypic.com/5jsinb.jpg",
                     extra="bleach"),
                Item(channel=item.channel,
                     action="episodi",
                     title="[COLOR azure] D.Gray Man [/COLOR] - [COLOR deepskyblue]Lista Episodi[/COLOR]",
                     url=host + "/streaming/d.gray-man/stream_dgray-man.htm",
                     thumbnail="http://i59.tinypic.com/9is3tf.jpg",
                     fanart="http://wallpapercraft.net/wp-content/uploads/2016/11/Cool-D-Gray-Man-Background.jpg",
                     extra="dgrayman")]

    return itemlist


def episodi(item):
    logger.info("[BleachPortal.py]==> episodi")
    itemlist = []

    data = httptools.downloadpage(item.url).data
    patron = '<td>?[<span\s|<width="\d+%"\s]+?class="[^"]+">\D+([\d\-]+)\s?<[^<]+<[^<]+<[^<]+<[^<]+<.*?\s+?.*?<span style="[^"]+">([^<]+).*?\s?.*?<a href="\.*(/?[^"]+)">'
    matches = re.compile(patron, re.DOTALL).findall(data)

    animetitle = "Bleach" if item.extra == "bleach" else "D.Gray Man"
    for scrapednumber, scrapedtitle, scrapedurl in matches:
        scrapedtitle = scrapedtitle.decode('latin1').encode('utf8')
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 title="[COLOR azure]%s Ep: [COLOR deepskyblue]%s[/COLOR][/COLOR]" % (animetitle, scrapednumber),
                 url=item.url.replace("stream_bleach.htm",scrapedurl) if "stream_bleach.htm" in item.url else item.url.replace("stream_dgray-man.htm", scrapedurl),
                 plot=scrapedtitle,
                 extra=item.extra,
                 thumbnail=item.thumbnail,
                 fanart=item.fanart,
                 fulltitle="[COLOR red]%s Ep: %s[/COLOR] | [COLOR deepskyblue]%s[/COLOR]" % (animetitle, scrapednumber, scrapedtitle)))

    if item.extra == "bleach":
        itemlist.append(
            Item(channel=item.channel,
                 action="oav",
                 title="[B][COLOR azure] OAV e Movies [/COLOR][/B]",
                 url=item.url.replace("stream_bleach.htm", "stream_bleach_movie_oav.htm"),
                 extra=item.extra,
                 thumbnail=item.thumbnail,
                 fanart=item.fanart))

    return list(reversed(itemlist))


def oav(item):
    logger.info("[BleachPortal.py]==> oav")
    itemlist = []

    data = httptools.downloadpage(item.url).data
    patron = '<td>?[<span\s|<width="\d+%"\s]+?class="[^"]+">-\s+(.*?)<[^<]+<[^<]+<[^<]+<[^<]+<.*?\s+?.*?<span style="[^"]+">([^<]+).*?\s?.*?<a href="\.*(/?[^"]+)">'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapednumber, scrapedtitle, scrapedurl in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 title="[COLOR deepskyblue] " + scrapednumber + " [/COLOR]",
                 url=item.url.replace("stream_bleach_movie_oav.htm", scrapedurl),
                 plot=scrapedtitle,
                 extra=item.extra,
                 thumbnail=item.thumbnail,
                 fulltitle="[COLOR red]" + scrapednumber + "[/COLOR] | [COLOR deepskyblue]" + scrapedtitle + "[/COLOR]"))

    return list(reversed(itemlist))


def findvideos(item):
    logger.info("[BleachPortal.py]==> findvideos")
    itemlist = []

    if "bleach//" in item.url:
        item.url = re.sub(r'\w+//', "", item.url)

    data = httptools.downloadpage(item.url).data

    if "bleach" in item.extra:
        video = scrapertools.find_single_match(data, 'file: "(.*?)",')
    else:
        video = scrapertools.find_single_match(data, 'file=(.*?)&').rsplit('/', 1)[-1]

    itemlist.append(
        Item(channel=item.channel,
             action="play",
             title="[[COLOR orange]Diretto[/COLOR]] [B]%s[/B]" % item.title,
             url=item.url.replace(item.url.split("/")[-1], "/" + video),
             thumbnail=item.thumbnail,
             fulltitle=item.fulltitle))
    return itemlist

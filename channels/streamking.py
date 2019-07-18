# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Stream King **** TEST ****
# Alhaziel
# ------------------------------------------------------------

import re
import urllib

from core import scrapertools, httptools
from core.item import Item
from platformcode import logger
from platformcode import config

__channel__ = "streamking"
host = config.get_channel_url(__channel__)

headers = [['Referer', host]]

def mainlist(item):
    logger.info("[streamking] canali")
    itemlist = []

    data = httptools.downloadpage(host, headers=headers).data.replace('\n','')
    patron = '<div class="tv-block">.*?<a href="([^"]+)".*?src="([^"]+)".*?title="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        url = host + scrapedurl
        thumb = host + scrapedthumbnail
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentTitle=scrapedtitle,
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=url,
                 thumbnail=thumb))

    return itemlist

def findvideos(item):
    logger.info("[streamking] findvideos")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data.replace('\n','')
    iframe = scrapertools.find_single_match(data, '<iframe src="([^"]+)"')
    data = httptools.downloadpage(iframe, headers=headers).data
    m3u8 = scrapertools.find_single_match(data, "file: '([^']+)'")
  
    itemlist.append(
        Item(channel=item.channel,
        action="play",
        title=item.title + 'Play',
        url=m3u8 + '|' + urllib.urlencode(dict(headers))
        ))
    return itemlist
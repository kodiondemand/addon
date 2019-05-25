# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import logger

host = 'http://www.18hentaionline.net/'
headers = [['User-Agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'],
           ['Referer', host]]


def mainlist(item):
    logger.info()

    itemlist = []

    itemlist.append(Item(channel=item.channel, title="Todos", action="todas", url=host, thumbnail='', fanart=''))

    itemlist.append(
        Item(channel=item.channel, title="Sin Censura", action="todas", url=host + 'tag/sin-censura/', thumbnail='',
             fanart=''))

    itemlist.append(
        Item(channel=item.channel, title="Estrenos", action="todas", url=host + 'category/estreno/', thumbnail='',
             fanart=''))

    itemlist.append(
        Item(channel=item.channel, title="Categorias", action="categorias", url=host, thumbnail='', fanart=''))

    return itemlist


def todas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, headers=headers).data
    patron = '<h3><a href="([^"]+)" title="([^"]+)">.*?<\/a><\/h3>.*?'
    patron += '<.*?>.*?'
    patron += '<a.*?img src="([^"]+)" alt'

    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        url = scrapedurl
        title = scrapedtitle.decode('utf-8')
        thumbnail = scrapedthumbnail
        fanart = ''
        itemlist.append(
            Item(channel=item.channel, action="episodios", title=title, url=url, thumbnail=thumbnail, fanart=fanart))

    # Paginacion
    title = ''
    siguiente = scrapertools.find_single_match(data,
                                               '<a rel="nofollow" class="next page-numbers" href="([^"]+)">Siguiente &raquo;<\/a><\/div>')
    title = 'Pagina Siguiente >>> '
    fanart = ''
    itemlist.append(Item(channel=item.channel, action="todas", title=title, url=siguiente, fanart=fanart))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto

    if texto != '':
        return todas(item)
    else:
        return []


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, headers=headers).data
    patron = "<a href='([^']+)' class='tag-link-.*? tag-link-position-.*?' title='.*?' style='font-size: 11px;'>([^<]+)<\/a>"

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        url = scrapedurl
        title = scrapedtitle
        itemlist.append(Item(channel=item.channel, action="todas", title=title, fulltitle=item.fulltitle, url=url))

    return itemlist


def episodios(item):
    censura = {'Si': 'con censura', 'No': 'sin censura'}
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, headers=headers).data
    old_mode = scrapertools.find_single_match(data, '<th>Censura<\/th>')
    if old_mode:
        patron = '<td>(\d+)<\/td><td>(.*?)<\/td><td>(.*?)<\/td><td>(.*?)<\/td><td><a href="(.*?)".*?>Ver Capitulo<\/a><\/td>'

        matches = re.compile(patron, re.DOTALL).findall(data)

        for scrapedcap, scrapedaud, scrapedsub, scrapedcen, scrapedurl in matches:
            url = scrapedurl
            title = 'CAPITULO ' + scrapedcap + ' AUDIO: ' + scrapedaud + ' SUB:' + scrapedsub + ' ' + censura[scrapedcen]
            thumbnail = ''
            plot = ''
            fanart = ''
            itemlist.append(Item(channel=item.channel, action="findvideos", title=title, fulltitle=item.fulltitle, url=url,
                                 thumbnail=item.thumbnail, plot=plot))
    else:
        patron = '<\/i>.*?(.\d+)<\/td><td style="text-align:center">MP4<\/td><td style="text-align:center">(.*?)<\/td>.*?'
        patron +='<a class="dr-button" href="(.*?)" >'

        matches = re.compile(patron, re.DOTALL).findall(data)

        for scrapedcap, scrapedsub, scrapedurl in matches:
            url = scrapedurl
            if scrapedsub !='':
                subs= scrapedsub
            else:
                sub = 'No'
            title = 'CAPITULO %s SUB %s'%(scrapedcap, subs)
            thumbnail = ''
            plot = ''
            fanart = ''
            itemlist.append(Item(channel=item.channel, action="findvideos", title=title, fulltitle=item.fulltitle, url=url,
                                 thumbnail=item.thumbnail, plot=plot))

    return itemlist

def findvideos(item):
    logger.info()

    itemlist = []
    data = httptools.downloadpage(item.url).data
    gvideo = scrapertools.find_single_match(data,'<li rel="(http:\/\/www\.18hentaionline\.net\/ramus\/phar\.php\?vid=.*?)">')
    headers = {'Host':'www.18hentaionline.net', 'Referer':item.url}
    gvideo_data = httptools.downloadpage(gvideo, headers = headers).data
    gvideo_url = scrapertools.find_single_match(gvideo_data, 'file: "(.*?)"')
    server = 'directo'
    new_item = (item.clone(url=gvideo_url, server=server))
    itemlist.append(new_item)
    itemlist.extend(servertools.find_video_items(data=data))
    for videoitem in itemlist:
        videoitem.channel = item.channel
        videoitem.title = item.title+' (%s)'%videoitem.server
        videoitem.action = 'play'
    return itemlist



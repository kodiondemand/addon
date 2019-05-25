# -*- coding: utf-8 -*-

import re

import urlparse

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import logger

host = 'http://sexkino.to'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="New" , action="lista", url= host + "/movies/"))
    itemlist.append( Item(channel=item.channel, title="Año" , action="anual", url= host))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url= host))

    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info("pelisalacarta.gmobi mainlist")
    texto = texto.replace(" ", "+")
    item.url = host + "/?s=%s" % texto
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<li class="cat-item cat-item-.*?<a href="(.*?)" >(.*?)</a> <i>(.*?)</i>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedtitle,cantidad  in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = scrapedtitle + " ("+cantidad+")"
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist

def anual(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<li><a href="([^<]+)">([^<]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<div class="poster">.*?'
    patron += '<img src="([^"]+)" alt="([^"]+)">.*?'
    patron += '<span class="quality">([^"]+)</span>.*?'
    patron += '<a href="([^"]+)">'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedthumbnail,scrapedtitle,calidad,scrapedurl in matches:
        scrapedplot = ""
        scrapedtitle = scrapedtitle + " (" + calidad + ")"
        itemlist.append( Item(channel=item.channel, action="findvideos", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail, fanart=scrapedthumbnail, plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data,'resppages.*?<a href="([^"]+)" ><span class="icon-chevron-right">')
    if next_page != "":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="Next page >>", text_color="blue", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    
    # <th>Watch online</th><th>Quality</th><th>Language</th><th>Added</th></tr></thead>
    # <tbody>
    # <tr id='link-3848'><td><img src='https://s2.googleusercontent.com/s2/favicons?domain=vidzella.me'> <a href='http://sexkino.to/links/69321-5/' target='_blank'>Watch online</a></td>
    # <td><strong class='quality'>DVDRip</strong></td><td>German</td><td>2 years</td></tr>
    # <tr id='link-3847'><td><img src='https://s2.googleusercontent.com/s2/favicons?domain=flashx.tv'> <a href='http://sexkino.to/links/69321-4/' target='_blank'>Watch online</a></td>
    # <td><strong class='quality'>DVDRip</strong></td><td>German</td><td>2 years</td></tr>
    # <tr id='link-3844'><td><img src='https://s2.googleusercontent.com/s2/favicons?domain=openload.co'> <a href='http://sexkino.to/links/69321-3/' target='_blank'>Watch online</a></td>
    # <td><strong class='quality'>DVDRip</strong></td><td>German</td><td>2 years</td></tr>
    # <tr id='link-3843'><td><img src='https://s2.googleusercontent.com/s2/favicons?domain=vidoza.net'> <a href='http://sexkino.to/links/69321-2/' target='_blank'>Watch online</a></td>
    # <td><strong class='quality'>DVDRip</strong></td><td>German</td><td>2 years</td></tr>
    # <tr id='link-3842'><td><img src='https://s2.googleusercontent.com/s2/favicons?domain=rapidvideo.ws'> <a href='http://sexkino.to/links/69321/' target='_blank'>Watch online</a></td>
    # <td><strong class='quality'>DVDRip</strong></td><td>German</td><td>2 years</td></tr>
    # </tbody></table></div></div></div></div>

    
    
    patron  = '<tr id=(.*?)</tr>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for match in matches:
        url = scrapertools.find_single_match(match,'href="([^"]+)" target')
        title = scrapertools.find_single_match(match,'<td><img src=.*?> (.*?)</td>')
        itemlist.append(item.clone(action="play", title=title, url=url))
     
     # <a id="link" href="https://vidzella.me/play#GS7D" class="btn" style="background-color:#1e73be">Continue</a>
     
    patron  = '<iframe class="metaframe rptss" src="([^"]+)".*?<li><a class="options" href="#option-\d+">\s+(.*?)\s+<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        url = scrapedurl
        title = scrapedtitle
        itemlist.append(item.clone(action="play", title=title, url=url))
    return itemlist


def play(item):
    logger.info()
    data = httptools.downloadpage(item.url).data
    itemlist = servertools.find_video_items(data=data)
    for videoitem in itemlist:
        videoitem.title = item.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
    return itemlist


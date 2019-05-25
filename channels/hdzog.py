# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re
import urllib
import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger

host = 'http://www.hdzog.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevos" , action="lista", url=host + "/new/"))
    itemlist.append( Item(channel=item.channel, title="Popular" , action="lista", url=host + "/popular/"))
    itemlist.append( Item(channel=item.channel, title="Longitud" , action="lista", url=host + "/longest/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist

def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/?q=%s" % texto
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
    data = scrapertools.find_single_match(data,'<ul class="cf">(.*?)</ul>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<li>.*?<a href="([^"]+)".*?'
    patron += '<img class="thumb" src="([^"]+)" alt="([^"]+)".*?'
    patron += '<span class="videos-count">(\d+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,vidnum in matches:
        scrapedplot = ""
        
        url= scrapedurl + "?sortby=post_date"
        title = scrapedtitle + " \(" + vidnum + "\)"
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=url,
                              thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data,'<ul class="cf">(.*?)<h2>Advertisement</h2>')
    patron  = '<li>.*?<a href="([^"]+)".*?'
    patron += 'src="([^"]+)" alt="([^"]+)".*?'
    patron += '<span class="time">(.*?)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,time  in matches:
        contentTitle = scrapedtitle
        title = "[COLOR yellow]" + time + "[/COLOR] " + scrapedtitle
        thumbnail = scrapedthumbnail
        plot = ""
        itemlist.append( Item(channel=item.channel, action="play", title=title, url=scrapedurl,
                               thumbnail=thumbnail, plot=plot, contentTitle = contentTitle))
    next_page = scrapertools.find_single_match(data,'<a href="([^"]+)" title="Next Page" data-page-num="\d+">Next page &raquo;</a>')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


def play(item):
    logger.info(item)
    itemlist = []
    data = httptools.downloadpage(item.url).data
    video_url = scrapertools.find_single_match(data, 'var video_url="([^"]*)"')
    video_url += scrapertools.find_single_match(data, 'video_url\+="([^"]*)"')
    partes = video_url.split('||')
    video_url = decode_url(partes[0])
    video_url = re.sub('/get_file/\d+/[0-9a-z]{32}/', partes[1], video_url)
    video_url += '&' if '?' in video_url else '?'
    video_url += 'lip=' + partes[2] + '&lt=' + partes[3]
    itemlist.append(item.clone(action="play", title=item.title, url=video_url))
    return itemlist


def decode_url(txt):
    _0x52f6x15 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,~'
    reto = ''; n = 0
    # En las dos siguientes líneas, ABCEM ocupan 2 bytes cada letra! El replace lo deja en 1 byte. !!!!: АВСЕМ (10 bytes) ABCEM (5 bytes)
    txt = re.sub('[^АВСЕМA-Za-z0-9\.\,\~]', '', txt)
    txt = txt.replace('А', 'A').replace('В', 'B').replace('С', 'C').replace('Е', 'E').replace('М', 'M')

    while n < len(txt):
        a = _0x52f6x15.index(txt[n])
        n += 1
        b = _0x52f6x15.index(txt[n])
        n += 1
        c = _0x52f6x15.index(txt[n])
        n += 1
        d = _0x52f6x15.index(txt[n])
        n += 1

        a = a << 2 | b >> 4
        b = (b & 15) << 4 | c >> 2
        e = (c & 3) << 6 | d
        reto += chr(a)
        if c != 64: reto += chr(b)
        if d != 64: reto += chr(e)

    return urllib.unquote(reto)


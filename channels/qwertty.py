# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re
import urllib
import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger

host = 'http://qwertty.net'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Recientes" , action="lista", url=host))
    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="lista", url=host + "/?filter=most-viewed"))
    itemlist.append( Item(channel=item.channel, title="Mas popular" , action="lista", url=host + "/?filter=popular"))
    itemlist.append( Item(channel=item.channel, title="Mejor valoradas" , action="lista", url=host + "/?filter=random"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
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
    patron  = '<li><a href="([^<]+)">(.*?)</a></li>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedurl = host + scrapedurl
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data,'<div class="videos-list">(.*?)<div class="videos-list">')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<article id="post-\d+".*?'
    patron += '<a href="([^"]+)" title="([^"]+)">.*?'
    patron += '<div class="post-thumbnail(.*?)<span class="views">.*?'
    patron += '<span class="duration"><i class="fa fa-clock-o"></i>([^<]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,duracion in matches:
        scrapedplot = ""
        thumbnail = scrapertools.find_single_match(scrapedthumbnail, 'poster="([^"]+)"')
        if thumbnail == "":
            thumbnail = scrapertools.find_single_match(scrapedthumbnail, "data-thumbs='(.*?jpg)")
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        itemlist.append( Item(channel=item.channel, action="play", title=title, url=scrapedurl,
                              fanart=thumbnail, thumbnail=thumbnail, plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data,'<li><a href="([^"]+)">Next</a>')
    if next_page=="":
        next_page = scrapertools.find_single_match(data,'<li><a class="current">.*?<li><a href=\'([^\']+)\' class="inactive">')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(data,'<meta itemprop="embedURL" content="([^"]+)"')
    url = url.replace("pornhub.com/embed/", "pornhub.com/view_video.php?viewkey=")
    data = httptools.downloadpage(url).data
    if "spankwire" in url : 
        data = httptools.downloadpage(item.url).data
        data = scrapertools.find_single_match(data,'Copy Embed Code(.*?)For Desktop')
        patron  = '<div class="shareDownload_container__item__dropdown">.*?<a href="([^"]+)"'
        matches = scrapertools.find_multiple_matches(data, patron)
        for scrapedurl  in matches:
            url = scrapedurl
            if url=="#":
                scrapedurl = scrapertools.find_single_match(data,'playerData.cdnPath480         = \'([^\']+)\'')
            itemlist.append(item.clone(action="play", title=scrapedurl, fulltitle = scrapedurl, url=scrapedurl))

    if "xvideos" in url : 
        scrapedurl  = scrapertools.find_single_match(data,'setVideoHLS\(\'([^\']+)\'')
    if "pornhub" in url : 
        scrapedurl  = scrapertools.find_single_match(data,'"defaultQuality":true,"format":"mp4","quality":"\d+","videoUrl":"(.*?)"')
    if "txx" in url :
        video_url = scrapertools.find_single_match(data, 'var video_url="([^"]*)"')
        video_url += scrapertools.find_single_match(data, 'video_url\+="([^"]*)"')
        partes = video_url.split('||')
        video_url = decode_url(partes[0])
        video_url = re.sub('/get_file/\d+/[0-9a-z]{32}/', partes[1], video_url)
        video_url += '&' if '?' in video_url else '?'
        video_url += 'lip=' + partes[2] + '&lt=' + partes[3]
        scrapedurl = video_url
    else:
        scrapedurl  = scrapertools.find_single_match(data,'"quality":"\d+","videoUrl":"(.*?)"')
    scrapedurl = scrapedurl.replace("\/", "/")
    itemlist.append(Item(channel=item.channel, action="play", title=item.title, fulltitle=item.fulltitle, url=scrapedurl,
                         thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))
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



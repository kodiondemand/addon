# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re
import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger

host = 'http://xxx.justporno.tv'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Ultimos" , action="lista", url=host + "/latest-updates/1/"))
    itemlist.append( Item(channel=item.channel, title="Mejor valoradas" , action="lista", url=host + "/top-rated/"))
    itemlist.append( Item(channel=item.channel, title="Mas Vistas", action="lista", url=host + "/most-popular/"))
    itemlist.append( Item(channel=item.channel, title="Categorias", action="categorias", url=host + "/categories/"))
    itemlist.append( Item(channel=item.channel, title="Buscar" , action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    item.url = "%s/search/%s/" % (host, texto.replace("+", "-"))
    item.extra = texto
    try:
        return lista(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<a class="item" href="([^"]+)" title="([^"]+)">.*?'
    patron += '<div class="videos">(\d+) video.*?</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,numero in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = scrapedtitle + " (" + numero + ")"
        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail , plot=scrapedplot) )

    return sorted(itemlist, key=lambda i: i.title)


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<a href="http://xxx.justporno.tv/videos/(\d+)/.*?" title="([^"]+)" >.*?'
    patron += 'data-original="([^"]+)".*?'
    patron += '<div class="duration">(.*?)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,scrapedtime in matches:
        scrapedplot = ""
        scrapedtitle = "[COLOR yellow]" + (scrapedtime) + "[/COLOR] " + scrapedtitle
        scrapedurl = "http://xxx.justporno.tv/embed/" + scrapedurl
        itemlist.append( Item(channel=item.channel, action="play", title=scrapedtitle, url=scrapedurl,
                              fanart=scrapedthumbnail, thumbnail=scrapedthumbnail, plot=scrapedplot) )
                              
    if item.extra:
        next_page = scrapertools.find_single_match(data, '<li class="next">.*?from_videos\+from_albums:(.*?)>')
        if next_page:
            if "from_videos=" in item.url:
                next_page = re.sub(r'&from_videos=(\d+)', '&from_videos=%s' % next_page, item.url)
            else:
                next_page = "%s?mode=async&function=get_block&block_id=list_videos_videos_list_search_result"\
                            "&q=%s&category_ids=&sort_by=post_date&from_videos=%s" % (item.url, item.extra, next_page)
            itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page))
    else:
        next_page = scrapertools.find_single_match(data,'<li class="next"><a href="([^"]+)"')
        if next_page and not next_page.startswith("#"):
            next_page = urlparse.urljoin(host, next_page)
            itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page))
        else:
            next_page = scrapertools.find_single_match(data, '<li class="next">.*?from:(\d+)')
            if next_page:
                if "from" in item.url:
                    next_page = re.sub(r'&from=(\d+)', '&from=%s' % next_page, item.url)
                else:
                    next_page = "%s?mode=async&function=get_block&block_id=list_videos_common_videos_list" \
                                "&sort_by=post_date&from=%s" % (item.url, next_page)
                itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page))

    # if next_page!="":
        # next_page = urlparse.urljoin(item.url,next_page)
        # itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = 'video_url: \'([^\']+)\''
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl in matches:
        scrapedplot = ""
        itemlist.append(item.clone(channel=item.channel, action="play", title=scrapedurl , url=scrapedurl , plot="" , folder=True) )
    return itemlist


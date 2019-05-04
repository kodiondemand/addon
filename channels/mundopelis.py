# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re, urllib, urlparse

from channels import autoplay
from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, jsontools, tmdb
from core import servertools
from channels import filtertools

host = 'https://mundopelis.xyz'

list_language = []
list_servers = ['Rapidvideo', 'Vidoza', 'Openload', 'Youtube']
list_quality = []
__channel__='mundopelis'
__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', __channel__)
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', __channel__)
try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
except:
    __modo_grafico__ = True


def mainlist(item):
    logger.info()
    itemlist = []
    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist.append(item.clone(title="Novedades" , action="lista", url= host + "/todos-los-estrenos", first=0))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url= host))
    itemlist.append(item.clone(title="Buscar", action="search"))
    
    itemlist.append(item.clone(title="Configurar canal...", text_color="gold", action="configuracion", folder=False))
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def configuracion(item):
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return ret


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/?option=com_spmoviedb&view=searchresults&searchword=%s&type=movies&Itemid=544" % texto
    item.first = 0
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
    patron  = '<a class="btn btn-xs btn-primary" href="/index.php([^"]+)".*?</i> ([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        url = urlparse.urljoin(item.url,scrapedurl)
        title = scrapedtitle 
        itemlist.append(item.clone(channel=item.channel, action="lista", title=title , url=url, first=0,
                              thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    
    next = False
    data = httptools.downloadpage(item.url).data
    patron  = '<div class="movie-poster">.*?'
    patron += '<img src="([^"]+)".*?'
    patron += '<a href="/index.php([^"]+)"><h4 class="movie-title">([^<]+)</h4>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    
    first = item.first
    last = first+20
    if last > len(matches):
        last = len(matches)
        next = True
    scrapertools.printMatches(matches)
    for scrapedthumbnail, scrapedurl, scrapedtitle in matches[first:last]:
        scrapedyear = "-"
        title = scrapedtitle.replace(" (2018)", "")
        url = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append(item.clone(channel=item.channel, action = 'findvideos', title=title, contentTitle = scrapedtitle,
                                   url=url, thumbnail=scrapedthumbnail, infoLabels={'year':scrapedyear} ))
    tmdb.set_infoLabels(itemlist, True)
    # Paginación    
    if not next:
        url_next_page = item.url
        first = last
    else:
        url_next_page = scrapertools.find_single_match(data, '<a title="Siguiente" href="([^"]+)"')
        url_next_page = urlparse.urljoin(item.url,url_next_page)
        first = 0
    if url_next_page:
        itemlist.append(item.clone(title="Siguiente >>", url=url_next_page, action='lista', first=first))    
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<(?:iframe|IFRAME).*?(?:src|SRC)="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url in matches:
        lang = "VOSE"
        if not config.get_setting('unify'):
            title = ' (%s)' % (lang)
        else:
            title = ''
        if url != '':  
            itemlist.append(item.clone(action="play", title='%s'+title, url=url, language=lang ))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())

    # Requerido para Filtrar enlaces
    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)
    # Requerido para FilterTools
    # itemlist = filtertools.get_links(itemlist, item, list_language)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)


    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra !='findvideos' and not "/episodios/" in item.url :
        itemlist.append(Item(channel=item.channel, action="add_pelicula_to_library", 
                             title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]', url=item.url,
                             extra="findvideos", contentTitle=item.contentTitle)) 
    return itemlist



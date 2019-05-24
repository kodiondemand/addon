# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per animetubeita
# ----------------------------------------------------------
import re
import urllib

from core import httptools, scrapertools, tmdb
from core.item import Item
from platformcode import logger, config

host = "http://www.animetubeita.com"
hostlista = host + "/lista-anime/"
hostgeneri = host + "/generi/"
hostcorso = host + "/category/serie-in-corso/"


def mainlist(item):
    log("animetubeita", "mainlist", item.channel)
    itemlist = [Item(channel=item.channel,
                     action="lista_home",
                     title="[COLOR azure]Home[/COLOR]",
                     url=host,
                     thumbnail=AnimeThumbnail,
                     fanart=AnimeFanart),
                # Item(channel=item.channel,
                #      action="lista_anime",
                #      title="[COLOR azure]A-Z[/COLOR]",
                #      url=hostlista,
                #      thumbnail=AnimeThumbnail,
                #      fanart=AnimeFanart),
                Item(channel=item.channel,
                     action="lista_genere",
                     title="[COLOR azure]Genere[/COLOR]",
                     url=hostgeneri,
                     thumbnail=CategoriaThumbnail,
                     fanart=CategoriaFanart),
                Item(channel=item.channel,
                     action="lista_in_corso",
                     title="[COLOR azure]Serie in Corso[/COLOR]",
                     url=hostcorso,
                     thumbnail=CategoriaThumbnail,
                     fanart=CategoriaFanart),
                Item(channel=item.channel,
                     action="search",
                     title="[COLOR lime]Cerca...[/COLOR]",
                     url=host + "/?s=",
                     thumbnail=CercaThumbnail,
                     fanart=CercaFanart)]
    return itemlist



def lista_home(item):
    log("animetubeita", "lista_home", item.channel)

    itemlist = []

    patron = '<h2 class="title"><a href="(.*?)" rel="bookmark" title=".*?">.*?<img.*?src="(.*?)".*?<strong>Titolo</strong></td>.*?<td>(.*?)</td>.*?<td><strong>Trama</strong></td>.*?<td>(.*?)</'
    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedplot in scrapedAll(item.url, patron):
        title = scrapertools.decodeHtmlentities(scrapedtitle)
        title = title.split("Sub")[0]
        fulltitle = re.sub(r'[Ee]pisodio? \d+', '', title)
        scrapedplot = scrapertools.decodeHtmlentities(scrapedplot)
        itemlist.append(
            Item(channel=item.channel,
                 action="dl_s",
                 contentType="tvshow",
                 title="[COLOR azure]" + title + "[/COLOR]",
                 fulltitle=fulltitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 fanart=scrapedthumbnail,
                 show=fulltitle,
                 plot=scrapedplot))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Paginazione
    # ===========================================================
    data = httptools.downloadpage(item.url).data
    patron = '<link rel="next" href="(.*?)"'
    next_page = scrapertools.find_single_match(data, patron)
    if next_page != "":
        itemlist.append(
            Item(channel=item.channel,
                 action="lista_home",
                 title=AvantiTxt,
                 url=next_page,
                 thumbnail=AvantiImg,
                 folder=True))
    # ===========================================================
    return itemlist



# def lista_anime(item):
#     log("animetubeita", "lista_anime", item.channel)

#     itemlist = []

#     patron = '<li.*?class="page_.*?href="(.*?)">(.*?)</a></li>'
#     for scrapedurl, scrapedtitle in scrapedAll(item.url, patron):
#         title = scrapertools.decodeHtmlentities(scrapedtitle)
#         title = title.split("Sub")[0]
#         log("url:[" + scrapedurl + "] scrapedtitle:[" + title + "]")
#         itemlist.append(
#             Item(channel=item.channel,
#                  action="dettaglio",
#                  contentType="tvshow",
#                  title="[COLOR azure]" + title + "[/COLOR]",
#                  url=scrapedurl,
#                  show=title,
#                  thumbnail="",
#                  fanart=""))

#     tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

#     return itemlist



def lista_genere(item):
    log("lista_anime_genere", "lista_genere", item.channel)
    itemlist = []

    data = httptools.downloadpage(item.url).data

    bloque = scrapertools.find_single_match(data,
                                    '<div class="hentry page post-1 odd author-admin clear-block">(.*?)<div id="disqus_thread">')

    patron = '<li class="cat-item cat-item.*?"><a href="(.*?)" >(.*?)</a>'
    matches = re.compile(patron, re.DOTALL).findall(bloque)
    scrapertools.printMatches(matches)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action="lista_generi",
                 title='[COLOR lightsalmon][B]' + scrapedtitle + '[/B][/COLOR]',
                 url=scrapedurl,
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 thumbnail=item.thumbnail))

    return itemlist



def lista_generi(item):
    log("animetubeita", "lista_generi", item.channel)

    itemlist = []
    patron = '<h2 class="title"><a href="(.*?)" rel="bookmark" title=".*?">.*?<img.*?src="(.*?)".*?<strong>Titolo</strong></td>.*?<td>(.*?)</td>.*?<td><strong>Trama</strong></td>.*?<td>(.*?)</'
    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedplot in scrapedAll(item.url, patron):
        title = scrapertools.decodeHtmlentities(scrapedtitle)
        title = title.split("Sub")[0]
        fulltitle = re.sub(r'[Ee]pisodio? \d+', '', title)
        scrapedplot = scrapertools.decodeHtmlentities(scrapedplot)
        itemlist.append(
            Item(channel=item.channel,
                 action="dettaglio",
                 title="[COLOR azure]" + title + "[/COLOR]",
                 contentType="tvshow",
                 fulltitle=fulltitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 show=fulltitle,
                 fanart=scrapedthumbnail,
                 plot=scrapedplot))
                 
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Paginazione
    # ===========================================================
    data = httptools.downloadpage(item.url).data
    patron = '<link rel="next" href="(.*?)"'
    next_page = scrapertools.find_single_match(data, patron)
    if next_page != "":
        itemlist.append(
            Item(channel=item.channel,
                 action="lista_generi",
                 title=AvantiTxt,
                 url=next_page,
                 thumbnail=AvantiImg,
                 folder=True))
    # ===========================================================


    return itemlist



def lista_in_corso(item):
    log("animetubeita", "lista_home", item.channel)

    itemlist = []

    patron = '<h2 class="title"><a href="(.*?)" rel="bookmark" title="Link.*?>(.*?)</a></h2>.*?<img.*?src="(.*?)".*?<td><strong>Trama</strong></td>.*?<td>(.*?)</td>'
    for scrapedurl, scrapedtitle, scrapedthumbnail, scrapedplot in scrapedAll(item.url, patron):
        title = scrapertools.decodeHtmlentities(scrapedtitle)
        title = title.split("Sub")[0]
        fulltitle = re.sub(r'[Ee]pisodio? \d+', '', title)
        scrapedplot = scrapertools.decodeHtmlentities(scrapedplot)
        itemlist.append(
            Item(channel=item.channel,
                 action="dettaglio",
                 title="[COLOR azure]" + title + "[/COLOR]",
                 contentType="tvshow",
                 fulltitle=fulltitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 show=fulltitle,
                 fanart=scrapedthumbnail,
                 plot=scrapedplot))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    
    # Paginazione
    # ===========================================================
    data = httptools.downloadpage(item.url).data
    patron = '<link rel="next" href="(.*?)"'
    next_page = scrapertools.find_single_match(data, patron)
    if next_page != "":
        itemlist.append(
            Item(channel=item.channel,
                 action="lista_in_corso",
                 title=AvantiTxt,
                 url=next_page,
                 thumbnail=AvantiImg,
                 folder=True))
    # ===========================================================
    return itemlist



def dl_s(item):
    log("animetubeita", "dl_s", item.channel)

    itemlist = []
    encontrados = set()

    # 1
    patron = '<p><center><a.*?href="(.*?)"'
    for scrapedurl in scrapedAll(item.url, patron):
        if scrapedurl in encontrados: continue
        encontrados.add(scrapedurl)
        title = "DOWNLOAD & STREAMING"
        itemlist.append(Item(channel=item.channel,
                             action="dettaglio",
                             title="[COLOR azure]" + title + "[/COLOR]",
                             url=scrapedurl,
                             thumbnail=item.thumbnail,
                             fanart=item.thumbnail,
                             plot=item.plot,
                             folder=True))
    # 2
    patron = '<p><center>.*?<a.*?href="(.*?)"'
    for scrapedurl in scrapedAll(item.url, patron):
        if scrapedurl in encontrados: continue
        encontrados.add(scrapedurl)
        title = "DOWNLOAD & STREAMING"
        itemlist.append(Item(channel=item.channel,
                             action="dettaglio",
                             title="[COLOR azure]" + title + "[/COLOR]",
                             url=scrapedurl,
                             thumbnail=item.thumbnail,
                             fanart=item.thumbnail,
                             plot=item.plot,
                             folder=True))

    return itemlist



def dettaglio(item):
    log("animetubeita", "dettaglio", item.channel)

    itemlist = []
    headers = {'Upgrade-Insecure-Requests': '1',
               'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:52.0) Gecko/20100101 Firefox/52.0'}

    episodio = 1
    patron = r'<a href="http:\/\/link[^a]+animetubeita[^c]+com\/[^\/]+\/[^s]+((?:stream|strm))[^p]+php(\?.*?)"'
    for phpfile, scrapedurl in scrapedAll(item.url, patron):
        title = "Episodio " + str(episodio)
        episodio += 1
        url = "%s/%s.php%s" % (host, phpfile, scrapedurl)
        headers['Referer'] =  url
        data = httptools.downloadpage(url, headers=headers).data
        # ------------------------------------------------
        cookies = ""
        matches = re.compile('(.animetubeita.com.*?)\n', re.DOTALL).findall(config.get_cookie_data())
        for cookie in matches:
            name = cookie.split('\t')[5]
            value = cookie.split('\t')[6]
            cookies += name + "=" + value + ";"
        headers['Cookie'] = cookies[:-1]
        # ------------------------------------------------
        url = scrapertools.find_single_match(data, """<source src="([^"]+)" type='video/mp4'>""")
        url += '|' + urllib.urlencode(headers)
        itemlist.append(Item(channel=item.channel,
                             action="play",
                             title="[COLOR azure]" + title + "[/COLOR]",
                             url=url,
                             thumbnail=item.thumbnail,
                             fanart=item.thumbnail,
                             plot=item.plot))

    return itemlist



def search(item, texto):
    log("animetubeita", "search", item.channel)
    item.url = item.url + texto

    try:
        return lista_home(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []



def scrapedAll(url="", patron=""):
    matches = []
    data = httptools.downloadpage(url).data
    MyPatron = patron
    matches = re.compile(MyPatron, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    return matches



def scrapedSingle(url="", single="", patron=""):
    matches = []
    data = httptools.downloadpage(url).data
    elemento = scrapertools.find_single_match(data, single)
    matches = re.compile(patron, re.DOTALL).findall(elemento)
    scrapertools.printMatches(matches)

    return matches



def log(funzione="", stringa="", canale=""):
    logger.debug("[" + canale + "].[" + funzione + "] " + stringa)



AnimeThumbnail = "http://img15.deviantart.net/f81c/i/2011/173/7/6/cursed_candies_anime_poster_by_careko-d3jnzg9.jpg"
AnimeFanart = "http://www.animetubeita.com/wp-content/uploads/21407_anime_scenery.jpg"
CategoriaThumbnail = "http://static.europosters.cz/image/750/poster/street-fighter-anime-i4817.jpg"
CategoriaFanart = "http://www.animetubeita.com/wp-content/uploads/21407_anime_scenery.jpg"
CercaThumbnail = "http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search"
CercaFanart = "https://i.ytimg.com/vi/IAlbvyBdYdY/maxresdefault.jpg"
AvantiTxt = config.get_localized_string(30992)
AvantiImg = "http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png"

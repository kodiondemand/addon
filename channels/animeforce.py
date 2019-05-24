# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per http://animeinstreaming.net/
# ------------------------------------------------------------
import re
import urllib
import urlparse

from core import httptools, scrapertools, servertools, tmdb
from core.item import Item
from platformcode import config, logger
from servers.decrypters import adfly

host = "https://ww1.animeforce.org"

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()

headers = [['Referer', host]]

PERPAGE = 20


# -----------------------------------------------------------------
def mainlist(item):
    log("mainlist", "mainlist", item.channel)
    itemlist = [Item(channel=item.channel,
                     action="lista_anime",
                     title="[COLOR azure]Anime [/COLOR]- [COLOR lightsalmon]Lista Completa[/COLOR]",
                     url=host + "/lista-anime/",
                     thumbnail=CategoriaThumbnail,
                     fanart=CategoriaFanart),
                Item(channel=item.channel,
                     action="animeaggiornati",
                     title="[COLOR azure]Anime Aggiornati[/COLOR]",
                     url=host,
                     thumbnail=CategoriaThumbnail,
                     fanart=CategoriaFanart),
                Item(channel=item.channel,
                     action="ultimiep",
                     title="[COLOR azure]Ultimi Episodi[/COLOR]",
                     url=host,
                     thumbnail=CategoriaThumbnail,
                     fanart=CategoriaFanart),
                Item(channel=item.channel,
                     action="search",
                     title="[COLOR yellow]Cerca ...[/COLOR]",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

    return itemlist


# =================================================================

# -----------------------------------------------------------------
def newest(categoria):
    log("newest", "newest" + categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "anime":
            item.url = host
            item.action = "ultimiep"
            itemlist = ultimiep(item)

            if itemlist[-1].action == "ultimiep":
                itemlist.pop()
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


# =================================================================

# -----------------------------------------------------------------
def search(item, texto):
    log("search", "search", item.channel)
    item.url = host + "/?s=" + texto
    try:
        return search_anime(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


# =================================================================

# -----------------------------------------------------------------
def search_anime(item):
    log("search_anime", "search_anime", item.channel)
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = r'<a href="([^"]+)"><img.*?src="([^"]+)".*?title="([^"]+)".*?/>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        if "Sub Ita Download & Streaming" in scrapedtitle or "Sub Ita Streaming":
            if 'episodio' in scrapedtitle.lower():
                itemlist.append(episode_item(item, scrapedtitle, scrapedurl, scrapedthumbnail))
            else:
                scrapedtitle, eptype = clean_title(scrapedtitle, simpleClean=True)
                cleantitle, eptype = clean_title(scrapedtitle)

                scrapedurl, total_eps = create_url(scrapedurl, cleantitle)

                itemlist.append(
                    Item(channel=item.channel,
                        action="episodios",
                        text_color="azure",
                        contentType="tvshow",
                        title=scrapedtitle,
                        url=scrapedurl,
                        fulltitle=cleantitle,
                        show=cleantitle,
                        thumbnail=scrapedthumbnail))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Next Page
    next_page = scrapertools.find_single_match(data, r'<link rel="next" href="([^"]+)"[^/]+/>')
    if next_page != "":
        itemlist.append(
            Item(channel=item.channel,
                 action="search_anime",
                 text_bold=True,
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=next_page,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png"))

    return itemlist


# =================================================================

# -----------------------------------------------------------------
def animeaggiornati(item):
    log("animeaggiornati", "animeaggiornati", item.channel)
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    patron = r'<img.*?src="([^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+><a href="([^"]+)">([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        if 'Streaming' in scrapedtitle:
            cleantitle, eptype = clean_title(scrapedtitle)
            
            # Creazione URL
            scrapedurl, total_eps = create_url(scrapedurl, scrapedtitle)

            itemlist.append(
                Item(channel=item.channel,
                     action="episodios",
                     text_color="azure",
                     contentType="tvshow",
                     title=cleantitle,
                     url=scrapedurl,
                     fulltitle=cleantitle,
                     show=cleantitle,
                     thumbnail=scrapedthumbnail))
    
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


# =================================================================

# -----------------------------------------------------------------
def ultimiep(item):
    log("ultimiep", "ultimiep", item.channel)
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    patron = r'<img.*?src="([^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+><a href="([^"]+)">([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        if 'Streaming' in scrapedtitle:
            itemlist.append(episode_item(item, scrapedtitle, scrapedurl, scrapedthumbnail))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


# =================================================================

# -----------------------------------------------------------------
def lista_anime(item):
    log("lista_anime", "lista_anime", item.channel)

    itemlist = []

    p = 1
    if '{}' in item.url:
        item.url, p = item.url.split('{}')
        p = int(p)

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data

    # Estrae i contenuti 
    patron = r'<li>\s*<strong>\s*<a\s*href="([^"]+?)">([^<]+?)</a>\s*</strong>\s*</li>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    scrapedplot = ""
    scrapedthumbnail = ""
    for i, (scrapedurl, scrapedtitle) in enumerate(matches):
        if (p - 1) * PERPAGE > i: continue
        if i >= p * PERPAGE: break

        # Pulizia titolo
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        cleantitle, eptype = clean_title(scrapedtitle, simpleClean=True)

        itemlist.append(
            Item(channel=item.channel,
                 extra=item.extra,
                 action="episodios",
                 text_color="azure",
                 contentType="tvshow",
                 title=cleantitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 fulltitle=cleantitle,
                 show=cleantitle,
                 plot=scrapedplot,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if len(matches) >= p * PERPAGE:
        scrapedurl = item.url + '{}' + str(p + 1)
        itemlist.append(
            Item(channel=item.channel,
                 extra=item.extra,
                 action="lista_anime",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))

    return itemlist


# =================================================================

# -----------------------------------------------------------------
def episodios(item):
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = '<td style="[^"]*?">\s*.*?<strong>(.*?)</strong>.*?\s*</td>\s*<td style="[^"]*?">\s*<a href="([^"]+?)"[^>]+>\s*<img.*?src="([^"]+?)".*?/>\s*</a>\s*</td>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    vvvvid_videos = False
    for scrapedtitle, scrapedurl, scrapedimg in matches:
        if 'nodownload' in scrapedimg or 'nostreaming' in scrapedimg:
            continue
        if 'vvvvid' in scrapedurl.lower():
            if not vvvvid_videos: vvvvid_videos = True
            itemlist.append(Item(title='I Video VVVVID Non sono supportati', text_color="red"))
            continue

        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        scrapedtitle = re.sub(r'<[^>]*?>', '', scrapedtitle)
        scrapedtitle = '[COLOR azure][B]' + scrapedtitle + '[/B][/COLOR]'
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentType="episode",
                 title=scrapedtitle,
                 url=urlparse.urljoin(host, scrapedurl),
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 plot=item.plot,
                 fanart=item.fanart,
                 thumbnail=item.thumbnail))

    # Comandi di servizio
    if config.get_videolibrary_support() and len(itemlist) != 0 and not vvvvid_videos:
        itemlist.append(
            Item(channel=item.channel,
                 title=config.get_localized_string(30161),
                 text_color="yellow",
                 text_bold=True,
                 url=item.url,
                 action="add_serie_to_library",
                 extra="episodios",
                 show=item.show))

    return itemlist


# ==================================================================

# -----------------------------------------------------------------
def findvideos(item):
    logger.info("kod.animeforce findvideos")

    itemlist = []

    if item.extra:
        data = httptools.downloadpage(item.url, headers=headers).data

        blocco = scrapertools.find_single_match(data, r'%s(.*?)</tr>' % item.extra)
        url = scrapertools.find_single_match(blocco, r'<a href="([^"]+)"[^>]*>')
        if 'vvvvid' in url.lower():
            itemlist = [Item(title='I Video VVVVID Non sono supportati', text_color="red")]
            return itemlist
        if 'http' not in url: url = "".join(['https:', url])
    else:
        url = item.url

    if 'adf.ly' in url:
        url = adfly.get_long_url(url)
    elif 'bit.ly' in url:
        url = httptools.downloadpage(url, only_headers=True, follow_redirects=False).headers.get("location")

    if 'animeforce' in url:
        headers.append(['Referer', item.url])
        data = httptools.downloadpage(url, headers=headers).data
        itemlist.extend(servertools.find_video_items(data=data))

        for videoitem in itemlist:
            videoitem.title = item.title + videoitem.title
            videoitem.fulltitle = item.fulltitle
            videoitem.show = item.show
            videoitem.thumbnail = item.thumbnail
            videoitem.channel = item.channel
            videoitem.contentType = item.contentType

        url = url.split('&')[0]
        data = httptools.downloadpage(url, headers=headers).data
        patron = """<source\s*src=(?:"|')([^"']+?)(?:"|')\s*type=(?:"|')video/mp4(?:"|')>"""
        matches = re.compile(patron, re.DOTALL).findall(data)
        headers.append(['Referer', url])
        for video in matches:
            itemlist.append(Item(channel=item.channel, action="play", title=item.title,
                                 url=video + '|' + urllib.urlencode(dict(headers)), folder=False))
    else:
        itemlist.extend(servertools.find_video_items(data=url))

        for videoitem in itemlist:
            videoitem.title = item.title + videoitem.title
            videoitem.fulltitle = item.fulltitle
            videoitem.show = item.show
            videoitem.thumbnail = item.thumbnail
            videoitem.channel = item.channel
            videoitem.contentType = item.contentType

    return itemlist


# ==================================================================

# =================================================================
# Funzioni di servizio
# -----------------------------------------------------------------
def scrapedAll(url="", patron=""):
    data = httptools.downloadpage(url).data
    MyPatron = patron
    matches = re.compile(MyPatron, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    return matches


# =================================================================

# -----------------------------------------------------------------
def create_url(url, title, eptype=""):
    logger.info()

    if 'download' not in url:
        url = url.replace('-streaming', '-download-streaming')

    total_eps = ""
    if not eptype:
        url = re.sub(r'episodio?-?\d+-?(?:\d+-|)[oav]*', '', url)
    else: # Solo se è un episodio passa
        total_eps = scrapertools.find_single_match(title.lower(), r'\((\d+)-(?:episodio|sub-ita)\)') # Questo numero verrà rimosso dall'url
        if total_eps: url = url.replace('%s-' % total_eps, '')
        url = re.sub(r'%s-?\d*-' % eptype.lower(), '', url)
    url = url.replace('-fine', '')

    return url, total_eps

# =================================================================

# -----------------------------------------------------------------
def clean_title(title, simpleClean=False):
    logger.info()

    title = title.replace("Streaming", "").replace("&", "")
    title = title.replace("Download", "")
    title = title.replace("Sub Ita", "")
    cleantitle = title.replace("#038;", "").replace("amp;", "").strip()

    if '(Fine)' in title:
        cleantitle = cleantitle.replace('(Fine)', '').strip() + " (Fine)"
    eptype = ""
    if not simpleClean:
        if "episodio" in title.lower():
            eptype = scrapertools.find_single_match(title, "((?:Episodio?|OAV))")
            cleantitle = re.sub(r'%s\s*\d*\s*(?:\(\d+\)|)' % eptype, '', title).strip()

            if 'episodio' not in eptype.lower():
                cleantitle = re.sub(r'Episodio?\s*\d+\s*(?:\(\d+\)|)\s*[\(OAV\)]*', '', cleantitle).strip()

            if '(Fine)' in title:
                cleantitle = cleantitle.replace('(Fine)', '')

    return cleantitle, eptype

# =================================================================

# -----------------------------------------------------------------
def episode_item(item, scrapedtitle, scrapedurl, scrapedthumbnail):
    scrapedtitle, eptype = clean_title(scrapedtitle, simpleClean=True)
    cleantitle, eptype = clean_title(scrapedtitle)

    # Creazione URL
    scrapedurl, total_eps = create_url(scrapedurl, scrapedtitle, eptype)

    epnumber = ""
    if 'episodio' in eptype.lower():
        epnumber = scrapertools.find_single_match(scrapedtitle.lower(), r'episodio?\s*(\d+)')
        eptype += ":? %s%s" % (epnumber, (r" \(%s\):?" % total_eps) if total_eps else "")

    extra = "<tr>\s*<td[^>]+><strong>(?:[^>]+>|)%s(?:[^>]+>[^>]+>|[^<]*|[^>]+>)</strong>" % eptype
    item = Item(channel=item.channel,
         action="findvideos",
         contentType="tvshow",
         title=scrapedtitle,
         text_color="azure",
         url=scrapedurl,
         fulltitle=cleantitle,
         extra=extra,
         show=cleantitle,
         thumbnail=scrapedthumbnail)
    return item

# =================================================================

# -----------------------------------------------------------------
def scrapedSingle(url="", single="", patron=""):
    data = httptools.downloadpage(url).data
    paginazione = scrapertools.find_single_match(data, single)
    matches = re.compile(patron, re.DOTALL).findall(paginazione)
    scrapertools.printMatches(matches)

    return matches


# =================================================================

# -----------------------------------------------------------------
def Crea_Url(pagina="1", azione="ricerca", categoria="", nome=""):
    # esempio
    # chiamate.php?azione=ricerca&cat=&nome=&pag=
    Stringa = host + "chiamate.php?azione=" + azione + "&cat=" + categoria + "&nome=" + nome + "&pag=" + pagina
    log("crea_Url", Stringa)
    return Stringa


# =================================================================

# -----------------------------------------------------------------
def log(funzione="", stringa="", canale=""):
    logger.debug("[" + canale + "].[" + funzione + "] " + stringa)


# =================================================================

# =================================================================
# riferimenti di servizio
# -----------------------------------------------------------------
AnimeThumbnail = "http://img15.deviantart.net/f81c/i/2011/173/7/6/cursed_candies_anime_poster_by_careko-d3jnzg9.jpg"
AnimeFanart = "https://i.ytimg.com/vi/IAlbvyBdYdY/maxresdefault.jpg"
CategoriaThumbnail = "http://static.europosters.cz/image/750/poster/street-fighter-anime-i4817.jpg"
CategoriaFanart = "https://i.ytimg.com/vi/IAlbvyBdYdY/maxresdefault.jpg"
CercaThumbnail = "http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search"
CercaFanart = "https://i.ytimg.com/vi/IAlbvyBdYdY/maxresdefault.jpg"
AvantiTxt = config.get_localized_string(30992)
AvantiImg = "http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png"

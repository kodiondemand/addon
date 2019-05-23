# -*- coding: utf-8 -*-
# Ringraziamo Icarus crew
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per AnimeSubIta
# ------------------------------------------------------------

import re, urllib, urlparse

from core import servertools, httptools, scrapertools, tmdb, support
from platformcode import logger, config
from core.item import Item



host = "http://www.animesubita.org"

PERPAGE = 20

# ----------------------------------------------------------------------------------------------------------------
def mainlist(item):
    logger.info()
    itemlist = [Item(channel=item.channel,
                     action="lista_anime_completa",
                     title=support.color("Lista Anime", "azure"),
                     url="%s/lista-anime/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="ultimiep",
                     title=support.color("Ultimi Episodi", "azure"),
                     url="%s/category/ultimi-episodi/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="lista_anime",
                     title=support.color("Anime in corso", "azure"),
                     url="%s/category/anime-in-corso/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="categorie",
                     title=support.color("Categorie", "azure"),
                     url="%s/generi/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="search",
                     title=support.color("Cerca anime ...", "yellow"),
                     extra="anime",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")
                ]

    return itemlist

# ================================================================================================================
# ----------------------------------------------------------------------------------------------------------------
def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == "anime":
            item.url = host
            item.action = "ultimiep"
            itemlist = ultimiep(item)

            if itemlist[-1].action == "ultimiep":
                itemlist.pop()
    # Continua l'esecuzione in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist

# ================================================================================================================
# ----------------------------------------------------------------------------------------------------------------
def search(item, texto):
    logger.info()
    item.url = host + "/?s=" + texto
    try:
        return lista_anime(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def categorie(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    patron = r'<li><a title="[^"]+" href="([^"]+)">([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(
                Item(channel=item.channel,
                     action="lista_anime",
                     title=scrapedtitle.replace('Anime', '').strip(),
                     text_color="azure",
                     url=scrapedurl,
                     thumbnail=item.thumbnail,
                     folder=True))

    return itemlist

# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def ultimiep(item):
    logger.info("ultimiep")
    itemlist = lista_anime(item, False, False)

    for itm in itemlist:
        title = scrapertools.decodeHtmlentities(itm.title)
        # Pulizia titolo
        title = title.replace("Streaming", "").replace("&", "")
        title = title.replace("Download", "")
        title = title.replace("Sub Ita", "").strip()
        eptype = scrapertools.find_single_match(title, "((?:Episodio?|OAV))")
        cleantitle = re.sub(r'%s\s*\d*\s*(?:\(\d+\)|)' % eptype, '', title).strip()
        # Creazione URL
        url = re.sub(r'%s-?\d*-' % eptype.lower(), '', itm.url)
        if "-streaming" not in url:
            url = url.replace("sub-ita", "sub-ita-streaming")

        epnumber = ""
        if 'episodio' in eptype.lower():
            epnumber = scrapertools.find_single_match(title.lower(), r'episodio?\s*(\d+)')
            eptype += ":? " + epnumber
                
        extra = "<tr>\s*<td[^>]+><strong>(?:[^>]+>|)%s(?:[^>]+>[^>]+>|[^<]*|[^>]+>)</strong>" % eptype
        itm.title = support.color(title, 'azure').strip()
        itm.action = "findvideos"
        itm.url = url
        itm.fulltitle = cleantitle
        itm.extra = extra
        itm.show = re.sub(r'Episodio\s*', '', title)
        itm.thumbnail = item.thumbnail
    
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist

# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def lista_anime(item, nextpage=True, show_lang=True):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    blocco = scrapertools.find_single_match(data, r'<div class="post-list group">(.*?)</nav><!--/.pagination-->')
    # patron = r'<a href="([^"]+)" title="([^"]+)">\s*<img[^s]+src="([^"]+)"[^>]+>' # Patron con thumbnail, Kodi non scarica le immagini dal sito
    patron = r'<a href="([^"]+)" title="([^"]+)">'
    matches = re.compile(patron, re.DOTALL).findall(blocco)

    for scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        scrapedtitle = re.sub(r'\s+', ' ', scrapedtitle)
        # Pulizia titolo
        scrapedtitle = scrapedtitle.replace("Streaming", "").replace("&", "")
        scrapedtitle = scrapedtitle.replace("Download", "")
        lang = scrapertools.find_single_match(scrapedtitle, r"([Ss][Uu][Bb]\s*[Ii][Tt][Aa])")
        scrapedtitle = scrapedtitle.replace("Sub Ita", "").strip()
        eptype = scrapertools.find_single_match(scrapedtitle, "((?:Episodio?|OAV))")
        cleantitle = re.sub(r'%s\s*\d*\s*(?:\(\d+\)|)' % eptype, '', scrapedtitle)


        cleantitle = cleantitle.replace(lang, "").strip()

        itemlist.append(
            Item(channel=item.channel,
                 action="episodi",
                 contentType="tvshow" if 'oav' not in scrapedtitle.lower() else "movie",
                 title=color(scrapedtitle.replace(lang, "(%s)" % support.color(lang, "red") if show_lang else "").strip(), 'azure'),
                 fulltitle=cleantitle,
                 url=scrapedurl,
                 show=cleantitle,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if nextpage:
        patronvideos = r'<link rel="next" href="([^"]+)"\s*/>'
        matches = re.compile(patronvideos, re.DOTALL).findall(data)
        
        if len(matches) > 0:
            scrapedurl = matches[0]
            itemlist.append(
                Item(channel=item.channel,
                    action="lista_anime",
                    title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                    url=scrapedurl,
                    thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                    folder=True))

    return itemlist

# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def lista_anime_completa(item):
    logger.info()
    itemlist = []

    p = 1
    if '{}' in item.url:
        item.url, p = item.url.split('{}')
        p = int(p)

    data = httptools.downloadpage(item.url).data
    blocco = scrapertools.find_single_match(data, r'<ul class="lcp_catlist"[^>]+>(.*?)</ul>')
    patron = r'<a href="([^"]+)"[^>]+>([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(blocco)

    for i, (scrapedurl, scrapedtitle) in enumerate(matches):
        if (p - 1) * PERPAGE > i: continue
        if i >= p * PERPAGE: break

        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle.strip())
        cleantitle = scrapedtitle.replace("Sub Ita Streaming", "").replace("Ita Streaming", "")

        itemlist.append(
            Item(channel=item.channel,
                 action="episodi",
                 contentType="tvshow" if 'oav' not in scrapedtitle.lower() else "movie",
                 title=support.color(scrapedtitle, 'azure'),
                 fulltitle=cleantitle,
                 show=cleantitle,
                 url=scrapedurl,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if len(matches) >= p * PERPAGE:
        scrapedurl = item.url + '{}' + str(p + 1)
        itemlist.append(
            Item(channel=item.channel,
                 extra=item.extra,
                 action="lista_anime_completa",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))

    return itemlist

# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def episodi(item):
    logger.info()
    itemlist = []
    
    data = httptools.downloadpage(item.url).data

    patron = '<td style="[^"]*?">\s*.*?<strong>(.*?)</strong>.*?\s*</td>\s*<td style="[^"]*?">\s*<a href="([^"]+?)"[^>]+>\s*<img.*?src="([^"]+?)".*?/>\s*</a>\s*</td>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedtitle, scrapedurl, scrapedimg in matches:
        if 'nodownload' in scrapedimg or 'nostreaming' in scrapedimg:
            continue
        if 'vvvvid' in scrapedurl.lower():
            itemlist.append(Item(title='I Video VVVVID Non sono supportati'))
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
                 fulltitle=item.title,
                 show=scrapedtitle,
                 plot=item.plot,
                 fanart=item.thumbnail,
                 thumbnail=item.thumbnail))

    # Comandi di servizio
    if config.get_videolibrary_support() and len(itemlist) != 0:
        itemlist.append(
            Item(channel=item.channel,
                 title="[COLOR lightblue]%s[/COLOR]" % config.get_localized_string(30161),
                 url=item.url,
                 action="add_serie_to_library",
                 extra="episodios",
                 show=item.show))

    return itemlist

# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def findvideos(item):
    logger.info()
    itemlist = []

    headers = {'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:52.0) Gecko/20100101 Firefox/52.0'}

    if item.extra:
        data = httptools.downloadpage(item.url, headers=headers).data
        blocco = scrapertools.find_single_match(data, r'%s(.*?)</tr>' % item.extra)
        item.url = scrapertools.find_single_match(blocco, r'<a href="([^"]+)"[^>]+>')

    patron = r'http:\/\/link[^a]+animesubita[^o]+org\/[^\/]+\/.*?(episodio\d*)[^p]+php(\?.*)'
    for phpfile, scrapedurl in re.findall(patron, item.url, re.DOTALL):
        url = "%s/%s.php%s" % (host, phpfile, scrapedurl)
        headers['Referer'] =  url
        data = httptools.downloadpage(url, headers=headers).data
        # ------------------------------------------------
        cookies = ""
        matches = re.compile('(.%s.*?)\n' % host.replace("http://", "").replace("www.", ""), re.DOTALL).findall(config.get_cookie_data())
        for cookie in matches:
            name = cookie.split('\t')[5]
            value = cookie.split('\t')[6]
            cookies += name + "=" + value + ";"
        headers['Cookie'] = cookies[:-1]
        # ------------------------------------------------
        scrapedurl = scrapertools.find_single_match(data, r'<source src="([^"]+)"[^>]+>')
        url = scrapedurl + '|' + urllib.urlencode(headers)
        itemlist.append(
            Item(channel=item.channel,
                action="play",
                text_color="azure",
                title="[%s] %s" % (support.color("Diretto", "orange"), item.title),
                fulltitle=item.fulltitle,
                url=url,
                thumbnail=item.thumbnail,
                fanart=item.thumbnail,
                plot=item.plot))

    return itemlist

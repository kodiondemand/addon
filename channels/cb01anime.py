# -*- coding: utf-8 -*-
# Ringraziamo Icarus crew
# ------------------------------------------------------------
# XBMC Plugin
# Canale  per cineblog01 - anime
# ------------------------------------------------------------
import re

from core import httptools, scrapertools, servertools, tmdb
from core.item import Item
from platformcode import logger, config

host = "https://www.cineblog01.pink"

#esclusione degli articoli 'di servizio'
blacklist = ['AVVISO IMPORTANTE – CB01.ROCKS', 'Lista Alfabetica Completa Anime/Cartoon', 'CB01.UNO ▶ TROVA L’INDIRIZZO UFFICIALE']

# -----------------------------------------------------------------
def mainlist(item):
    logger.info("[cb01anime.py] mainlist")

    # Main options
    itemlist = [Item(channel=item.channel,
                     action="list_titles",
                     title="[COLOR azure]Anime - Novita'[/COLOR]",
                     url=host + '/anime',
                     thumbnail="http://orig09.deviantart.net/df5a/f/2014/169/2/a/fist_of_the_north_star_folder_icon_by_minacsky_saya-d7mq8c8.png"),
                Item(channel=item.channel,
                     action="genere",
                     title="[COLOR azure]Anime - Per Genere[/COLOR]",
                     url=host + '/anime',
                     thumbnail="http://xbmc-repo-ackbarr.googlecode.com/svn/trunk/dev/skin.cirrus%20extended%20v2/extras/moviegenres/Genres.png"),
                Item(channel=item.channel,
                     action="alfabetico",
                     title="[COLOR azure]Anime - Per Lettera A-Z[/COLOR]",
                     url=host + '/anime',
                     thumbnail="http://i.imgur.com/IjCmx5r.png"),
                Item(channel=item.channel,
                     action="listacompleta",
                     title="[COLOR azure]Anime - Lista Completa[/COLOR]",
                     url="%s/anime/lista-completa-anime-cartoon/" % host,
                     thumbnail="http://i.imgur.com/IjCmx5r.png"),
                Item(channel=item.channel,
                     action="search",
                     title="[COLOR yellow]Cerca Anime[/COLOR]",
                     extra="anime",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

    return itemlist


# =================================================================

# -----------------------------------------------------------------
def genere(item):
    logger.info("[cb01anime.py] genere")

    return build_itemlist(item, '<select name="select2"(.*?)</select>', '<option value="([^"]+)">([^<]+)</option>',
                          "list_titles")


def alfabetico(item):
    logger.info("[cb01anime.py] alfabetico")

    return build_itemlist(item, '<option value=\'-1\'>Anime per Lettera</option>(.*?)</select>',
                          '<option value="([^"]+)">\(([^<]+)\)</option>', "list_titles")


def listacompleta(item):
    logger.info("[cb01anime.py] listacompleta")

    return build_itemlist(item,
                          '<a href="#char_5a" title="Go to the letter Z">Z</a></span></div>(.*?)</ul></div><div style="clear:both;"></div></div>',
                          '<li><a href="' + host + '([^"]+)"><span class="head">([^<]+)</span></a></li>', "episodios")


def build_itemlist(item, re_bloque, re_patron, iaction):
    itemlist = []

    data = httptools.downloadpage(item.url).data

    # Narrow search by selecting only the combo
    bloque = scrapertools.find_single_match(data, re_bloque)

    # The categories are the options for the combo
    matches = re.compile(re_patron, re.DOTALL).findall(bloque)
    scrapertools.printMatches(matches)

    for url, titulo in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action=iaction,
                 contentType="tvshow",
                 title=titulo,
                 fulltitle=titulo,
                 text_color="azure",
                 show=titulo,
                 url=host + url,
                 plot=""))

    return itemlist


# =================================================================


# -----------------------------------------------------------------
def search(item, texto):
    logger.info("[cb01anime.py] " + item.url + " search " + texto)

    item.url = host + "/anime/?s=" + texto

    return list_titles(item)


# =================================================================

# -----------------------------------------------------------------
def list_titles(item):
    logger.info("[cb01anime.py] mainlist")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data

    # Estrae i contenuti 
    patronvideos = r'<div class="span4">\s*<a href="([^"]+)">'
    patronvideos += r'<img src="([^"]+)"[^>]+><\/a>[^>]+>[^>]+>'
    patronvideos += r'[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(.*?)<\/a>'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        scrapedtitle = scrapertools.htmlclean(scrapedtitle).strip()
        if not scrapedtitle in blacklist:
            if 'lista richieste' in scrapedtitle.lower(): continue

            patron = r'(?:\[[Ff][Uu][Ll]{2}\s*[Ii][Tt][Aa]\]|\[[Ss][Uu][Bb]\s*[Ii][Tt][Aa]\])'
            cleantitle = re.sub(patron, '', scrapedtitle).strip()

            ## ------------------------------------------------
            scrapedthumbnail = httptools.get_url_headers(scrapedthumbnail)
            ## ------------------------------------------------

            # Añade al listado de XBMC
            itemlist.append(
                Item(channel=item.channel,
                    action="listacompleta" if "Lista Alfabetica Completa Anime/Cartoon" in scrapedtitle else "episodios",
                    contentType="tvshow",
                    title=scrapedtitle,
                    fulltitle=cleantitle,
                    text_color="azure",
                    show=cleantitle,
                    url=scrapedurl,
                    thumbnail=scrapedthumbnail,
                    viewmode="movie_with_plot"))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Put the next page mark
    try:
        next_page = scrapertools.find_single_match(data, "<link rel='next' href='([^']+)'")
        itemlist.append(
            Item(channel=item.channel,
                 action="list_titles",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=next_page,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png"))
    except:
        pass

    return itemlist


# =================================================================


# -----------------------------------------------------------------
def episodios(item):
    logger.info("[cb01anime.py] episodios")

    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data
    # data = scrapertools.decodeHtmlentities(data)

    patron1 = '(?:<p>|<td bgcolor="#ECEAE1">)<span class="txt_dow">(.*?)(?:</p>)?(?:\s*</span>)?\s*</td>'
    patron2 = '<a.*?href="([^"]+)"[^>]*>([^<]+)</a>'
    matches1 = re.compile(patron1, re.DOTALL).findall(data)
    if len(matches1) > 0:
        for match1 in re.split('<br />|<p>', matches1[0]):
            if len(match1) > 0:
                # Estrae i contenuti 
                titulo = None
                scrapedurl = ''
                matches2 = re.compile(patron2, re.DOTALL).finditer(match1)
                for match2 in matches2:
                    if titulo is None:
                        titulo = match2.group(2)
                    scrapedurl += match2.group(1) + '#' + match2.group(2) + '|'
                if titulo is not None:
                    title = item.title + " " + titulo
                    itemlist.append(
                        Item(channel=item.channel,
                             action="findvideos",
                             contentType="episode",
                             title=title,
                             extra=scrapedurl,
                             fulltitle=item.fulltitle,
                             show=item.show))

    if config.get_videolibrary_support() and len(itemlist) != 0:
        itemlist.append(
            Item(channel=item.channel,
                 title="[COLOR lightblue]%s[/COLOR]" % config.get_localized_string(30161),
                 url=item.url,
                 action="add_serie_to_library",
                 extra="episodios",
                 show=item.show))

    return itemlist


# =================================================================


# -----------------------------------------------------------------
def findvideos(item):
    logger.info("[cb01anime.py] findvideos")

    itemlist = []

    for match in item.extra.split(r'|'):
        match_split = match.split(r'#')
        scrapedurl = match_split[0]
        if len(scrapedurl) > 0:
            scrapedtitle = match_split[1]
            title = item.title + " [COLOR blue][" + scrapedtitle + "][/COLOR]"
            itemlist.append(
                Item(channel=item.channel,
                     action="play",
                     title=title,
                     url=scrapedurl,
                     fulltitle=item.fulltitle,
                     show=item.show,
                     ontentType=item.contentType,
                     folder=False))

    return itemlist


# =================================================================


# -----------------------------------------------------------------
def play(item):
    logger.info("[cb01anime.py] play")

    if '/goto/' in item.url:
        item.url = item.url.split('/goto/')[-1].decode('base64')

    data = item.url

    logger.debug("##### Play data ##\n%s\n##" % data)
    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.show
        videoitem.fulltitle = item.fulltitle
        videoitem.show = item.show
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
        videoitem.contentType = item.contentType

    return itemlist


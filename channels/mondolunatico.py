# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale mondolunatico
# ------------------------------------------------------------
import os
import re
import time
import urllib

import urlparse

from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config
from platformcode import logger

__channel__ = "mondolunatico"

host = "http://mondolunatico.org"

captcha_url = '%s/pass/CaptchaSecurityImages.php?width=100&height=40&characters=5' % host

PERPAGE = 25


def mainlist(item):
    logger.info("kod.mondolunatico mainlist")
    itemlist = [Item(channel=item.channel,
                     title="[COLOR azure]Novità[/COLOR]",
                     extra="movie",
                     action="peliculas",
                     url=host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR azure]Categorie[/COLOR]",
                     extra="movie",
                     action="categorias",
                     url=host,
                     thumbnail="http://xbmc-repo-ackbarr.googlecode.com/svn/trunk/dev/skin.cirrus%20extended%20v2/extras/moviegenres/All%20Movies%20by%20Genre.png"),
                Item(channel=item.channel,
                     title="[COLOR yellow]Cerca...[/COLOR]",
                     extra="movie",
                     action="search",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

                #Item(channel=item.channel,
                #     title="[COLOR azure]Serie TV[/COLOR]",
                #     extra="tvshow",
                #     action="serietv",
                #     url="%s/serietv/lista-alfabetica/" % host,
                #     thumbnail="http://i.imgur.com/rO0ggX2.png"),
                #Item(channel=item.channel,
                #     title="[COLOR yellow]Cerca Serie TV...[/COLOR]",
                #     extra="tvshow",
                #     action="search",
                #     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search"),]
    return itemlist


def categorias(item):
    logger.info("kod.mondolunatico categorias")
    itemlist = []

    data = httptools.downloadpage(item.url).data

    # Narrow search by selecting only the combo
    bloque = scrapertools.find_single_match(data, '<option class="level-0" value="7">(.*?)<option class="level-0" value="8">')

    # The categories are the options for the combo
    patron = '<option class=[^=]+="([^"]+)">(.*?)<'
    matches = re.compile(patron, re.DOTALL).findall(bloque)

    for scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapedtitle.replace("&nbsp;", "")
        scrapedtitle = scrapedtitle.replace("(", "")
        scrapedtitle = scrapedtitle.replace(")", "")
        scrapedtitle = scrapedtitle.replace("0", "")
        scrapedtitle = scrapedtitle.replace("1", "")
        scrapedtitle = scrapedtitle.replace("2", "")
        scrapedtitle = scrapedtitle.replace("3", "")
        scrapedtitle = scrapedtitle.replace("4", "")
        scrapedtitle = scrapedtitle.replace("5", "")
        scrapedtitle = scrapedtitle.replace("6", "")
        scrapedtitle = scrapedtitle.replace("7", "")
        scrapedtitle = scrapedtitle.replace("8", "")
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle.replace("9", ""))
        scrapedurl = host + "/category/film-per-genere/" + scrapedtitle
        scrapedthumbnail = ""
        scrapedplot = ""
        itemlist.append(
            Item(channel=item.channel,
                 extra=item.extra,
                 action="peliculas",
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot))

    return itemlist


def search(item, texto):
    logger.info("[mondolunatico.py] " + item.url + " search " + texto)
    item.url = host + "/?s=" + texto
    try:
        if item.extra == "movie":
            return peliculas(item)
        if item.extra == "tvshow":
            item.url = "%s/serietv/lista-alfabetica/" % host
            return search_serietv(item, texto)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def peliculas(item):
    logger.info("kod.mondolunatico peliculas")

    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data

    # Estrae i contenuti 
    patron = '<div class="boxentry">\s*<a href="([^"]+)"[^>]+>\s*<img src="([^"]+)" alt="([^"]+)"[^>]+>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    scrapedplot = ""
    for scrapedurl, scrapedthumbnail, scrapedtitle, in matches:
        title = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(
            Item(channel=item.channel,
                 extra=item.extra,
                 action="findvideos",
                 contentType="movie",
                 title=title,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 fulltitle=title,
                 show=title,
                 plot=scrapedplot,
                 folder=True))

    # Paginazione
    patronvideos = '<a class="nextpostslink" rel="next" href="([^"]+)">'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)

    if len(matches) > 0:
        scrapedurl = urlparse.urljoin(item.url, matches[0])
        itemlist.append(
            Item(channel=item.channel,
                 extra=item.extra,
                 action="peliculas",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def serietv(item):
    logger.info("kod.mondolunatico serietv")

    itemlist = []

    p = 1
    if '{}' in item.url:
        item.url, p = item.url.split('{}')
        p = int(p)

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, '<h1>Lista Alfabetica</h1>(.*?)</div>')

    # Estrae i contenuti 
    patron = '<li><a href="([^"]+)">([^<]+)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    scrapedplot = ""
    scrapedthumbnail = ""
    for i, (scrapedurl, scrapedtitle) in enumerate(matches):
        if (p - 1) * PERPAGE > i: continue
        if i >= p * PERPAGE: break
        title = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(
            Item(channel=item.channel,
                 extra=item.extra,
                 action="episodios",
                 title=title,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 fulltitle=title,
                 show=title,
                 plot=scrapedplot,
                 folder=True))

    if len(matches) >= p * PERPAGE:
        scrapedurl = item.url + '{}' + str(p + 1)
        itemlist.append(
            Item(channel=item.channel,
                 extra=item.extra,
                 action="serietv",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def search_serietv(item, texto):
    logger.info("kod.mondolunatico serietv")

    texto = urllib.unquote_plus(texto).lower()

    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, '<h1>Lista Alfabetica</h1>(.*?)</div>')

    # Estrae i contenuti 
    patron = '<li><a href="([^"]+)">([^<]+)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    scrapedplot = ""
    scrapedthumbnail = ""
    for i, (scrapedurl, scrapedtitle) in enumerate(matches):
        title = scrapertools.decodeHtmlentities(scrapedtitle)
        if texto not in title.lower(): continue
        itemlist.append(
            Item(channel=item.channel,
                 extra=item.extra,
                 action="episodios",
                 title=title,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 fulltitle=title,
                 show=title,
                 plot=scrapedplot,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

def episodios(item):
    logger.info("kod.mondolunatico episodios")

    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data

    html = []

    for i in range(2):
        patron = 'href="(https?://www\.keeplinks\.eu/p92/([^"]+))"'
        matches = re.compile(patron, re.DOTALL).findall(data)
        for keeplinks, id in matches:
            _headers = [['Cookie', 'flag[' + id + ']=1; defaults=1; nopopatall=' + str(int(time.time()))],
                        ['Referer', keeplinks]]

            html.append(httptools.downloadpage(keeplinks, headers=_headers).data)

        patron = r'="(%s/pass/index\.php\?ID=[^"]+)"' % host
        matches = re.compile(patron, re.DOTALL).findall(data)
        for scrapedurl in matches:
            tmp = httptools.downloadpage(scrapedurl).data

            if 'CaptchaSecurityImages.php' in tmp:
                # Descarga el captcha
                img_content = httptools.downloadpage(captcha_url).data

                captcha_fname = os.path.join(config.get_data_path(), __channel__ + "captcha.img")
                with open(captcha_fname, 'wb') as ff:
                    ff.write(img_content)

                from platformcode import captcha

                keyb = captcha.Keyboard(heading='', captcha=captcha_fname)
                keyb.doModal()
                if keyb.isConfirmed():
                    captcha_text = keyb.getText()
                    post_data = urllib.urlencode({'submit1': 'Invia', 'security_code': captcha_text})
                    tmp = httptools.downloadpage(scrapedurl, post=post_data).data

                try:
                    os.remove(captcha_fname)
                except:
                    pass

            html.append(tmp)

        data = '\n'.join(html)

    encontrados = set()

    patron = '<p><a href="([^"]+?)">([^<]+?)</a></p>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapedtitle.split('/')[-1]
        if not scrapedtitle or scrapedtitle in encontrados: continue
        encontrados.add(scrapedtitle)
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(
            Item(channel=item.channel,
                 extra=item.extra,
                 action="findvideos",
                 title=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=item.thumbnail,
                 fulltitle=item.fulltitle,
                 show=item.show))

    patron = '<a href="([^"]+)" target="_blank" class="selecttext live">([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapedtitle.split('/')[-1]
        if not scrapedtitle or scrapedtitle in encontrados: continue
        encontrados.add(scrapedtitle)
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(
            Item(channel=item.channel,
                 extra=item.extra,
                 action="findvideos",
                 title=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=item.thumbnail,
                 fulltitle=item.fulltitle,
                 show=item.show))

    return itemlist


def findvideos(item):
    logger.info("kod.mondolunatico findvideos")

    itemlist = []

    # Carica la pagina 
    data = item.url if item.extra == "tvshow" else httptools.downloadpage(item.url).data

    # Estrae i contenuti 
    patron = r'noshade>(.*?)<br>.*?<a href="(%s/pass/index\.php\?ID=[^"]+)"' % host
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedtitle, scrapedurl in matches:
        scrapedtitle = scrapedtitle.replace('*', '').replace('Streaming', '').strip()
        title = '%s - [%s]' % (item.title, scrapedtitle)
        itemlist.append(
            Item(channel=item.channel,
                 action="play",
                 title=title,
                 url=scrapedurl,
                 thumbnail=item.thumbnail,
                 fulltitle=item.fulltitle,
                 show=item.show,
                 server='captcha',
                 folder=False))

    patron = 'href="(%s/stream/links/\d+/)"' % host
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl in matches:
        data += httptools.downloadpage(scrapedurl).data

    ### robalo fix obfuscator - start ####

    patron = 'href="(https?://www\.keeplinks\.(?:co|eu)/p92/([^"]+))"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for keeplinks, id in matches:
        headers = [['Cookie', 'flag[' + id + ']=1; defaults=1; nopopatall=' + str(int(time.time()))],
                   ['Referer', keeplinks]]

        html = httptools.downloadpage(keeplinks, headers=headers).data
        data += str(scrapertools.find_multiple_matches(html, '</lable><a href="([^"]+)" target="_blank"'))

    ### robalo fix obfuscator - end ####

    patron = 'src="([^"]+)" frameborder="0"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl in matches:
        data += httptools.downloadpage(scrapedurl).data

    for videoitem in servertools.find_video_items(data=data):
        videoitem.title = item.title + videoitem.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.show = item.show
        videoitem.plot = item.plot
        videoitem.channel = item.channel
        itemlist.append(videoitem)

    return itemlist


def play(item):
    logger.info("kod.mondolunatico play")

    itemlist = []

    if item.server == 'captcha':
        headers = [['Referer', item.url]]

        # Carica la pagina 
        data = httptools.downloadpage(item.url, headers=headers).data

        if 'CaptchaSecurityImages.php' in data:
            # Descarga el captcha
            img_content = httptools.downloadpage(captcha_url, headers=headers).data

            captcha_fname = os.path.join(config.get_data_path(), __channel__ + "captcha.img")
            with open(captcha_fname, 'wb') as ff:
                ff.write(img_content)

            from platformcode import captcha

            keyb = captcha.Keyboard(heading='', captcha=captcha_fname)
            keyb.doModal()
            if keyb.isConfirmed():
                captcha_text = keyb.getText()
                post_data = urllib.urlencode({'submit1': 'Invia', 'security_code': captcha_text})
                data = httptools.downloadpage(item.url, post=post_data, headers=headers).data

            try:
                os.remove(captcha_fname)
            except:
                pass

        itemlist.extend(servertools.find_video_items(data=data))

        for videoitem in itemlist:
            videoitem.title = item.title
            videoitem.fulltitle = item.fulltitle
            videoitem.thumbnail = item.thumbnail
            videoitem.show = item.show
            videoitem.plot = item.plot
            videoitem.channel = item.channel
    else:
        itemlist.append(item)

    return itemlist


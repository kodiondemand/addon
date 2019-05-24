# -*- coding: utf-8 -*-

import re
import urllib

import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import config, logger


def mainlist(item):
    logger.info()
    itemlist = []

    config.set_setting("url_error", False, "cumlouder")
    itemlist.append(item.clone(title="Últimos videos", action="videos", url="https://www.cumlouder.com/"))
    itemlist.append(item.clone(title="Categorias", action="categorias", url="https://www.cumlouder.com/categories/"))
    itemlist.append(item.clone(title="Pornstars", action="pornstars_list", url="https://www.cumlouder.com/girls/"))
    itemlist.append(item.clone(title="Listas", action="series", url="https://www.cumlouder.com/series/"))
    itemlist.append(item.clone(title="Buscar", action="search", url="https://www.cumlouder.com/search?q=%s"))

    return itemlist


def search(item, texto):
    logger.info()

    item.url = item.url % texto
    item.action = "videos"
    try:
        return videos(item)
    except:
        import traceback
        logger.error(traceback.format_exc())
        return []


def pornstars_list(item):
    logger.info()
    itemlist = []
    for letra in "abcdefghijklmnopqrstuvwxyz":
        itemlist.append(item.clone(title=letra.upper(), url=urlparse.urljoin(item.url, letra), action="pornstars"))

    return itemlist


def pornstars(item):
    logger.info()
    itemlist = []

    data = get_data(item.url)
    patron = '<a girl-url="[^"]+" class="[^"]+" href="([^"]+)" title="([^"]+)">[^<]+'
    patron += '<img class="thumb" src="([^"]+)" [^<]+<h2[^<]+<span[^<]+</span[^<]+</h2[^<]+'
    patron += '<span[^<]+<span[^<]+<span[^<]+</span>([^<]+)</span>'

    matches = re.compile(patron, re.DOTALL).findall(data)
    for url, title, thumbnail, count in matches:
        if "go.php?" in url:
            url = urllib.unquote(url.split("/go.php?u=")[1].split("&")[0])
            thumbnail = urllib.unquote(thumbnail.split("/go.php?u=")[1].split("&")[0])
        else:
            url = urlparse.urljoin(item.url, url)
            if not thumbnail.startswith("https"):
                thumbnail = "https:%s" % thumbnail
        itemlist.append(item.clone(title="%s (%s)" % (title, count), url=url, action="videos", thumbnail=thumbnail))

    # Paginador
    matches = re.compile('<li[^<]+<a href="([^"]+)" rel="nofollow">Next[^<]+</a[^<]+</li>', re.DOTALL).findall(data)
    if matches:
        if "go.php?" in matches[0]:
            url = urllib.unquote(matches[0].split("/go.php?u=")[1].split("&")[0])
        else:
            url = urlparse.urljoin(item.url, matches[0])
        itemlist.append(item.clone(title="Pagina Siguiente", url=url))

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []

    data = get_data(item.url)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<a tag-url=.*?href="([^"]+)" title="([^"]+)".*?<img class="thumb" src="([^"]+)".*?<span class="cantidad">([^<]+)</span>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for url, title, thumbnail, count in matches:
        if "go.php?" in url:
            url = urllib.unquote(url.split("/go.php?u=")[1].split("&")[0])
            thumbnail = urllib.unquote(thumbnail.split("/go.php?u=")[1].split("&")[0])
        else:
            url = urlparse.urljoin(item.url, url)
            if not thumbnail.startswith("https"):
                thumbnail = "https:%s" % thumbnail
        itemlist.append(
            item.clone(title="%s (%s videos)" % (title, count), url=url, action="videos", thumbnail=thumbnail))

    # Paginador
    matches = re.compile('<li[^<]+<a href="([^"]+)" rel="nofollow">Next[^<]+</a[^<]+</li>', re.DOTALL).findall(data)
    if matches:
        if "go.php?" in matches[0]:
            url = urllib.unquote(matches[0].split("/go.php?u=")[1].split("&")[0])
        else:
            url = urlparse.urljoin(item.url, matches[0])
        itemlist.append(item.clone(title="Pagina Siguiente", url=url))

    return itemlist

def series(item):
    logger.info()
    itemlist = []

    data = get_data(item.url)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<a onclick=.*?href="([^"]+)".*?\<img src="([^"]+)".*?h2 itemprop="name">([^<]+).*?p>([^<]+)</p>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for url, thumbnail, title, count in matches:
        itemlist.append(
            item.clone(title="%s (%s) " % (title, count), url=urlparse.urljoin(item.url, url), action="videos", thumbnail=thumbnail))

    # Paginador
    matches = re.compile('<li[^<]+<a href="([^"]+)" rel="nofollow">Next[^<]+</a[^<]+</li>', re.DOTALL).findall(data)
    if matches:
        if "go.php?" in matches[0]:
            url = urllib.unquote(matches[0].split("/go.php?u=")[1].split("&")[0])
        else:
            url = urlparse.urljoin(item.url, matches[0])
        itemlist.append(item.clone(title="Pagina Siguiente", url=url))

    return itemlist

def videos(item):
    logger.info()
    itemlist = []

    data = get_data(item.url)
    patron = '<a class="muestra-escena" href="([^"]+)" title="([^"]+)"[^<]+<img class="thumb" src="([^"]+)".*?<span class="minutos"> <span class="ico-minutos sprite"></span> ([^<]+)</span>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for url, title, thumbnail, duration in matches:
        if "go.php?" in url:
            url = urllib.unquote(url.split("/go.php?u=")[1].split("&")[0])
            thumbnail = urllib.unquote(thumbnail.split("/go.php?u=")[1].split("&")[0])
        else:
            url = urlparse.urljoin("https://www.cumlouder.com", url)
            if not thumbnail.startswith("https"):
                thumbnail = "https:%s" % thumbnail
        itemlist.append(item.clone(title="%s (%s)" % (title, duration), url=urlparse.urljoin(item.url, url),
                                   action="play", thumbnail=thumbnail, contentThumbnail=thumbnail,
                                   contentType="movie", contentTitle=title))

    # Paginador
    nextpage = scrapertools.find_single_match(data, '<ul class="paginador"(.*?)</ul>')
    matches = re.compile('<a href="([^"]+)" rel="nofollow">Next »</a>', re.DOTALL).findall(nextpage)
    if not matches:
        matches = re.compile('<li[^<]+<a href="([^"]+)">Next »</a[^<]+</li>', re.DOTALL).findall(nextpage)
    if matches:
        if "go.php?" in matches[0]:
            url = urllib.unquote(matches[0].split("/go.php?u=")[1].split("&")[0])
        else:
            url = urlparse.urljoin(item.url, matches[0])

        itemlist.append(item.clone(title="Pagina Siguiente", url=url))

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    data = get_data(item.url)
    patron = '<source src="([^"]+)" type=\'video/([^\']+)\' label=\'[^\']+\' res=\'([^\']+)\' />'
    url, type, res = re.compile(patron, re.DOTALL).findall(data)[0]
    if "go.php?" in url:
        url = urllib.unquote(url.split("/go.php?u=")[1].split("&")[0])
    elif not url.startswith("http"):
        url = "http:" + url.replace("&amp;", "&")
    itemlist.append(
        Item(channel='cumlouder', action="play", title='Video' + res, fulltitle=type.upper() + ' ' + res, url=url,
             server="directo", folder=False))

    return itemlist


def get_data(url_orig):
    try:
        if config.get_setting("url_error", "cumlouder"):
            raise Exception
        response = httptools.downloadpage(url_orig)
        if not response.data or "urlopen error [Errno 1]" in str(response.code):
            raise Exception
    except:
        config.set_setting("url_error", True, "cumlouder")
        import random
        server_random = ['nl', 'de', 'us']
        server = server_random[random.randint(0, 2)]
        url = "https://%s.hideproxy.me/includes/process.php?action=update" % server
        post = "u=%s&proxy_formdata_server=%s&allowCookies=1&encodeURL=0&encodePage=0&stripObjects=0&stripJS=0&go=" \
               % (urllib.quote(url_orig), server)
        while True:
            response = httptools.downloadpage(url, post, follow_redirects=False)
            if response.headers.get("location"):
                url = response.headers["location"]
                post = ""
            else:
                break

    return response.data

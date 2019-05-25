# -*- coding: utf-8 -*-

import re

from urlparse import urljoin

from core import httptools
from core import servertools
from platformcode import logger

HOST="http://yespornplease.com"

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(action="links",      title="Novedades",  url=HOST))
    itemlist.append(item.clone(action="categories", title="Categorías", url=urljoin(HOST, "categories")))
    itemlist.append(item.clone(action="search",     title="Buscar",     url=urljoin(HOST, "search")))
    return itemlist


def search(item, texto):
    logger.info("texto = %s" %(texto))
    item.url = urljoin(HOST, "search?q=" + texto)
    try:
        return links(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categories(item):
    logger.info()
    data = httptools.downloadpage(item.url).data
    result = []
    categories = re.findall("href=[\"'](?P<url>/search[^\"']+).*?>(?P<name>[^<>]+)</div>.*?badge[^>]+>(?P<counter>\d+)", data, re.DOTALL | re.MULTILINE)
    for url, name, counter in categories:
        result.append(item.clone(action = "links", title = "%s (%s videos)" % (name, counter), url = urljoin(item.url, url)))
    return result


def get_page(url):
    page = re.search("p=(\d+)", url)
    if page:
        return int(page.group(1))
    return 1


def get_page_url(url, page):
    logger.debug("URL: %s to page %d" % (url, page))
    resultURL = re.sub("([&\?]p=)(?:\d+)", "\g<1>%d" % page, url)
    if resultURL == url:
        resultURL += ("&" if "?" in url else "?") + "p=%d" % (page)
    logger.debug("Result: %s" % (resultURL))
    return resultURL


def links(item):
    logger.info()
    data = httptools.downloadpage(item.url).data
    reExpr = "<img\s+src=['\"](?P<img>[^'\"]+)[^>]+(?:title|alt)[^'\"]*['\"](?P<title>[^\"]+)[^>]+id[^'\"]*['\"](?P<id>[^'\"]+)[^>]*>(?:[^<]*<[^>]+>(?P<quality>[^<]+)<)?[^<]*<[^>]*duration[^>]*>(?P<duration>[^<]+)"
    reResults = re.findall(reExpr, data, re.MULTILINE | re.DOTALL)
    result = []
    for img, title, vID, quality, duration in reResults:
        formattedQuality = ""
        if quality:
            formattedQuality += " [%s]" % (quality)
        titleFormatted = "%(title)s%(quality)s [%(duration)s]" % ({"title": title, "quality": formattedQuality, "duration": duration})
        result.append(item.clone(action = "play", title = titleFormatted, url = urljoin(item.url, "/view/%s" % (vID)), thumbnail = urljoin(item.url, img), vID = vID))
    # Has pagination
    paginationOccurences = data.count('class="prevnext"')
    if paginationOccurences:
        page = get_page(item.url)
        logger.info("Page " + str(page) + " Ocurrences: " + str(paginationOccurences))
        if page > 1:
            result.append(item.clone(action = "links", title = "<< Anterior", url = get_page_url(item.url, page - 1)))
        if paginationOccurences > 1 or page == 1:
            result.append(item.clone(action = "links", title = "Siguiente >>", url = get_page_url(item.url, page + 1)))
    return result


def play(item):
    logger.info(item)
    embededURL = urljoin(item.url, "/view/%s" % (item.vID))
    itemlist = servertools.find_video_items(item.clone(url = embededURL))
    return itemlist

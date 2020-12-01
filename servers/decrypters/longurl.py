# -*- coding: utf-8 -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    #from future import standard_library
    #standard_library.install_aliases()
    import urllib.parse as urllib                               # Es muy lento en PY2.  En PY3 es nativo
else:
    import urllib                                               # Usamos el nativo de PY2 que es más rápido

import re

from core import httptools
from core import scrapertools
from platformcode import logger


def get_server_list():
    servers = []
    data = httptools.downloadpage("http://longurl.org/services").data
    data = scrapertools.unescape(data)
    data = scrapertools.find_single_match(data, '<ol>(.*?)</ol>')
    patron = '<li>(.*?)</li>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    # añadiendo algunos manualmente que no salen en la web
    servers.append("sh.st")

    for server in matches:
        servers.append(server)
    return servers


servers = get_server_list()


def get_long_urls(data):
    logger.debug()
    patron = '<a href="http://([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for short_url in matches:
        if short_url.startswith(tuple(servers)):
            logger.debug(": " + short_url)
            longurl_data = httptools.downloadpage(
                "http://api.longurl.org/v2/expand?url=" + urllib.quote_plus(short_url)).data
            logger.debug(longurl_data)
            try:
                long_url = scrapertools.scrapertools.find_single_match(longurl_data, '<long-url><!\[CDATA\[(.*?)\]\]></long-url>')
            except:
                long_url = ""
            if (long_url != ""): data = data.replace(short_url, long_url)
    return data

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

from core import scrapertools
from platformcode import logger


# Obtiene la URL que hay detrás de un enlace a linkbucks
def get_long_url(short_url):
    logger.debug("(short_url='%s')" % short_url)

    request_headers = []
    request_headers.append(["User-Agent",
                            "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; es-ES; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12"])
    request_headers.append(["Referer", "http://linkdecrypter.com"])
    post = urllib.urlencode({"pro_links": short_url, "modo_links": "text", "modo_recursivo": "on", "link_cache": "on"})
    url = "http://linkdecrypter.com/"

    # Parche porque python no parece reconocer bien la cabecera phpsessid
    body, response_headers = scrapertools.read_body_and_headers(url, post=post, headers=request_headers)
    location = ""
    n = 1
    while True:
        for name, value in response_headers:
            if name == "set-cookie":
                logger.debug("Set-Cookie: " + value)
                cookie_name = scrapertools.scrapertools.find_single_match(value, '(.*?)\=.*?\;')
                cookie_value = scrapertools.scrapertools.find_single_match(value, '.*?\=(.*?)\;')
                request_headers.append(["Cookie", cookie_name + "=" + cookie_value])

        body, response_headers = scrapertools.read_body_and_headers(url, headers=request_headers)
        logger.debug("body=" + body)

        try:
            location = scrapertools.scrapertools.find_single_match(body, '<textarea.*?class="caja_des">([^<]+)</textarea>')
            logger.debug("location=" + location)
            break
        except:
            n = n + 1
            if n > 3:
                break

    return location

# -*- coding: utf-8 -*-
# Ringraziamo errmax e dr-z3r0
import re

from core import httptools, scrapertoolsV2
from platformcode import logger
from servers.decrypters import expurl


def get_video_url(page_url, premium=False, user="", password="", video_password=""):

    encontrados = {
        'https://vcrypt.net/images/logo', 'https://vcrypt.net/css/out',
        'https://vcrypt.net/images/favicon', 'https://vcrypt.net/css/open',
        'http://linkup.pro/js/jquery', 'https://linkup.pro/js/jquery',
        'http://www.rapidcrypt.net/open'
    }
    devuelve = []

    patronvideos = [
        r'(https?://(gestyy|rapidteria|sprysphere)\.com/[a-zA-Z0-9]+)',
        r'(https?://(?:www\.)?(vcrypt|linkup)\.[^/]+/[^/]+/[a-zA-Z0-9_]+)',
        r'(https?://(?:www\.)?(bit)\.ly/[a-zA-Z0-9]+)',        
    ]

    for patron in patronvideos:
        logger.info(" find_videos #" + patron + "#")
        matches = re.compile(patron).findall(page_url)

        for url, host in matches:
            if url not in encontrados:
                logger.info("  url=" + url)
                encontrados.add(url)

                if host == 'gestyy':
                    resp = httptools.downloadpage(
                        url,
                        follow_redirects=False,
                        cookies=False,
                        only_headers=True,
                        replace_headers=True,
                        headers={'User-Agent': 'curl/7.59.0'})
                    data = resp.headers.get("location", "")
                elif 'vcrypt.net' in url:
                    from lib import unshortenit
                    data, status = unshortenit.unshorten(url)
                    logger.info("Data - Status zcrypt vcrypt.net: [%s] [%s] " %(data, status)) 
                elif 'linkup' in url or 'bit.ly' in url:
                    idata = httptools.downloadpage(url).data
                    data = scrapertoolsV2.find_single_match(idata, "<iframe[^<>]*src=\\'([^'>]*)\\'[^<>]*>")
                    #fix by greko inizio
                    if not data:  
                        data = scrapertoolsV2.find_single_match(idata, 'action="(?:[^/]+.*?/[^/]+/([a-zA-Z0-9_]+))">')
                    from lib import unshortenit
                    data, status = unshortenit.unshorten(url)
                    logger.info("Data - Status zcrypt linkup : [%s] [%s] " %(data, status))
                    if '/speedx/' in data: # aggiunto per server speedvideo
                       data = data.replace('http://linkup.pro/speedx', 'http://speedvideo.net')
                    # fix by greko fine
                else:
                    data = ""
                    while host in url:
                        resp = httptools.downloadpage(
                            url, follow_redirects=False)
                        url = resp.headers.get("location", "")
                        if not url:
                            data = resp.data
                        elif host not in url:
                            data = url
                if data:
                    devuelve.append(data)
            else:
                logger.info("  url duplicada=" + url)

    patron = r"""(https?://(?:www\.)?(?:threadsphere\.bid|adf\.ly|q\.gs|j\.gs|u\.bb|ay\.gy|linkbucks\.com|any\.gs|cash4links\.co|cash4files\.co|dyo\.gs|filesonthe\.net|goneviral\.com|megaline\.co|miniurls\.co|qqc\.co|seriousdeals\.net|theseblogs\.com|theseforums\.com|tinylinks\.co|tubeviral\.com|ultrafiles\.net|urlbeat\.net|whackyvidz\.com|yyv\.co|adfoc\.us|lnx\.lu|sh\.st|href\.li|anonymz\.com|shrink-service\.it|rapidcrypt\.net|ecleneue\.com)/[^"']+)"""#|bit\.ly)/[^"']+)"""

    logger.info(" find_videos #" + patron + "#")
    matches = re.compile(patron).findall(page_url)

    for url in matches:
        if url not in encontrados:
            logger.info("  url=" + url)
            encontrados.add(url)

            long_url = expurl.expand_url(url)
            if long_url:
                devuelve.append(long_url)
        else:
            logger.info("  url duplicada=" + url)

    ret = page_url+" "+str(devuelve) if devuelve else page_url
    logger.info(" RET=" + str(ret))
    return ret



# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)

    real_url = page_url.replace("uploaded.to", "uploaded.net")
    code = httptools.downloadpage(real_url, only_headers=True).code
    if code > 200:
        return False,"Archivo eliminado o inexistente"
    else:
        return True, ""
        
def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    video_urls = []
    if premium:
        #Si no hay almacenada una cookie activa, hacemos login
        if check_cookie("uploaded.net", "login") != True:
            
        # Login para conseguir la cookie
            logger.debug("-------------------------------------------")
            logger.debug("login")
            logger.debug("-------------------------------------------")
            login_url = "http://uploaded.net/io/login"
            post = "id=" + user + "&pw=" + password
            setcookie = httptools.downloadpage(login_url, post=post, follow_redirects=False,
                                           only_headers=True).headers.get("set-cookie", "")

        logger.debug("-------------------------------------------")
        logger.debug("obtiene la url")
        logger.debug("-------------------------------------------")

        location = httptools.downloadpage(page_url, follow_redirects=False, only_headers=True).headers.get("location",
                                                                                                           "")
        logger.debug("location=" + location)
        
        #fix descarga no directa
        if location == "":
            data = httptools.downloadpage(page_url).data
            #logger.debug("data: %s" % data)
            if "<h1>Premium Download</h1>" in data:
                location = scrapertools.find_single_match(data, '<form method="post" action="([^"]+)"')
                #logger.debug("location: %s" % location)
            elif "Hybrid-Traffic is completely exhausted" in data:
                logger.error("Trafico agotado")
            
            elif "<h1>Free Download</h1>" in data:
                logger.error("Cuenta Free")
            else:
                logger.error("Error Desconocido")
        logger.debug("-------------------------------------------")
        logger.debug("obtiene el nombre del fichero")
        logger.debug("-------------------------------------------")
        try:
            content_disposition = httptools.downloadpage(location, post="", follow_redirects=False,
                                                         only_headers=True).headers.get("content-disposition", "")
            logger.debug("content_disposition=" + content_disposition)
            if content_disposition != "":
                filename = scrapertools.find_single_match(content_disposition, 'filename="([^"]+)"')
                extension = filename[-4:]
            else:
                extension = ""

        except:
            import traceback
            logger.error(traceback.format_exc())
            extension = ""

        video_urls.append([extension + " (Premium) [uploaded.to]", location])

    for video_url in video_urls:
        logger.debug("%s - %s" % (video_url[0], video_url[1]))

    return video_urls

def check_cookie(domain, cname):
    from platformcode import config
    #cargamos las cookies
    cookies = config.get_cookie_data()
    #buscamos el valor de la cookie "cname" del dominio "domain"
    cookie_value = scrapertools.find_single_match(cookies, domain + ".*?" + cname + "\s+([A-Za-z0-9\+\=\%\_]+)")
    if cookie_value:
        if len(cookie_value) > 6:
            return True
        else:
            return False
    else:
        return False

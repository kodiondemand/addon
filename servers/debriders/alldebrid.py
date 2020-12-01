# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from platformcode import logger


# Returns an array of possible video url's from the page_url
def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug()
    page_url = correct_url(page_url)
    dd1 = httptools.downloadpage("https://api.alldebrid.com/user/login?agent=mySoft&username=%s&password=%s" %(user, password)).data
    token = scrapertools.find_single_match(dd1, 'token":"([^"]+)')
    dd2 = httptools.downloadpage("https://api.alldebrid.com/link/unlock?agent=mySoft&token=%s&link=%s" %(token, page_url)).data
    link = scrapertools.find_single_match(dd2, 'link":"([^"]+)')
    link = link.replace("\\","")
    video_urls = []
    if link:
        extension = "mp4 [alldebrid]"
        video_urls.append([extension, link])
    else:
        try:
            server_error = "Alldebrid: " + data["error"].decode("utf-8", "ignore")
            server_error = server_error.replace("This link isn't available on the hoster website.",
                                                "Enlace no disponible en el servidor de descarga") \
                .replace("Hoster unsupported or under maintenance.",
                         "Servidor no soportado o en mantenimiento")
        except:
            server_error = "Alldebrid: Error en el usuario/password o en la web"
        video_urls.append([server_error, ''])
    return video_urls


def correct_url(url):
    if "userporn.com" in url:
        url = url.replace("/e/", "/video/")
    if "putlocker" in url:
        url = url.replace("/embed/", "/file/")
    return url

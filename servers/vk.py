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

from core import httptools
from core import scrapertools
from platformcode import config, logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    if not login():
        return False, "Falta Ingresar/Actualizar las credenciales en el servidor vk. Configuracion - Preferencias - Ajustes de servidores - Configuración del servidor vk"
    data = httptools.downloadpage(page_url).data
    if "This video has been removed from public access" in data or "Video not found." in data:
        return False, "El archivo ya no esta disponible<br/>en VK (ha sido borrado)"
    return True, ""


# Returns an array of possible video url's from the page_url
def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    matches = scrapertools.find_multiple_matches(data, '<source src="([^"]+)" type="video/(\w+)')
    for media_url, ext in matches:
        calidad = scrapertools.find_single_match(media_url, '(\d+)\.%s' % ext)
        video_urls.append([calidad + "p ." + ext + " [vk]", media_url])
    video_urls.sort(key=lambda it: int(it[0].split("p ", 1)[0]))
    for video_url in video_urls:
        logger.debug("%s - %s" % (video_url[0], video_url[1]))
    return video_urls


def login():
    data = httptools.downloadpage("https://vk.com").data
    if "data-href" in data:
        return True
    ip_h = scrapertools.find_single_match(data, 'ip_h=(\w+)')
    lg_h = scrapertools.find_single_match(data, 'lg_h=(\w+)')
    vkemail = config.get_setting("vkemail",server="vk")
    vkpassword = config.get_setting("vkpassword",server="vk")
    post = {"act":"login","role":"al_frame","expire":"","recaptcha":"","captcha_sid":"","captcha_key":"","_origin":"https://vk.com","email":vkemail,"pass":vkpassword, "ip_h":ip_h, "lg_h":lg_h}
    url = "https://login.vk.com/?act=login"
    url = httptools.downloadpage(url, follow_redirects=False, only_headers=True, post=urllib.urlencode(post)).headers.get("location", "")
    data = httptools.downloadpage(url).data
    if "name: " not in data:
        return False
    return True

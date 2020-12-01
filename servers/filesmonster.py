# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from platformcode import logger


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("( page_url='%s')")
    video_urls = []
    itemlist = []
    data1 = ''
    data2 = ''
    url = ''
    alerta = '[filesmonster premium]'
    enlace = "no"
    post2 = "username=" + user + "&password=" + password
    login_url = "http://filesmonster.com/api/public/login"
    data1 = httptools.downloadpage(login_url, post=post2).data
    partes1 = data1.split('"')
    estado = partes1[3]
    if estado != 'success': alerta = "[error de filesmonster premium]: " + estado

    id = page_url
    id = id.replace("http://filesmonster.com/download.php", "")
    post = id.replace("?", "")
    url = 'http://filesmonster.com/api/public/premiumDownload'
    data2 = httptools.downloadpage(url, post=post).data

    partes = data2.split('"')

    url = partes[7]
    filename = scrapertools.get_filename_from_url(url)[-4:]
    alerta = filename + " " + alerta
    if "http" not in url: alerta = "[error de filesmonster premium]: " + url

    video_urls.append([alerta, url])

    return video_urls

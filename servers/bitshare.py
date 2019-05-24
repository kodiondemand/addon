# -*- coding: utf-8 -*-

from core import httptools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "Error - Archivo no disponible" in data or "Por favor seleccione el archivo a cargar" in data:
        return False, "Archivo no encontrado"
    patron = '<b>()'
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    return video_urls

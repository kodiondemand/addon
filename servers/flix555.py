# -*- coding: utf-8 -*-

import time
import urllib

from core import httptools, scrapertools
from lib import jsunpack
from platformcode import logger, platformtools


def test_video_exists(page_url):
    resp = httptools.downloadpage(page_url)
    if resp.code == 404 or '<b>File Not Found</b>' in resp.data:
        return False, "[flix555] El video no está disponible"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(page_url).data
    # ~ logger.info(data)

    post = {}
    inputs = scrapertools.find_multiple_matches(data, '<input type="(?:hidden|submit)" name="([^"]*)" value="([^"]*)"')
    for nom, valor in inputs: post[nom] = valor
    post = urllib.urlencode(post)
    # ~ logger.info(post)

    espera = scrapertools.find_single_match(data, '<span id="cxc">(\d+)</span>')
    platformtools.dialog_notification('Cargando flix555', 'Espera de %s segundos requerida' % espera)
    time.sleep(int(espera))

    data = httptools.downloadpage(page_url, post=post).data
    # ~ logger.info(data)

    packed = scrapertools.find_single_match(data, "<script type=[\"']text/javascript[\"']>(eval.*?)</script>")
    unpacked = jsunpack.unpack(packed)
    # ~ logger.info(unpacked)

    matches = scrapertools.find_multiple_matches(unpacked, 'file\s*:\s*"([^"]*)"\s*,\s*label\s*:\s*"([^"]*)"')
    if matches:
        for url, lbl in matches:
            if not url.endswith('.srt'):
                itemlist.append(['[%s]' % lbl, url])

    return itemlist


# Conector vidcloud By Alfa development Group
# --------------------------------------------------------

import re

from core import httptools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url)
    if data.code == 404:
        return False, "[Cloud] El archivo no existe o  ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    data = data.replace('\\\\', '\\').replace('\\','')
    patron = '"file":"([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for url in matches:
        if not ".vtt" in url:
            video_urls.append(['vidcloud', url])
    return video_urls

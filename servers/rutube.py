# -*- coding: utf-8 -*-
# -*- Server Rutube -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re

from core import httptools
from core import jsontools
from platformcode import logger


def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = get_source(page_url)

    if "File was deleted" in data or "File Not Found" in data:
        return False, "[Rutube] El video ha sido borrado"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    import urllib
    video_urls = []
    referer = ''
    id = ''
    if "|" in page_url:
        page_url = page_url.replace('?', '|')
        page_url, id, referer = page_url.split("|", 2)
        header = {'referer':referer}
        referer = urllib.urlencode(header)
    "http://rutube.ru/api/play/options/10531822/?format=json&sqr4374_compat=1&no_404=true&referer=http%3A%2F%2Frutube.ru%2Fplay%2Fembed%2F10531822%3Fp%3DeDk8m91H0UBPOCUuFicFbQ&p=eDk8m91H0UBPOCUuFicFbQ"
    base_link = page_url.replace("/play/embed/", "/api/play/options/")
    new_link = base_link + '/?format=json&sqr4374_compat=1&no_404=true&%s&%s' % (referer, id)
    data = httptools.downloadpage(new_link).data
    json_data = jsontools.load(data)
    video_urls.append(['Rutube', json_data['video_balancer']['m3u8']])
    return video_urls

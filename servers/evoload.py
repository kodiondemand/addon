# -*- coding: utf-8 -*-
# --------------------------------------------------------

# Conector EvoLoad By 4l3x87
# --------------------------------------------------------
from core import httptools, jsontools
from core import scrapertools
from platformcode import config
from platformcode import logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    global json
    json = get_json(page_url)
    if not json or ('xstatus' in json and json['xstatus'] == 'del'):
        return False,  config.get_localized_string(70449) % "EvoLoad"
    return True, ""


def get_json(page_url):
    csrv_pass = '7dczpuzsmak'
    code = page_url[-14:]
    csrv_token = httptools.downloadpage('https://csrv.evosrv.com/captcha?m412548', headers={"Referer": page_url}).data
    post = 'code=' + code + '&token=&csrv_token=' + csrv_token + '&pass=' + csrv_pass + '&reff=' + page_url
    logger.debug("post=" + post)
    response = httptools.downloadpage("https://evoload.io/SecurePlayer", post=post, headers=[])
    data = jsontools.load(response.data)
    if data:
        return data
    return False


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    global json
    video_urls = []

    if json:
        label = json.get('name', '').split('/')[-1]
        url = json.get('stream', {}).get('src', '')
        if url:
            video_urls.append(['%s [evoload]' % label, url])
    return video_urls

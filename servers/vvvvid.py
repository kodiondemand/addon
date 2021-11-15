# -*- coding: utf-8 -*-
import functools
import re

import requests

from core import httptools
from lib import vvvvid_decoder
from platformcode import logger, config

# Creating persistent session
current_session = requests.Session()
current_session.request = functools.partial(current_session.request, timeout=httptools.HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT)
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.82 Safari/537.36'}

# Getting conn_id token from vvvvid and creating payload
login_page = 'https://www.vvvvid.it/user/login'
try:
    res = current_session.get(login_page, headers=headers)
    conn_id = res.json()['data']['conn_id']
    payload = {'conn_id': conn_id}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14', 'Cookie': res.headers['set-cookie']}
except:
    conn_id = ''



def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "Not Found" in data or "File was deleted" in data:
        return False, config.get_localized_string(70449) % "VVVVID"
    else:
        page_url = page_url.replace("/show/","/#!show/")
        show_id = re.findall("#!show/([0-9]+)/", page_url)[0]
        name = re.findall(show_id + "/(.+?)/", page_url)
        if not name: return False, config.get_localized_string(70449) % "VVVVID"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    video_urls = []

    page_url = page_url.replace("/show/","/#!show/")

    # Getting info from given URL
    show_id = re.findall("#!show/([0-9]+)/", page_url)[0]
    name = re.findall(show_id + "/(.+?)/", page_url)[0]
    season_id = re.findall(name + "/(.+?)/", page_url)[0]
    video_id = re.findall(season_id + "/(.+?)/", page_url)[0]

    # Getting info from Site
    json_url = "https://www.vvvvid.it/vvvvid/ondemand/" + show_id + '/season/' +season_id + '/'
    json_file = current_session.get(json_url, headers=headers, params=payload).json()
    logger.debug(json_file['data'])

    # Search for the correct episode
    for episode in json_file['data']:
        if episode['video_id'] == int(video_id):
            ep_title = '[B]' + episode['title'] + '[/B]'
            embed_info = vvvvid_decoder.dec_ei(episode['embed_info'])
            embed_info = embed_info.replace('manifest.f4m','master.m3u8').replace('http://','https://').replace('/z/','/i/')
            key_url = 'https://www.vvvvid.it/kenc?action=kt&conn_id=' + conn_id + '&url=' + embed_info.replace(':','%3A').replace('/','%2F')
            key = vvvvid_decoder.dec_ei(current_session.get(key_url, headers=headers, params=payload).json()['message'])

    video_urls.append([ep_title, str(embed_info) + '?' + key])

    return video_urls
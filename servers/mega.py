# -*- coding: utf-8 -*-
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import json
import random
from core import httptools
from core import scrapertools
from platformcode import platformtools, logger

files = None

def test_video_exists(page_url):
    # from core .support import dbg;dbg()
    types= "File"
    msg = "The link has a problem."
    id_video = None
    get = ""
    seqno = random.randint(0, 0xFFFFFFFF)
    url = page_url.split("#")[1]
    f_id = url.split("!")[1]
    id_video = None
    if "|" in url:
        url, id_video = url.split("|")
    post = {'a': 'g', 'g': 1, 'p': f_id}
    isfolder = False
    if "/#F!" in page_url:
        get = "&n=" + f_id
        post = {"a":"f","c":1,"r":0}
        isfolder = True
        types= "Folder"
        if id_video:
            #Aqui ya para hacer un check se complica, no hay una manera directa aún teniendo la id del video dentro de la carpeta
            return True, ""

    codes = {-1: 'An internal error has occurred in Mega.nz',
             -2: 'Error in the request made, Cod -2',
             -3: 'A temporary jam or malfunction in the Mega server prevents your link from being processed',
             -4: 'You have exceeded the allowed transfer fee. Try it again later',
             -6: types + ' not find deleted account',
             -9: types + ' not find',
             -11: 'Restricted access',
             -13: 'You are trying to access an incomplete file',
             -14: 'Decryption operation failed',
             -15: 'User session expired or invalid, log in again',
             -16: types + ' not available, the uploader account was banned',
             -17: 'The request exceeds your allowable transfer fee',
             -18: types + ' temporarily unavailable, please try again later'
    }
    api = 'https://g.api.mega.co.nz/cs?id={}{}'.format(seqno, get)
    req_api = httptools.downloadpage(api, post=json.dumps([post])).json
    if isfolder:
        req_api = req_api
    else:
        try:
            req_api = req_api[0]
        except:
            req_api = req_api
    logger.error(req_api)
    if isinstance(req_api, (int, long)):
        if req_api in codes:
            msg = codes[req_api]
        return False, msg
    else:
        #Comprobación limite cuota restante
        from lib.megaserver import Client
        global c
        c = Client(url=page_url, is_playing_fnc=platformtools.is_playing)
        global files
        files = c.get_files()
        if files == 509:
            msg1 = "The video exceeds the daily viewing limit."
            return False, msg1
        elif isinstance(files, (int, long)):
            return False, "Error code %s" % str(files)

        return True, ""

def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    page_url = page_url.replace('/embed#', '/#')
    logger.debug("(page_url='%s')" % page_url)
    video_urls = []

    # If there are more than 5 files create a playlist with all
    # This function (the playlist) does not go, you have to browse megaserver / handler.py although the call is in client.py
    if len(files) > 5:
        media_url = c.get_play_list()
        video_urls.append([scrapertools.get_filename_from_url(media_url)[-4:] + " [mega]", media_url])
    else:
        for f in files:
            media_url = f["url"]
            video_urls.append([scrapertools.get_filename_from_url(media_url)[-4:] + " [mega]", media_url])

    return video_urls

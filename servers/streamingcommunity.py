# -*- coding: utf-8 -*-
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import json
import random
from core import httptools
from core import scrapertools
from platformcode import platformtools, logger
from lib.streamingcommunity import Client as SCClient
from lib.streamingcommunity import File as SCFile

files = None

def test_video_exists(video_id):

    # page_url is the {VIDEO_ID}. Es: 5957

    global c
    c = Client(video_id=video_id, is_playing_fnc=platformtools.is_playing)

    return True, ""

def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    page_url = page_url.replace('/embed#', '/#')
    logger.debug("(page_url='%s')" % page_url)
    video_urls = []

    # If there are more than 5 files create a playlist with all
    # This function (the playlist) does not go, you have to browse megaserver / handler.py although the call is in client.py
    media_url = c.get_manifest_url()

    video_urls.append([scrapertools.get_filename_from_url(media_url)[-4:] + " [mega]", media_url])

    return video_urls

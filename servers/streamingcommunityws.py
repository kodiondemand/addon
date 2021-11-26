# -*- coding: utf-8 -*-
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import json
import random
from core import httptools, support, scrapertools
from platformcode import platformtools, logger
from lib.streamingcommunity import Client as SCClient

files = None

def test_video_exists(page_url):

    # page_url is the {VIDEO_ID}. Es: 5957
    return True, ""

def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):

    videoUrls = []

    global c
    c = SCClient("",video_id=page_url, isPlaying_fnc=platformtools.isPlaying)

    media_url = c.get_manifest_url()

    videoUrls.append({'type':scrapertools.get_filename_from_url(media_url).split('.')[-1] , 'url':media_url})

    return videoUrls

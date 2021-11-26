# -*- coding: utf-8 -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    #from future import standard_library
    #standard_library.install_aliases()
    import urllib.parse as urllib                               # Es muy lento en PY2.  En PY3 es nativo
else:
    import urllib                                               # Usamos el nativo de PY2 que es más rápido

import re

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    post = {}
    r = re.findall(r'type="hidden" name="(.+?)"\s* value="?(.+?)">', data)
    for name, value in r:
        post[name] = value
        post.update({'method_free': 'Free Download'})
    data = httptools.downloadpage(page_url, post=urllib.urlencode(post)).data
    # Get link
    sPattern = '''<div id="player_code">.*?<script type='text/javascript'>(eval.+?)</script>'''
    r = re.findall(sPattern, data, re.DOTALL | re.I)
    mediaUrl = ""
    if r:
        sUnpacked = jsunpack.unpack(r[0])
        sUnpacked = sUnpacked.replace("\\'", "")
        r = re.findall('file,(.+?)\)\;s1', sUnpacked)
        if not r:
            r = re.findall('"src"value="(.+?)"/><embed', sUnpacked)

        mediaUrl = r[0]

    videoUrls = []
    videoUrls.append({'type':scrapertools.get_filename_from_url(mediaUrl).split('.')[-1], 'url':mediaUrl})

    # for videoUrl in videoUrls:
    #     logger.debug("%s - %s" % (videoUrl[0], videoUrl[1]))

    return videoUrls

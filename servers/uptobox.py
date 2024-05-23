# -*- coding: utf-8 -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3: import urllib.parse as urllib
else: import urllib

from core import httptools
from core import scrapertools
from platformcode import logger
from core.support import match


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    data = httptools.downloadpage(page_url).data

    if "Streaming link:" in data:
        return True, ""
    elif "Unfortunately, the file you want is not available." in data or "Unfortunately, the video you want to see is not available" in data or "This stream doesn" in data or "Page not found" in data or "Archivo no encontrado" in data:
        return False, config.get_localized_string(70449) % "UPtoStream"
    wait = scrapertools.find_single_match(data, "You have to wait ([0-9]+) (minute|second)")
    if len(wait) > 0:
        return False, "[UPtoStream] Limite di download raggiunto. <br/> Attendi " + wait[0] + " " + wait[1]

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    global data
    # If the link is direct from upstream
    if "uptobox" not in page_url:
        if "Video not found" in data:
            page_url = page_url.replace("uptostream.com/iframe/", "uptobox.com/")
            video_urls = uptobox(page_url, httptools.downloadpage(page_url).data)
        else:
            video_urls = uptostream(data)
    else:
        # If the file has a streaming link, it is redirected to upstream
        if "Streaming link:" in data:
            page_url = "http://uptostream.com/iframe/" + scrapertools.find_single_match(page_url, 'uptobox.com/([a-z0-9]+)')
            video_urls = uptostream(httptools.downloadpage(page_url).data)
        else:
            # If you don't have it, the normal download is used
            video_urls = uptobox(page_url, data)
    return video_urls


def uptostream(data):
    video_id = match(data, patron=r"var videoId\s*=\s*'([^']+)").match
    subtitle = match(data, patron=r'kind="subtitles" src="([^"]+)"').match
    if subtitle and not '://' in subtitle:
        subtitle = "http://" + subtitle
    video_urls = []
    api_url = "https://uptostream.com/api/streaming/source/get?token=null&file_code=%s" % video_id
    api_data = httptools.downloadpage(api_url).json
    js_code = api_data.get('data', '').get('sources', '')

    from lib import js2py

    context = js2py.EvalJs({'atob': atob})
    context.execute(js_code)
    result = context.sources

    for x in result:
        media_url = x.get('src', '')
        tipo = x.get('type', '')
        res = x.get('label', '')
        lang = x.get('lang', '')
        tipo = tipo.replace("video/","")
        if lang: extension = "{} - {} [{}]".format(tipo, res, lang.upper())
        else: extension = "{} - {}".format(tipo, res)
        video_urls.append([extension + " [UPtoStream]", media_url, 0, subtitle])
        video_urls.sort(key=lambda url: int(match(url[0], patron=r'(\d+)p').match))
    return video_urls

def atob(s):
    import base64
    return base64.b64decode('{}'.format(s)).decode('utf-8')

def uptobox(url, data):
    video_urls = []
    post = ""

    matches = match(data, patron=r'name="([^"]+)".*?value="([^"]*)"').matches
    for inputname, inputvalue in matches:
        post += inputname + "=" + inputvalue + "&"

    media = match(url, post=post[:-1], patron=r'<a href="([^"]+)">\s*<span class="button_upload green">').match
    url_strip = media.rsplit('/', 1)[1]
    media_url = media.rsplit('/', 1)[0] + "/" + url_strip
    video_urls.append([media_url[-4:] + " [UPtoStream]", media_url])

    return video_urls
# -*- coding: utf-8 -*-
import sys

from platformcode import config

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    #from future import standard_library
    #standard_library.install_aliases()
    import urllib.parse as urllib                               # Es muy lento en PY2.  En PY3 es nativo
else:
    import urllib                                               # Usamos el nativo de PY2 que es más rápido

from core import httptools
from core import scrapertools
from platformcode import logger

token = ""
excption = False


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)

    data = get_data(page_url.replace(".org", ".me"))
    if "File Not Found" in data: return False,  config.get_localized_string(70449) % "Clicknupload"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)

    data = get_data(page_url.replace(".org", ".me"))

    post = ""
    block = scrapertools.find_single_match(data, '(?i)<Form method="POST"(.*?)</Form>')
    matches = scrapertools.find_multiple_matches(block, 'input.*?name="([^"]+)".*?value="([^"]*)"')
    for inputname, inputvalue in matches:
        post += inputname + "=" + inputvalue + "&"
    post = post.replace("download1", "download2")

    data = get_data(page_url, post)

    video_urls = []
    media = scrapertools.find_single_match(data, "onClick=\"window.open\('([^']+)'")
    # Solo es necesario codificar la ultima parte de la url
    url_strip = urllib.quote(media.rsplit('/', 1)[1])
    media_url = media.rsplit('/', 1)[0] + "/" + url_strip
    video_urls.append([scrapertools.get_filename_from_url(media_url)[-4:] + " [clicknupload]", media_url])
    for video_url in video_urls:
        logger.debug("%s - %s" % (video_url[0], video_url[1]))

    return video_urls


def get_data(url_orig, req_post=""):
    try:
        if not excption:
            response = httptools.downloadpage(url_orig, post=req_post)
            if not response.data or "urlopen error [Errno 1]" in str(response.code):
                global excption
                excption = True
                raise Exception
            return response.data
        else:
            raise Exception
    except:
        post = {"address": url_orig.replace(".me", ".org")}
        if req_post:
            post["options"] = [{"man": "--data", "attribute": req_post}]
        else:
            post["options"] = []
        from core import jsontools
        global token
        if not token:
            data = httptools.downloadpage("http://onlinecurl.com/").data
            token = scrapertools.find_single_match(data, '<meta name="csrf-token" content="([^"]+)"')

        headers = {'X-Requested-With': 'XMLHttpRequest', 'X-CSRF-Token': token, 'Referer': 'http://onlinecurl.com/'}
        post = "curl_request=" + urllib.quote(jsontools.dump(post)) + "&email="
        response = httptools.downloadpage("http://onlinecurl.com/onlinecurl", post=post, headers=headers).data
        data = jsontools.load(response).get("body", "")

        return data

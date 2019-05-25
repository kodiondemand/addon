# s-*- coding: utf-8 -*-

import re
import urllib

import urlparse

from core import httptools
from core import jsontools as json
from core import scrapertools
from platformcode import config, logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url).data

    if "File was deleted" in data:
        return False, config.get_localized_string(70449) % "Youtube"

    return True, ""



def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)

    if not page_url.startswith("http"):
        page_url = "http://www.youtube.com/watch?v=%s" % page_url
        logger.info(" page_url->'%s'" % page_url)

    video_id = scrapertools.find_single_match(page_url, '(?:v=|embed/)([A-z0-9_-]{11})')
    video_urls = extract_videos(video_id)
    video_urls.reverse()

    for video_url in video_urls:
        logger.info(str(video_url))

    return video_urls


def remove_additional_ending_delimiter(data):
    pos = data.find("};")
    if pos != -1:
        data = data[:pos + 1]
    return data


def normalize_url(url):
    if url[0:2] == "//":
        url = "http:" + url
    return url


def extract_flashvars(data):
    assets = 0
    flashvars = {}
    found = False

    for line in data.split("\n"):
        if line.strip().find(";ytplayer.config = ") > 0:
            found = True
            p1 = line.find(";ytplayer.config = ") + len(";ytplayer.config = ") - 1
            p2 = line.rfind(";")
            if p1 <= 0 or p2 <= 0:
                continue
            data = line[p1 + 1:p2]
            break
    data = remove_additional_ending_delimiter(data)

    if found:
        data = json.load(data)
        if assets:
            flashvars = data["assets"]
        else:
            flashvars = data["args"]

    for k in ["html", "css", "js"]:
        if k in flashvars:
            flashvars[k] = normalize_url(flashvars[k])

    return flashvars


def extract_videos(video_id):
    fmt_value = {
        5: "240p h263 flv",
        6: "240p h263 flv",
        18: "360p h264 mp4",
        22: "720p h264 mp4",
        26: "???",
        33: "???",
        34: "360p h264 flv",
        35: "480p h264 flv",
        36: "3gpp",
        37: "1080p h264 mp4",
        38: "4K h264 mp4",
        43: "360p vp8 webm",
        44: "480p vp8 webm",
        45: "720p vp8 webm",
        46: "1080p vp8 webm",
        59: "480p h264 mp4",
        78: "480p h264 mp4",
        82: "360p h264 3D",
        83: "480p h264 3D",
        84: "720p h264 3D",
        85: "1080p h264 3D",
        100: "360p vp8 3D",
        101: "480p vp8 3D",
        102: "720p vp8 3D"
    }

    url = 'http://www.youtube.com/get_video_info?video_id=%s&eurl=https://youtube.googleapis.com/v/%s&ssl_stream=1' % \
          (video_id, video_id)
    data = httptools.downloadpage(url).data

    video_urls = []
    params = dict(urlparse.parse_qsl(data))
    if params.get('hlsvp'):
        video_urls.append(["(LIVE .m3u8) [youtube]", params['hlsvp']])
        return video_urls

    if config.is_xbmc():
        import xbmc
        xbmc_version = config.get_platform(True)['num_version']
        if xbmc_version >= 17 and xbmc.getCondVisibility('System.HasAddon(inputstream.adaptive)') \
                and params.get('dashmpd'):
            if params.get('use_cipher_signature', '') != 'True':
                video_urls.append(['mpd  HD [youtube]', params['dashmpd'], 0, '', True])

    js_signature = ""
    youtube_page_data = httptools.downloadpage("http://www.youtube.com/watch?v=%s" % video_id).data
    params = extract_flashvars(youtube_page_data)
    if params.get('url_encoded_fmt_stream_map'):
        data_flashvars = params["url_encoded_fmt_stream_map"].split(",")
        for url_desc in data_flashvars:
            url_desc_map = dict(urlparse.parse_qsl(url_desc))
            if not url_desc_map.get("url") and not url_desc_map.get("stream"):
                continue

            try:
                key = int(url_desc_map["itag"])
                if not fmt_value.get(key):
                    continue

                if url_desc_map.get("url"):
                    url = urllib.unquote(url_desc_map["url"])
                elif url_desc_map.get("conn") and url_desc_map.get("stream"):
                    url = urllib.unquote(url_desc_map["conn"])
                    if url.rfind("/") < len(url) - 1:
                        url += "/"
                    url += urllib.unquote(url_desc_map["stream"])
                elif url_desc_map.get("stream") and not url_desc_map.get("conn"):
                    url = urllib.unquote(url_desc_map["stream"])

                if url_desc_map.get("sig"):
                    url += "&signature=" + url_desc_map["sig"]
                elif url_desc_map.get("s"):
                    sig = url_desc_map["s"]
                    if not js_signature:
                        urljs = scrapertools.find_single_match(youtube_page_data, '"assets":.*?"js":\s*"([^"]+)"')
                        urljs = urljs.replace("\\", "")
                        if urljs:
                            if not re.search(r'https?://', urljs):
                                urljs = urlparse.urljoin("https://www.youtube.com", urljs)
                            data_js = httptools.downloadpage(urljs).data
                            from jsinterpreter import JSInterpreter
                            funcname = scrapertools.find_single_match(data_js, '\.sig\|\|([A-z0-9$]+)\(')
                            if not funcname:
                                funcname = scrapertools.find_single_match(data_js, '["\']signature["\']\s*,\s*'
                                                                                   '([A-z0-9$]+)\(')
                            jsi = JSInterpreter(data_js)
                            js_signature = jsi.extract_function(funcname)

                    signature = js_signature([sig])
                    url += "&signature=" + signature
                url = url.replace(",", "%2C")
                video_urls.append(["(" + fmt_value[key] + ") [youtube]", url])
            except:
                import traceback
                logger.info(traceback.format_exc())

    return video_urls

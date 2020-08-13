# s-*- coding: utf-8 -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    #from future import standard_library
    #standard_library.install_aliases()
    import urllib.parse as urllib                               # Es muy lento en PY2.  En PY3 es nativo
    import urllib.parse as urlparse
else:
    import urllib                                               # Usamos el nativo de PY2 que es más rápido
    import urlparse

import re

from core import httptools
from core import jsontools as json
from core import scrapertools
from platformcode import config, logger


itag_list = {1: "video",
             5: "flv 240p",
             6: "flv 270p",
             17: "3gp 144p",
             18: "mp4 360p",
             22: "mp4 720p",
             34: "flv 360p",
             35: "flv 480p",
             36: "3gp 180p",
             37: "mp4 1080p",
             38: "mp4 3072p",
             43: "webm 360p",
             44: "webm 480p",
             45: "webm 720p",
             46: "webm 1080p",
             82: "mp4 360p 3D",
             83: "mp4 480p 3D",
             84: "mp4 720p 3D",
             85: "mp4 1080p 3D",
             92: "hls 240p 3D",
             93: "hls 360p 3D",
             94: "hls 480p 3D",
             95: "hls 720p 3D",
             96: "hls 1080p",
             100: "webm 360p 3D",
             101: "webm 480p 3D",
             102: "webm 720p 3D",
             132: "hls 240p",
             133: "mp4 240p",
             134: "mp4 360p",
             135: "mp4 480p",
             136: "mp4 720p",
             137: "mp4 1080p",
             138: "mp4 2160p",
             160: "mp4 144p",
             167: "webm 360p",
             168: "webm 480p",
             169: "webm 1080p",
             219: "webm 144p",
             242: "webm 240p",
             243: "webm 360p",
             244: "webm 480p",
             245: "webm 480p",
             246: "webm 480p",
             247: "webm 720p",
             248: "webm 1080p",
             266: "mp4 2160p",
             271: "webm 1440p",
             272: "webm 4320p",
             278: "webm 144p",
             298: "mp4 720p",
             299: "mp4 1080p",
             302: "webm 720p",
             303: "webm 1080p",
             308: "webm 1440p",
             313: "webm 2160p",
             315: "webm 2160p",
             330: "webm 144p hdr",
             331: "webm 240p hdr",
             332: "webm 360p hdr",
             333: "webm 480p hdr",
             334: "webm 720p hdr",
             335: "webm 1080p hdr",
             336: "webm 1440p hdr"}


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url).data

    if "File was deleted" in data or "Video non disponibile" in data:
        return False, config.get_localized_string(70449) % "Youtube"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)

    if not page_url.startswith("http"):
        page_url = "http://www.youtube.com/watch?v=%s" % page_url
        logger.info(" page_url->'%s'" % page_url)

    video_id = scrapertools.find_single_match(page_url, '(?:v=|embed/)([A-z0-9_-]{11})')
    video_urls = extract_videos(video_id)

    return sorted(video_urls, reverse=True)


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


def get_signature(youtube_page_data):

    from lib.jsinterpreter import JSInterpreter

    urljs = scrapertools.find_single_match(youtube_page_data, '"assets":.*?"js":\s*"([^"]+)"')
    urljs = urljs.replace("\\", "")
    if urljs:
        if not re.search(r'https?://', urljs):
            urljs = urlparse.urljoin("https://www.youtube.com", urljs)
        data_js = httptools.downloadpage(urljs).data

    pattern = r'(?P<fname>\w+)=function\(\w+\){(\w)=\2\.split\(""\);.*?return\s+\2\.join\(""\)}'

    funcname = re.search(pattern, data_js).group('fname')

    jsi = JSInterpreter(data_js)
    js_signature = jsi.extract_function(funcname)

    return js_signature


def extract_videos(video_id):


    url = 'https://www.youtube.com/get_video_info?video_id=%s&eurl=https://youtube.googleapis.com/v/%s&ssl_stream=1' % \
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

    youtube_page_data = httptools.downloadpage("https://www.youtube.com/watch?v=%s" % video_id).data

    params = extract_flashvars(youtube_page_data)

    if params.get('player_response'):
        params = json.load(params.get('player_response'))
        data_flashvars = params["streamingData"]
        for s_data in data_flashvars:
            if s_data in ["adaptiveFormats", "formats"]:
                for opt in data_flashvars[s_data]:
                    opt = dict(opt)
                    if "audioQuality" not in opt:
                        continue
                    if "signatureCipher" in opt and opt['mimeType'].startswith('video'):
                        signature = get_signature(youtube_page_data)
                        cipher = dict(urlparse.parse_qsl(urllib.unquote(opt["signatureCipher"])))
                        url = re.search('url=(.*)', opt["signatureCipher"]).group(1)
                        s = cipher.get('s')
                        url = "%s&sig=%s" % (urllib.unquote(url), signature([s]))
                        video_urls.append(["%s" % itag_list.get(opt["itag"], "video"), url])
                    elif opt["itag"] in itag_list:
                        video_urls.append(["%s" % itag_list.get(opt["itag"], "video"), opt["url"]])

    return video_urls
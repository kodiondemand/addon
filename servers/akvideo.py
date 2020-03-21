# -*- coding: utf-8 -*-
# by DrZ3r0

import urllib, re

from core import httptools
from core import scrapertools
from platformcode import logger, config, platformtools


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    # page_url = re.sub('akvideo.stream/(?:video/|video\\.php\\?file_code=)?(?:embed-)?([a-zA-Z0-9]+)','akvideo.stream/video/\\1',page_url)
    global data
    page = httptools.downloadpage(page_url)
    if 'embed_ak.php' in page_url or '/embed-' in page.url:
        code = scrapertools.find_single_match(page.url, '/embed-([0-9a-z]+)\.html')
        if not code:
            code = scrapertools.find_single_match(page.data, r"""input\D*id=(?:'|")[^'"]+(?:'|").*?value='([a-z0-9]+)""")
        if code:
            page = httptools.downloadpage('http://akvideo.stream/video/' + code)
        else:
            return False, config.get_localized_string(70449) % "Akvideo"
    data = page.data

    # ID, code = scrapertools.find_single_match(data, r"""input\D*id=(?:'|")([^'"]+)(?:'|").*?value='([a-z0-9]+)""")
    # post = urllib.urlencode({ID: code})
    # logger.info('PAGE DATA' + data)
    if "File Not Found" in data:
        return False, config.get_localized_string(70449) % "Akvideo"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info(" url=" + page_url)
    video_urls = []

    global data
    # logger.info('PAGE DATA' + data)
    # sitekey = scrapertools.find_single_match(data, 'data-sitekey="([^"]+)')
    # captcha = platformtools.show_recaptcha(sitekey, page_url) if sitekey else ''
    #
    # if captcha:
    #     data = httptools.downloadpage(page_url, post={'g-recaptcha-response': captcha}).data
    vres = scrapertools.find_multiple_matches(data, 'nowrap[^>]+>([^,]+)')
    if not vres: vres = scrapertools.find_multiple_matches(data, '<td>(\d+x\d+)')

    data_pack = scrapertools.find_single_match(data, "</div>\n\s*<script[^>]+>(eval.function.p,a,c,k,e,.*?)\s*</script>")
    if data_pack != "":
        from lib import jsunpack
        data = jsunpack.unpack(data_pack)

    block = scrapertools.find_single_match(data, "sources:\s\[([^\]]+)\]")
    data = block if block else data
    # URL
    # logger.info(data)
    if vres:
        matches = scrapertools.find_multiple_matches(data, '''src:\s*["']?(http.*?\.mp4)''')
    else:
        matches = scrapertools.find_multiple_matches(data, '''src:\s*["']?(http.*?\.mp4)(?:[^,]+,[^,]+,res:([^,]+))?''')
        if matches:
            if len(matches[0])==2:
                i=0
                for m in matches:
                    vres.append("%sx" % m[1])
                    matches[i]=m[0]
                    i+=1

    _headers = urllib.urlencode(httptools.default_headers)

    i = 0
    for media_url in matches:
        # URL del vídeo
        video_urls.append([vres[i] if i<len(vres) else "" + " mp4 [Akvideo] ", media_url.replace('https://', 'http://') + '|' + _headers])
        i = i + 1

    return sorted(video_urls, key=lambda x: int(x[0].split('x')[0])) if vres else video_urls

# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector para streamcherry
# --------------------------------------------------------

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url).data
    if "We are unable to find the video" in data:
        return False, "[streamcherry] El archivo no existe o  ha sido borrado"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url).data

    video_urls = []

    matches = scrapertools.find_multiple_matches(data, "type:\"video/([^\"]+)\",src:d\('([^']+)',(.*?)\).+?height:(\d+)")

    for ext, encoded, code, quality in matches:

        media_url = decode(encoded, int(code))
        media_url = media_url.replace("@","")
        if not media_url.startswith("http"):
            media_url = "http:" + media_url
        video_urls.append([".%s %sp [streamcherry]" % (ext, quality), media_url])

    video_urls.reverse()
    for video_url in video_urls:
        logger.info("%s - %s" % (video_url[0], video_url[1]))

    return video_urls


def decode(encoded, code):
    logger.info("encoded '%s', code '%s'" % (encoded, code))

    _0x59b81a = ""
    k = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='
    k = k[::-1]

    count = 0

    for index in range(0, len(encoded) - 1):
        while count <= len(encoded) - 1:
            _0x4a2f3a = k.index(encoded[count])
            count += 1
            _0x29d5bf = k.index(encoded[count])
            count += 1
            _0x3b6833 = k.index(encoded[count])
            count += 1
            _0x426d70 = k.index(encoded[count])
            count += 1

            _0x2e4782 = ((_0x4a2f3a << 2) | (_0x29d5bf >> 4))
            _0x2c0540 = (((_0x29d5bf & 15) << 4) | (_0x3b6833 >> 2))
            _0x5a46ef = ((_0x3b6833 & 3) << 6) | _0x426d70
            _0x2e4782 = _0x2e4782 ^ code

            _0x59b81a = str(_0x59b81a) + chr(_0x2e4782)

            if _0x3b6833 != 64:
                _0x59b81a = str(_0x59b81a) + chr(_0x2c0540)
            if _0x3b6833 != 64:
                _0x59b81a = str(_0x59b81a) + chr(_0x5a46ef)

    return _0x59b81a

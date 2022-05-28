# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Streamz
# --------------------------------------------------------

import re
from core import httptools, scrapertools, support
from platformcode import logger, config
from lib import jsunpack


def test_video_exists(page_url):
    global data
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url)

    if "<b>File not found, sorry!</b" in data.data:
        return False, config.get_localized_string(70449) % "streamZ"
    return True, ""


def get_video_url(page_url, video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    packed_data = scrapertools.find_multiple_matches(data.data, r'(eval.*?video(\d).*?video_(\d)[^<]+)')
    if packed_data:
        for p, index, control in packed_data:
            if index == control:
                try:
                    url = scrapertools.find_single_match(jsunpack.unpack(p), r"src:\\'([^'\\]+)")
                    break
                except:
                    pass

    else:
        url = re.sub(r'(\.\w{2,3})/\w', '\\1/getl1nk-', data.url) + '.dll'
    url += "|Referer=https://streamz.ws/&User-Agent=Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14'"
    video_urls.append(["mp4 [streamZ]", url])

    return video_urls

def get_filename(page_url):
    # support.dbg()
    title = httptools.downloadpage(page_url).data.split('<title>')[1].split('</title>')[0]
    prefix = 'StreamZZ.to '
    if title.startswith(prefix):
        return title[len(prefix):]
    return ""
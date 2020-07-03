# -*- coding: utf-8 -*-

import time, sys
if sys.version_info[0] >= 3:
    import urllib.parse as urllib
else:
    import urllib

from core import httptools, scrapertools
from lib import jsunpack
from platformcode import logger, config


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    data = httptools.downloadpage(page_url).data.replace('"', "'")
    if "Not Found" in data or "File Does not Exist" in data:
        return False, config.get_localized_string(70449) % "DeltaBit"
    return True, ""

def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(deltabit page_url='%s')" % page_url)
    video_urls = []
    global data

    post = urllib.urlencode({k: v for k, v in scrapertools.find_multiple_matches(data, "name='([^']+)' value='([^']*)'")})
    time.sleep(2.1)
    data = httptools.downloadpage(page_url, post=post).data

    videos_packed = scrapertools.find_single_match(data, r"</div>\s*<script type='text/javascript'>(eval.function.p,a,c,k,e,.*?)\s*</script>")

    video_unpacked = jsunpack.unpack(videos_packed)
    videos = scrapertools.find_single_match(video_unpacked, r'sources:\["([^"]+)"\]')
    video_urls.append([videos.split('.')[-1] + ' [DeltaBit]', videos.replace('https:','http:')])
    return video_urls

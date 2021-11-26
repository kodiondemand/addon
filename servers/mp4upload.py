# -*- coding: utf-8 -*-
import re

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import config
from platformcode import logger


def test_video_exists(page_url):
    data = httptools.downloadpage(page_url).data
    if data == "File was deleted" or data == '':
        return False,  config.getLocalizedString(70449) % "mp4upload"


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    data = re.sub(r"\n|\r|\t|\s{2}", "", httptools.downloadpage(page_url).data)
    match = scrapertools.find_single_match(data, "<script type='text/javascript'>(.*?)</script>")
    data = jsunpack.unpack(match)
    data = data.replace("\\'", "'")
    media_url = scrapertools.find_single_match(data, '{type:"video/mp4",src:"([^"]+)"}')
    if not media_url:
        media_url = scrapertools.find_single_match(data, '"file":"([^"]+)')
    logger.debug("media_url=" + media_url)
    videoUrls = list()
    videoUrls.append({'type':scrapertools.get_filename_from_url(media_url).split('.')[-1], 'url':media_url})
    # for videoUrl in videoUrls:
    #     logger.debug("%s - %s" % (videoUrl[0], videoUrl[1]))
    return videoUrls

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
        return False,  config.get_localized_string(70449) % "mp4upload"


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    data = re.sub(r"\n|\r|\t|\s{2}", "", httptools.downloadpage(page_url).data)
    match = scrapertools.find_single_match(data, "<script type='text/javascript'>(.*?)</script>")
    data = jsunpack.unpack(match)
    data = data.replace("\\'", "'")
    media_url = scrapertools.find_single_match(data, '{type:"video/mp4",src:"([^"]+)"}')
    if not media_url:
        media_url = scrapertools.find_single_match(data, '"file":"([^"]+)')
    logger.debug("media_url=" + media_url)
    video_urls = list()
    video_urls.append([scrapertools.get_filename_from_url(media_url)[-4:] + " [mp4upload]", media_url])
    for video_url in video_urls:
        logger.debug("%s - %s" % (video_url[0], video_url[1]))
    return video_urls

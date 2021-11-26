# -*- coding: utf-8 -*-
##

from core import httptools, scrapertools
from platformcode import config, logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url).data

    if "File was deleted" in data or "Video is transfer on streaming server now." in data \
            or 'Conversione video in corso' in data:
        return False, config.getLocalizedString(70449) % "Speedvideo"

    return True, ""


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    videoUrls = []
    quality ={'MOBILE':1,
              'NORMAL':2,
              'HD':3}
    data = httptools.downloadpage(page_url).data
    # logger.debug('SPEEDVIDEO DATA '+ data)

    media_urls = scrapertools.findMultipleMatches(data, r"file:[^']'([^']+)',\s*label:[^\"]\"([^\"]+)\"")
    logger.debug("speed video - media urls: %s " % media_urls)
    for media_url, label in media_urls:
        media_url = httptools.downloadpage(media_url, only_headers=True, follow_redirects=False).headers.get("location", "")

        if media_url:
            videoUrls.append({'type':media_url.split('.')[-1], 'res':label, 'url':media_url})
    # logger.debug("speed video - media urls: %s " % videoUrls)

    return videoUrls


##,
##      {
##        "pattern": "speedvideo.net/([A-Z0-9a-z]+)",
##        "url": "https:\/\/speedvideo.net\/\\1"
##      }    

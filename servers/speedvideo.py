# -*- coding: utf-8 -*-
##

from core import httptools, scrapertools
from platformcode import config, logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url).data

    if "File was deleted" in data or "Video is transfer on streaming server now." in data \
            or 'Conversione video in corso' in data:
        return False, config.get_localized_string(70449) % "Speedvideo"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    video_urls = []
    quality ={'MOBILE':1,
              'NORMAL':2,
              'HD':3}
    data = httptools.downloadpage(page_url).data
    # logger.debug('SPEEDVIDEO DATA '+ data)

    media_urls = scrapertools.find_multiple_matches(data, r"file:[^']'([^']+)',\s*label:[^\"]\"([^\"]+)\"")
    logger.debug("speed video - media urls: %s " % media_urls)
    for media_url, label in media_urls:
        media_url = httptools.downloadpage(media_url, only_headers=True, follow_redirects=False).headers.get("location", "")

        if media_url:
            video_urls.append([media_url.split('.')[-1] + ' - ' + label + ' - ' + ' [Speedvideo]', media_url])
    logger.debug("speed video - media urls: %s " % video_urls)

    return sorted(video_urls, key=lambda x: quality[x[0].split(' - ')[1]])


##,
##      {
##        "pattern": "speedvideo.net/([A-Z0-9a-z]+)",
##        "url": "https:\/\/speedvideo.net\/\\1"
##      }    

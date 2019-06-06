# -*- coding: utf-8 -*-
##

from core import httptools, scrapertools
from platformcode import config, logger

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url).data

    if "File was deleted" in data:
        return False, config.get_localized_string(70449) % "Speedvideo"

    return True, ""

def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    
    data = httptools.downloadpage(page_url).data

    media_urls = scrapertools.find_multiple_matches(data, r"file:[^']'([^']+)',\s*label:[^\"]\"([^\"]+)\"")
    logger.info("speed video - media urls: %s " % media_urls)
    for media_url, label in media_urls:
        media_url = httptools.downloadpage(media_url, only_headers=True, follow_redirects=False).headers.get("location", "")

        if media_url:
            video_urls.append([label + " " + media_url.rsplit('.', 1)[1] + ' [speedvideo]', media_url])
    logger.info("speed video - media urls: %s " % video_urls)
    return video_urls


##,
##      {
##        "pattern": "speedvideo.net/([A-Z0-9a-z]+)",
##        "url": "https:\/\/speedvideo.net\/\\1"
##      }    

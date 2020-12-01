# -*- coding: utf-8 -*-

import re

from core import scrapertools
from platformcode import logger


# Returns an array of possible video url's from the page_url
def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)

    video_urls = []

    if page_url.startswith("http://www.4shared"):
        # http://www.4shared.com/embed/392975628/ff297d3f
        page_url = scrapertools.get_header_from_response(page_url, header_to_get="location")

        # http://www.4shared.com/flash/player.swf?file=http://dc237.4shared.com/img/392975628/ff297d3f/dlink__2Fdownload_2Flj9Qu-tF_3Ftsid_3D20101030-200423-87e3ba9b/preview.flv&d
        logger.debug("redirect a '%s'" % page_url)
        patron = "file\=([^\&]+)\&"
        matches = re.compile(patron, re.DOTALL).findall(page_url)

        try:
            video_urls.append(["[fourshared]", matches[0]])
        except:
            pass
    else:
        video_urls.append(["[fourshared]", page_url])

    for video_url in video_urls:
        logger.debug("%s - %s" % (video_url[0], video_url[1]))

    return video_urls

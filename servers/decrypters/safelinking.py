# -*- coding: utf-8 -*-

from core import scrapertools
from platformcode import logger


def get_long_url(short_url):
    logger.debug("(short_url='%s')" % short_url)

    location = scrapertools.get_header_from_response(short_url, header_to_get="location")
    logger.debug("location=" + location)

    return location

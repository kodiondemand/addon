# -*- coding: utf-8 -*-


from core import httptools
from core import scrapertools
from platformcode import config, logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if '"title":"Video Not Found"' in data:
        return False,  config.getLocalizedString(70449) % "Vimple"

    return True, ""


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("(page_url=%s)" % page_url)

    data = httptools.downloadpage(page_url).data

    media_url = scrapertools.find_single_match(data, '"video"[^,]+,"url":"([^"]+)"').replace('\\', '')
    data_cookie = config.getCookieData()
    cfduid = scrapertools.find_single_match(data_cookie, '.vimple.ru.*?(__cfduid\t[a-f0-9]+)') \
        .replace('\t', '=')
    univid = scrapertools.find_single_match(data_cookie, '.vimple.ru.*?(UniversalUserID\t[a-f0-9]+)') \
        .replace('\t', '=')

    media_url += "|User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0" \
                 "&Cookie=%s; %s" % (cfduid, univid)

    videoUrls = []
    videoUrls.append({'type':scrapertools.get_filename_from_url(media_url).split('.')[-1], 'url':media_url})

    # for videoUrl in videoUrls:
    #     logger.debug("%s - %s" % (videoUrl[0], videoUrl[1]))

    return videoUrls

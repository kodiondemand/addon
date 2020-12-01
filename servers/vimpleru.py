# -*- coding: utf-8 -*-


from core import httptools
from core import scrapertools
from platformcode import config, logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if '"title":"Video Not Found"' in data:
        return False,  config.get_localized_string(70449) % "Vimple"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("(page_url=%s)" % page_url)

    data = httptools.downloadpage(page_url).data

    media_url = scrapertools.find_single_match(data, '"video"[^,]+,"url":"([^"]+)"').replace('\\', '')
    data_cookie = config.get_cookie_data()
    cfduid = scrapertools.find_single_match(data_cookie, '.vimple.ru.*?(__cfduid\t[a-f0-9]+)') \
        .replace('\t', '=')
    univid = scrapertools.find_single_match(data_cookie, '.vimple.ru.*?(UniversalUserID\t[a-f0-9]+)') \
        .replace('\t', '=')

    media_url += "|User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0" \
                 "&Cookie=%s; %s" % (cfduid, univid)

    video_urls = []
    video_urls.append([scrapertools.get_filename_from_url(media_url)[-4:] + " [vimple.ru]", media_url])

    for video_url in video_urls:
        logger.debug("%s - %s" % (video_url[0], video_url[1]))

    return video_urls

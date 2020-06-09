# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from platformcode import logger, config


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global response

    response = httptools.downloadpage(page_url, cookies=False)
    if "Pagina non trovata" in response.data:
        return False, config.get_localized_string(70449) % "dailymotion"
    if response.code == 404:
        return False, config.get_localized_string(70449) % "dailymotion"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    cookie = {'Cookie': response.headers["set-cookie"]}
    data = response.data.replace("\\", "")
    subtitle = scrapertools.find_single_match(data, '"subtitles":.*?"es":.*?urls":\["([^"]+)"')
    qualities = scrapertools.find_multiple_matches(data, '"([^"]+)":(\[\{"type":".*?\}\])')
    for calidad, urls in qualities:
        patron = '"type":"(?:video|application)\\/([^"]+)","url":"([^"]+)"'
        matches = scrapertools.find_multiple_matches(urls, patron)
        for stream_type, stream_url in matches:
            stream_type = stream_type.replace('x-mpegURL', 'm3u8')
            if stream_type == "mp4":
                stream_url = httptools.downloadpage(stream_url, headers=cookie, only_headers=True,
                                                    follow_redirects=False).headers.get("location", stream_url)
            else:
                data_m3u8 = httptools.downloadpage(stream_url).data
                calidad = scrapertools.find_single_match(data_m3u8, r'NAME="([^"]+)"')
                stream_url_http = scrapertools.find_single_match(data_m3u8, r'PROGRESSIVE-URI="([^"]+)"')
                if stream_url_http:
                    stream_url = stream_url_http
            video_urls.append(["%sp .%s [dailymotion]" % (calidad, stream_type), stream_url, 0, subtitle])
    for video_url in video_urls:
        logger.info("%s - %s" % (video_url[0], video_url[1]))
    return video_urls
# -*- coding: utf-8 -*-
import re

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import config
from platformcode import logger


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    response = httptools.downloadpage(page_url)
    if response.code != 200 or "No longer available!" in response.data:
        return False,  config.get_localized_string(70449) % "vshare"
    else:
        return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url = " + page_url)
    headers = {"Referer":page_url}
    data = httptools.downloadpage(page_url, headers=headers).data
    flowplayer = re.search("url: [\"']([^\"']+)", data)
    if flowplayer:
        return [["FLV", flowplayer.group(1)]]
    video_urls = []
    try:
        jsUnpack = jsunpack.unpack(data)
        logger.debug(jsUnpack)
        fields = re.search("\[([^\]]+).*?parseInt\(value\)-(\d+)", jsUnpack)
        if fields:
            logger.debug("Values: " + fields.group(1))
            logger.debug("Substract: " + fields.group(2))
            substract = int(fields.group(2))
            arrayResult = [chr(int(value) - substract) for value in fields.group(1).split(",")]
            strResult = "".join(arrayResult)
            logger.debug(strResult)
            videoSources = re.findall("<source[\s]+src=[\"'](?P<url>[^\"']+)[^>]+label=[\"'](?P<label>[^\"']+)", strResult)
            for url, label in videoSources:
                url += "|Referer=%s" %page_url
                video_urls.append([label, url])
            video_urls.sort(key=lambda i: int(i[0].replace("p","")))
    except:
        url = scrapertools.find_single_match(data,'<source src="([^"]+)')
        video_urls.append(["MP4", url])
    return video_urls

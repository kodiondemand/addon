# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector mystream By Alfa development Group
# --------------------------------------------------------
from core import httptools
from core import scrapertools
from lib import js2py
from platformcode import logger, config
import re


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url)
    global page_data
    page_data = data.data
    if data.code == 404:
        return False, config.get_localized_string(70449) % "mystream"
    if "<title>video is no longer available" in data.data or "<title>Video not found" in data.data or "We are unable to find the video" in data.data:
        return False, config.get_localized_string(70449) % "mystream"
    return True, ""

def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    video_urls = []
    global page_data
    video_url = scrapertools.find_single_match(decode(page_data), r"'src',\s*'([^']+)")
    video_urls.append([video_url.split('.')[-1] + ' [MyStream]', video_url])
    return video_urls

def decode(data):
    # adapted from ResolveURL code - https://github.com/jsergio123/script.module.resolveurl

    first_group = scrapertools.find_single_match(data, r'"\\"("\+.*?)"\\""\)\(\)\)\(\)')
    match = scrapertools.find_single_match(first_group, r"(\(!\[\]\+\"\"\)\[.+?\]\+)")
    if match:
        first_group = first_group.replace(match, 'l').replace('$.__+', 't').replace('$._+', 'u').replace('$._$+', 'o')

        tmplist = []
        js = scrapertools.find_single_match(data, r'(\$={.+?});')
        if js:
            js_group = js[3:][:-1]
            second_group = js_group.split(',')

            i = -1
            for x in second_group:
                a, b = x.split(':')

                if b == '++$':
                    i += 1
                    tmplist.append(("$.{}+".format(a), i))

                elif b == '(![]+"")[$]':
                    tmplist.append(("$.{}+".format(a), 'false'[i]))

                elif b == '({}+"")[$]':
                    tmplist.append(("$.{}+".format(a), '[object Object]'[i]))

                elif b == '($[$]+"")[$]':
                    tmplist.append(("$.{}+".format(a), 'undefined'[i]))

                elif b == '(!""+"")[$]':
                    tmplist.append(("$.{}+".format(a), 'true'[i]))

            tmplist = sorted(tmplist, key=lambda z: str(z[1]))
            for x in tmplist:
                first_group = first_group.replace(x[0], str(x[1]))

            first_group = first_group.replace('\\"', '\\').replace("\"\\\\\\\\\"", "\\\\").replace('\\"', '\\').replace('"', '').replace("+", "")
    return first_group.encode('ascii').decode('unicode-escape').encode('ascii').decode('unicode-escape')
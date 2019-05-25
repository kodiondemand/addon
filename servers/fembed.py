# -*- coding: utf-8 -*-

from core import httptools
from core import jsontools
from platformcode import logger

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "Sorry 404 not found" in data:
        return False, "[fembed] El fichero ha sido borrado"
    return True, ""


def get_video_url(page_url, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    page_url = page_url.replace("/f/","/v/")
    page_url = page_url.replace("/v/","/api/source/")
    data = httptools.downloadpage(page_url, post={}).data
    data = jsontools.load(data)
    for videos in data["data"]:
        v = videos["file"]
        if not v.startswith("http"): v = "https://www.fembed.com" + videos["file"]
        video_urls.append([videos["label"] + " [fembed]", v])
    return video_urls

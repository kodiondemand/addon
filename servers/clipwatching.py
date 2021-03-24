# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger, config


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    global data
    data = httptools.downloadpage(page_url).data
    if "File Not Found" in data or "File was deleted" in data:
        return False, config.get_localized_string(70292) % "ClipWatching"
    return True, ""


def get_video_url(page_url, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    multires = False

    try:
        packed = scrapertools.find_single_match(data, "text/javascript'>(eval.*?)\s*</script>")
        unpacked = jsunpack.unpack(packed)
    except:
        unpacked = scrapertools.find_single_match(data,"window.hola_player.*")

    videos = scrapertools.find_multiple_matches(unpacked if unpacked else data, r'(?:file|src|sources):\s*(?:\[)?"([^"]+).*?(?:label:\s*"([^"]+))?')
    for video, label in videos:
        if ".jpg" not in video:
            if label and not label.endswith('p'):
                label += 'p'
                multires = True
            else:
                label = video.split('.')[-1]
                multires = False
            video_urls.append([label + " [clipwatching]", video])
    if multires:
        video_urls.sort(key=lambda it: int(it[0].split("p ", 1)[0]))
    return video_urls

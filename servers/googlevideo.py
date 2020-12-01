# -*- coding: utf-8 -*-

import re

from core import httptools
from platformcode import logger


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("(page_url='%s')" % page_url)
    video_urls = []
    # Lo extrae a partir de flashvideodownloader.org
    if page_url.startswith("http://"):
        url = 'http://www.flashvideodownloader.org/download.php?u=' + page_url
    else:
        url = 'http://www.flashvideodownloader.org/download.php?u=http://video.google.com/videoplay?docid=' + page_url
    logger.debug("url=" + url)
    data = httptools.downloadpage(url).data

    # Extrae el vídeo
    newpatron = '</script>.*?<a href="(.*?)" title="Click to Download">'
    newmatches = re.compile(newpatron, re.DOTALL).findall(data)
    if len(newmatches) > 0:
        video_urls.append(["[googlevideo]", newmatches[0]])

    for video_url in video_urls:
        logger.debug("%s - %s" % (video_url[0], video_url[1]))

    return video_urls

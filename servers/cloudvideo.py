# Conector Cloudvideo By Alfa development Group
# --------------------------------------------------------

from core import httptools
from core import scrapertools
from platformcode import logger, config
from lib import jsunpack


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    html = httptools.downloadpage(page_url)
    global data
    data = html.data
    if html.code == 404 or 'No Signal 404 Error Page' in data:
        return False, config.getLocalizedString(70449) % "CloudVideo"
    return True, ""


def get_videoUrl(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    videoUrls = []
    global data
    # data = httptools.downloadpage(page_url).data
    enc_data = scrapertools.find_single_match(data, r'text/javascript">(eval.+?)(?:\n|\s*</script>)')
    if enc_data:
        dec_data = jsunpack.unpack(enc_data)
        matches = scrapertools.findMultipleMatches(dec_data, r'src:"([^"]+)"')
    else:
        sources = scrapertools.find_single_match(data, r"<source(.*?)</source")
        patron = r'src="([^"]+)'
        matches = scrapertools.findMultipleMatches(sources, patron)
    for url in matches:
        Type = 'm3u8'
        videoUrl = url
        if 'label' in url:
            url = url.split(',')
            videoUrl = url[0]
            Type = url[1].replace('label:','')
        videoUrls.append({'type':Type, 'url':videoUrl})
    return videoUrls

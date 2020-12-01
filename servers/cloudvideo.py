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
        return False, config.get_localized_string(70449) % "CloudVideo"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    video_urls = []
    global data
    # data = httptools.downloadpage(page_url).data
    enc_data = scrapertools.find_single_match(data, r'text/javascript">(eval.+?)(?:\n|\s*</script>)')
    if enc_data:
        dec_data = jsunpack.unpack(enc_data)
        matches = scrapertools.find_multiple_matches(dec_data, r'src:"([^"]+)"')
    else:
        sources = scrapertools.find_single_match(data, r"<source(.*?)</source")
        patron = r'src="([^"]+)'
        matches = scrapertools.find_multiple_matches(sources, patron)
    for url in matches:
        Type = 'm3u8'
        video_url = url
        if 'label' in url:
            url = url.split(',')
            video_url = url[0]
            Type = url[1].replace('label:','')
        video_urls.append(['%s [CloudVideo]' % Type, video_url])
    return video_urls

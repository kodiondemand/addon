import ast ,sys
import base64 
if sys .version_info [0 ]>=3 :
    import urllib .parse as urlparse 
else :
    import urlparse 
from core import httptools ,scrapertools ,support 
from lib import jsunpack 
from platformcode import logger ,config ,platformtools 

def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    global data

    data = httptools.downloadpage(page_url).data

    if "File is no longer available" in data:
        return False, config.get_localized_string(70449) % "Maxstream"

    return True, ""

def get_video_url (page_url, premium=False, user="", password="", video_password=""):
    global data
    video_urls = []
    html = httptools.downloadpage(page_url).data;
    if not scrapertools.find_single_match(html, '(eval.+)'):
        html = httptools.downloadpage(scrapertools.find_single_match(html, r'<iframe [^>]+src="([^"]+)')).data
    js = scrapertools.find_single_match(html, '(eval.+)')
    packed = jsunpack.detect(js);
    if(packed):
        video = jsunpack.unpack(js)
        video = scrapertools.find_single_match(video, r'src:"(.+)",type');
        video_urls.append(["[Maxstream]", video])
        return video_urls
        
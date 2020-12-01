# -*- coding: utf-8 -*-

try:
    import urllib.parse as urllib
except ImportError:
    import urllib

from core import httptools, support
from core import scrapertools
from platformcode import logger, config

headers = [['User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0']]


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    # page_url = re.sub('akvideo.stream/(?:video/|video\\.php\\?file_code=)?(?:embed-)?([a-zA-Z0-9]+)','akvideo.stream/video/\\1',page_url)
    global data
    page = httptools.downloadpage(page_url, headers=headers)
    if 'embed_ak.php' in page_url or '/embed-' in page.url:
        code = scrapertools.find_single_match(page.url, '/embed-([0-9a-z]+)\.html')
        if not code:
            code = scrapertools.find_single_match(page.data, r"""input\D*id=(?:'|")[^'"]+(?:'|").*?value='([a-z0-9]+)""")
        if code:
            page = httptools.downloadpage('http://akvideo.stream/video/' + code, headers=headers)
        else:
            return False, config.get_localized_string(70449) % "Akvideo"

    if 'video.php?file_code=' in page.url:
        page = httptools.downloadpage(page.url.replace('video.php?file_code=', 'video/'), headers=headers)
    data = page.data

    # ID, code = scrapertools.find_single_match(data, r"""input\D*id=(?:'|")([^'"]+)(?:'|").*?value='([a-z0-9]+)""")
    # post = urllib.urlencode({ID: code})
    # logger.debug('PAGE DATA' + data)
    if "File Not Found" in data:
        return False, config.get_localized_string(70449) % "Akvideo"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug(" url=" + page_url)
    video_urls = []

    global data
    # logger.debug('PAGE DATA' + data)
    # sitekey = scrapertools.find_single_match(data, 'data-sitekey="([^"]+)')
    # captcha = platformtools.show_recaptcha(sitekey, page_url) if sitekey else ''
    #
    # if captcha:
    #     data = httptools.downloadpage(page_url, post={'g-recaptcha-response': captcha}).data
    vres = scrapertools.find_multiple_matches(data, 'nowrap[^>]+>([^,]+)')
    if not vres: vres = scrapertools.find_multiple_matches(data, '<td>(\d+x\d+)')

    data_pack = scrapertools.find_single_match(data, "</div>\n\s*<script[^>]+>(eval.function.p,a,c,k,e,.*?)\s*</script>")
    if data_pack != "":
        from lib import jsunpack
        data = jsunpack.unpack(data_pack)

    _headers = urllib.urlencode(httptools.default_headers)
    video_urls = support.get_jwplayer_mediaurl(data, 'akvideo', onlyHttp=True)


    return sorted(video_urls, key=lambda x: int(x[0].split('x')[0])) if vres else video_urls

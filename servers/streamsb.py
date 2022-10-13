# adapted from
# https://github.com/tvaddonsco/script.module.urlresolver/blob/master/lib/urlresolver/plugins/streamsb.py

from core import httptools, scrapertools
from platformcode import config
import base64


def test_video_exists(page_url):
    global data
    data = httptools.downloadpage(page_url).data

    if 'File Not Found' in data:
        return False, config.get_localized_string(70449) % "StreamSB"
    else:
        return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    video_urls = []
    global data
    dl_url = 'https://{}/dl?op=download_orig&id={}&mode={}&hash={}'

    host = scrapertools.get_domain_from_url(page_url)
    sources = scrapertools.find_multiple_matches(data, r'download_video([^"]+)[^\d]+\d+x(\d+)')
    hash = scrapertools.find_single_match(data, r"file_id',\s'(\d+)")

    if sources:
        sources.sort(key=lambda x: int(x[1]), reverse=True)
        sources = [(x[1] + 'p', x[0]) for x in sources]
        s = sources[0]  # only the first to reduce the number of requests to google recaptcha
        code, mode, null = eval(s[1])
        data = httptools.downloadpage(dl_url.format(host, code, mode, hash)).data
        captcha = scrapertools.girc(data, 'https://{0}/'.format(host), base64.b64encode('https://{0}:443'.format(host).encode('utf-8')).decode('utf-8').replace('=', ''))
        if captcha:
            hash = scrapertools.find_single_match(data, r'"hash" value="([^"]+)')
            data = httptools.downloadpage(dl_url.format(host, code, mode, hash), post={'op': 'download_orig', 'id': code, 'mode': mode, 'hash': hash, 'g-recaptcha-response': captcha}, timeout=10, header={'Referer':dl_url}).data
            media_url = scrapertools.find_single_match(data, r'href="([^"]+)"[^>]+>Download')
            if media_url:
                video_urls.append([s[0], media_url])
    return video_urls


def get_filename(page_url):
    # from core.support import dbg;dbg()
    title = httptools.downloadpage(page_url).data.split('<h3>')[1].split('</h3>')[0]
    prefix = 'Download '
    if title.startswith(prefix):
        return title[len(prefix):]
    return ""

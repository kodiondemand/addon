# adapted from
# https://github.com/tvaddonsco/script.module.urlresolver/blob/master/lib/urlresolver/plugins/streamsb.py

from core import httptools, scrapertools
from platformcode import config

host = 'streamsb.net'


def test_video_exists(page_url):
    global data
    data = httptools.downloadpage(page_url).data

    if 'File Not Found' in data:
        return False, config.get_localized_string(70449) % "MixDrop"
    else:
        return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    video_urls = []
    global data
    sources = scrapertools.find_multiple_matches(data, r'download_video([^"]+)[^\d]+\d+x(\d+)')
    if sources:
        sources.sort(key=lambda x: int(x[1]), reverse=True)
        sources = [(x[1] + 'p', x[0]) for x in sources]
        for s in sources:
            code, mode, hash = eval(s[1])
            dl_url = 'https://{0}/dl?op=download_orig&id={1}&mode={2}&hash={3}'.format(host, code, mode, hash)
            data = httptools.downloadpage(dl_url).data
            media_url = scrapertools.find_single_match(data, 'href="([^"]+)">Direct')
            if media_url:
                video_urls.append(["MP4", media_url])
    return video_urls

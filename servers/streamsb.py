import re
from core import httptools, support, scrapertools
from platformcode import config, logger, platformtools

try:
    import urllib.parse as urllib
except ImportError:
    import urllib
import re, sys

from base64 import b64encode


host = 'https://streamas.cloud'

def get_sources(page_url):
    sources = support.match(page_url, headers={'watchsb': 'sbstream', 'User-Agent': httptools.get_user_agent()}, replace_headers=True, patron=r'download_video([^"]+).*?<span>\s*(\d+)').matches
    if sources:
        sources = {s[1]: s[0].replace('(','').replace(')','').replace("'",'').split(',') for s in sources}
    return sources


def test_video_exists(page_url):
    global sources
    sources = get_sources(page_url)

    if sources:
        return True, ""
    else:
        return False, config.get_localized_string(70449) % "StreamSB"


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    global sources
    video_urls = list()
    if sources:
        action = config.get_setting('default_action')
        if action == 0:
            progress = platformtools.dialog_progress_bg("StreamSB", message="Risoluzione URLs")
            step = int(100 / len(sources))
            percent = 0
            for res, url in sources.items():
                progress.update(percent, "Risoluzione URL: {}p".format(res))
                r, u = resolve_url(res, url)
                percent += step
                progress.update(percent, "Risoluzione URL: {}p".format(res))
                video_urls.append(['{} [{}]'.format(u.split('.')[-1], r), u])
            progress.close()
        else:
            res = sorted([* sources])[0 if action == 1 else -1]
            progress = platformtools.dialog_progress_bg("StreamSB", message="Risoluzione URL: {}p".format(res))
            url = sources[res]
            r, u = resolve_url(res, url)
            progress.close()
            video_urls.append(['{} [{}]'.format(u.split(',')[-1], r), u])

    return video_urls


def get_payloads(data, token):
    # support.dbg()
    payloads = {'g-recaptcha-response': token}
    for name, value in support.match(data, patron=r'input type="hidden" name="([^"]+)" value="([^"]+)').matches:
        payloads[name] = value
    return payloads

def resolve_url(res, params):
    url = ''
    source_url = '{}/dl?op=download_orig&id={}&mode={}&hash={}'.format(host, params[0], params[1], params[2])
    data = httptools.downloadpage(source_url).data
    co = b64encode((host + ':443').encode('utf-8')).decode('utf-8').replace('=', '')
    token = scrapertools.girc(data, host, co)
    payload = get_payloads(data, token)
    if token:
        url = support.match(source_url, patron=r'href="([^"]+)"\s*class="btn\s*btn-light', post=payload).match
    return res, url
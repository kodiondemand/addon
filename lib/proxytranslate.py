# based on https://github.com/MrCl0wnLab/ProxyGoogleTranslate
import sys
if sys.version_info[0] >= 3:
    from urllib import request
    import urllib.parse as urlparse
    PY3 = True
else:
    PY3 = False
    import urllib as request
    import urlparse

import re
import time

import requests
try:
    from platformcode import logger
except ImportError:
    logger = None

HEADERS = {
    'Host': 'translate.google.com',
    'User-Agent': 'android'
}

MAX_CONECTION_THREAD = 10
SL = 'en'
TL = 'it'

BASE_URL_PROXY = 'https://translate.googleusercontent.com'
BASE_URL_TRANSLATE = 'https://translate.google.com/translate?hl=it&sl=' + SL + '&tl=' + TL + '&u=[TARGET_URL]&sandbox=0'  # noqa: E501


def checker_url(html, url):
    grep_regex = re.findall(r'(?:href="|src="|value=")([^"]+)', html)  # noqa: E501
    for url_result_regex in grep_regex:
        if url in url_result_regex:
            return url_result_regex.replace('&amp;', '&')


def process_request_proxy(url):
    if not url:
        return

    try:
        domain = urlparse.urlparse(url).netloc

        target_url = \
            BASE_URL_TRANSLATE.replace('[TARGET_URL]', request.quote(url))

        if logger:
            logger.debug(target_url)
        else:
            print(target_url)

        return_html = requests.get(target_url, timeout=20, headers=HEADERS)

        if not return_html:
            return

        url_request = checker_url(
            return_html.text,
            BASE_URL_PROXY + '/translate_p?hl=it&sl=' + SL + '&tl=' + TL + '&u='
        )

        if logger:
            logger.debug(url_request)
        else:
            print(url_request)

        request_final = requests.get(
            url_request,
            timeout=20,
            headers={'User-Agent': 'android'}
        )

        url_request_proxy = checker_url(
            request_final.text, 'translate.google')

        if logger:
            logger.debug(url_request_proxy)
        else:
            print(url_request_proxy)

        data = None
        result = None
        while not data or 'Sto traducendo' in data:
            time.sleep(0.5)
            result = requests.get(
                url_request_proxy,
                timeout=20,
                headers={'User-Agent': 'android'}
            )
            data = result.content.decode('utf-8', 'ignore')
            if not PY3:
                data = data.encode('utf-8')
            if logger:
                logger.debug()

        data = re.sub('\s(\w+)=(?!")([^<>\s]+)', r' \1="\2"', data)
        data = re.sub('https://translate\.googleusercontent\.com/.*?u=(.*?)&amp;usg=[A-Za-z0-9_-]+', '\\1', data)
        data = re.sub('https?://[a-zA-Z0-9]+--' + domain.replace('.', '-') + '\.translate\.goog(/[a-zA-Z0-9#/-]+)', 'https://' + domain + '\\1', data)
        data = re.sub('\s+<', '<', data)
        data = data.replace('&amp;', '&').replace('https://translate.google.com/website?sl=' + SL + '&tl=' + TL + '&u=', '')

        return {'url': url.strip(), 'result': result, 'data': data}
    except Exception as e:
        if logger:
            logger.error(e)
        else:
            print(e)

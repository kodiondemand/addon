# based on https://github.com/MrCl0wnLab/ProxyGoogleTranslate
import sys
if sys.version_info[0] >= 3:
    from urllib import request
    PY3 = True
else:
    PY3 = False
    import urllib as request

import re
import time

import requests
from platformcode import logger

HEADERS = {
    'Host': 'translate.google.com',
    'User-Agent': 'android'
}

MAX_CONECTION_THREAD = 10

BASE_URL_PROXY = 'https://translate.googleusercontent.com'
BASE_URL_TRANSLATE = 'https://translate.google.com/translate?hl=it&sl=en&tl=it&u=[TARGET_URL]&sandbox=0'  # noqa: E501


def checker_url(html, url):
    grep_regex = re.findall(r'href="|src="|value="|((?:http[s]://|ftp[s]://)+\.*([-a-zA-Z0-9\.]+)([-a-zA-Z0-9\.]){1,}([-a-zA-Z0-9_\.\#\@\:%_/\?\=\~\&\-\//\!\'\;\(\)\s\^\:blank:\:punct:\:xdigit:\:space:\$]+))', html)  # noqa: E501
    for url_result_regex in grep_regex:
        if url in url_result_regex[0]:
            return url_result_regex[0].replace('&amp;', '&')


def process_request_proxy(url):
    if not url:
        return

    try:
        target_url = \
            BASE_URL_TRANSLATE.replace('[TARGET_URL]', request.quote(url))

        logger.debug(target_url)

        return_html = requests.get(target_url, timeout=20, headers=HEADERS)

        if not return_html:
            return

        url_request = checker_url(
            return_html.text,
            BASE_URL_PROXY + '/translate_p?hl=it&sl=en&tl=it&u='
        )

        logger.debug(url_request)

        request_final = requests.get(
            url_request,
            timeout=20,
            headers={'User-Agent': 'android'}
        )

        url_request_proxy = checker_url(
            request_final.text, BASE_URL_PROXY + '/translate_c?depth=1')

        logger.debug(url_request_proxy)

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
            logger.debug()

        data = re.sub('\s(\w+)=(?!")([^<>\s]+)', r' \1="\2"', data)
        data = re.sub('https://translate\.googleusercontent\.com/.*?u=(.*?)&amp;usg=[A-Za-z0-9_-]+', '\\1', data)

        return {'url': url.strip(), 'result': result, 'data': data.replace('&amp;', '&')}
    except Exception as e:
        logger.error(e)

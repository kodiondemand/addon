# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector MaxStream
# --------------------------------------------------------
import ast, sys

import requests

from core import httptools, scrapertools, support
from lib import jsunpack
from platformcode import logger, config, platformtools
if sys.version_info[0] >= 3:
    import urllib.parse as urlparse
else:
    import urlparse


def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)

    global data
    if 'uprot/' in page_url:
        id = httptools.downloadpage(page_url, follow_redirects=False, cloudscraper=True).headers.get('location').split('/')[-1]
    else:
        id = page_url.split('/')[-1]
    page_url = 'http://lozioangie.altervista.org/max_anticaptcha.php?id=' + id
    data = httptools.downloadpage(page_url, cloudscraper=True).data

    if scrapertools.find_single_match(data, '(?<!none);[^>]*>file was deleted'):
        return False, config.get_localized_string(70449) % "MaxStream"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    video_urls = []
    global data
    if 'captcha' in data:
        httptools.set_cookies(requests.get('http://lozioangie.altervista.org/maxcookie.php').json())
        data = httptools.downloadpage(page_url, cloudscraper=True).data

    # sitekey = scrapertools.find_multiple_matches(data, """data-sitekey=['"] *([^"']+)""")
    # if sitekey: sitekey = sitekey[-1]
    # captcha = platformtools.show_recaptcha(sitekey, page_url) if sitekey else ''
    #
    # possibleParam = scrapertools.find_multiple_matches(data,
    #                                                    r"""<input.*?(?:name=["']([^'"]+).*?value=["']([^'"]*)['"]>|>)""")
    # if possibleParam:
    #     post = {param[0]: param[1] for param in possibleParam if param[0]}
    #     if captcha: post['g-recaptcha-response'] = captcha
    #     if post:
    #         data = httptools.downloadpage(page_url, post=post, follow_redirects=True, verify=False).data
    # else:
    #     platformtools.dialog_ok(config.get_localized_string(20000), config.get_localized_string(707434))
    #     return []

    packed = support.match(data, patron=r"(eval\(function\(p,a,c,k,e,d\).*?)\s*</script").match
    if packed:
        data = jsunpack.unpack(packed)
    url = scrapertools.find_single_match(data, 'src:\s*"([^"]+)')
    if url:
        video_urls.append(['m3u8 [MaxStream]', url])
    return video_urls
    # support.dbg()
    # possible_cast_url = support.match('http://maxstream.video/?op=page&tmpl=../../download1', patron='<a[^<]+href="(?:https://maxstream\.video/)?([^".?]+/)"').matches
    # for cast_url in possible_cast_url:
    #     data = httptools.downloadpage('http://maxstream.video/' + cast_url + page_url.split('/')[-1]).data
    #     url_video = ''
    #
    #     lastIndexStart = data.rfind('<script>')
    #     lastIndexEnd = data.rfind('</script>')
    #
    #     script = data[ (lastIndexStart + len('<script>')):lastIndexEnd ]
    #
    #     match = scrapertools.find_single_match(script, r'(\[[^\]]+\])[^\{]*\{[^\(]+\(parseInt\(value\)\s?-\s?([0-9]+)')
    #     if match:
    #         char_codes = ast.literal_eval(match[0])
    #         hidden_js = "".join([chr(c - int(match[1])) for c in char_codes])
    #
    #         newurl = scrapertools.find_single_match(hidden_js, r'\$.get\(\'([^\']+)').replace('https://', 'http://')
    #         castpage = httptools.downloadpage(newurl, headers={'x-requested-with': 'XMLHttpRequest', 'Referer': page_url}).data
    #         url_video = scrapertools.find_single_match(castpage, r"cc\.cast\('(http[s]?.[^']+)'")
    #     else:
    #         logger.debug('Something wrong: no url found before that :(')
    #
    #     if url_video and url_video.split('/')[-1] == page_url.split('/')[-1]:
    #         import random, string
    #         parse = urlparse.urlparse(url_video)
    #         video_urls = [['mp4 [MaxStream]', url_video]]
    #         try:
    #             r1 = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(19))
    #             r2 = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(19))
    #             r3 = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(19))
    #             video_urls.append(['m3u8 [MaxStream]', '{}://{}/hls/{},{},{},{},.urlset/master.m3u8'.format(parse.scheme, parse.netloc, parse.path.split('/')[1], r1, r2, r3)])
    #             # video_urls.append(['m3u8 [MaxStream]', '{}://{}/hls/{},wpsc2hllm5g5fkjvslq,4jcc2hllm5gzykkkgha,fmca2hllm5jtpb7cj5q,.urlset/master.m3u8'.format(parse.scheme, parse.netloc, parse.path.split('/')[1])])
    #         except:
    #             logger.debug('Something wrong: Impossible get HLS stream')
    #         return video_urls

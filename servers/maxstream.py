# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector MaxStream
# --------------------------------------------------------

from core import httptools, scrapertools, support
from lib import jsunpack
from platformcode import logger, config
import ast, sys

if sys.version_info[0] >= 3:
    import urllib.parse as urlparse
else:
    import urlparse

headers =({'user-agent':'Mozilla/5.0 (Linux; Android 9; SM-A102U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.136 Mobile Safari/537.36'})

def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)

    global data
    data = httptools.downloadpage(page_url, headers=headers).data

    if "file was deleted" in data:
        return False, config.get_localized_string(70449) % "MaxStream"

    return True, ""



def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    video_urls = []
    
    # support.dbg()
    packed = support.match(data, patron=r"(eval\(function\(p,a,c,k,e,d\).*?)\s*</script").match
    unpack = jsunpack.unpack(packed)
    url = scrapertools.find_single_match(unpack, 'src:\s*"([^"]+)')
    if url:
         video_urls.append(['m3u8 [MaxStream]', url])
    # url_video = ''

    # lastIndexStart = data.rfind('<script>')
    # lastIndexEnd = data.rfind('</script>')

    # script = data[ (lastIndexStart + len('<script>')):lastIndexEnd ]

    # match = scrapertools.find_single_match(script, r'(\[[^\]]+\])[^\{]*\{[^\(]+\(parseInt\(value\)\s?-\s?([0-9]+)')
    # if match:
    #     char_codes = ast.literal_eval(match[0])
    #     hidden_js = "".join([chr(c - int(match[1])) for c in char_codes])

    #     newurl = scrapertools.find_single_match(hidden_js, r'\$.get\(\'([^\']+)').replace('https://', 'http://')
    #     castpage = httptools.downloadpage(newurl, headers={'x-requested-with': 'XMLHttpRequest', 'Referer': page_url}).data
    #     url_video = scrapertools.find_single_match(castpage, r"cc\.cast\('(http[s]?.[^']+)'")
    # else:
    #     logger.debug('Something wrong: no url found before that :(')

    # if url_video:
    #     import random, string
    #     parse = urlparse.urlparse(url_video)
    #     video_urls.append(['mp4 [MaxStream]', url_video])
    #     try:
    #         r1 = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(19))
    #         r2 = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(19))
    #         r3 = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(19))
    #         video_urls.append(['m3u8 [MaxStream]', '{}://{}/hls/{},{},{},{},.urlset/master.m3u8'.format(parse.scheme, parse.netloc, parse.path.split('/')[1], r1, r2, r3)])
    #         # video_urls.append(['m3u8 [MaxStream]', '{}://{}/hls/{},wpsc2hllm5g5fkjvslq,4jcc2hllm5gzykkkgha,fmca2hllm5jtpb7cj5q,.urlset/master.m3u8'.format(parse.scheme, parse.netloc, parse.path.split('/')[1])])
    #     except:
    #         logger.debug('Something wrong: Impossible get HLS stream')
    return video_urls





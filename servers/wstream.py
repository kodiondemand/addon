# -*- coding: utf-8 -*-
# Kodi on Demand - Kodi Addon - Kodi Addon
# by DrZ3r0 - Fix Alhaziel

import json
import re

try: import urllib.parse as urllib
except ImportError: import urllib

from core import httptools, scrapertools
from platformcode import logger, config, platformtools

# real_host = 'wstream.video'

def test_video_exists(page_url):
    global headers
    real_host = '116.202.226.34'
    headers = [['User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0'],
               ['Host', scrapertools.get_domain_from_url(page_url)]]

    logger.log("(page_url='%s')" % page_url)
    if 'wstream' in page_url:
        resp = httptools.downloadpage(page_url.replace(headers[1][1], real_host), headers=headers, verify=False)
    else:
        resp = httptools.downloadpage(page_url, headers=headers, verify=False)

    global data, real_url
    data = resp.data

    page_url = resp.url.replace(headers[1][1], real_host)
    if '/streaming.php' in page_url in page_url:
        code = httptools.downloadpage(page_url, headers=headers, follow_redirects=False, only_headers=True, verify=False).headers['location'].split('/')[-1].replace('.html', '')
        # logger.log('WCODE=' + code)
        page_url = 'https://' + real_host + '/video.php?file_code=' + code
        data = httptools.downloadpage(page_url, headers=headers, follow_redirects=True, verify=False).data

    if 'nored.icu' in str(headers):
        var = scrapertools.find_single_match(data, r'var [a-zA-Z0-9]+ = \[([^\]]+).*?')
        value = scrapertools.find_single_match(data, r'String\.fromCharCode\(parseInt\(value\) \D (\d+)')
        if var and value:
            dec = ''
            for v in var.split(','):
                dec += chr(int(v) - int(value))
            page_url = 'https://' + real_host + '/video.php?file_code=' + scrapertools.find_single_match(dec, "src='([^']+)").split('/')[-1].replace('.html','')
            headers = [['User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0'],['Host', 'wstream.video']]
            new_data = httptools.downloadpage(page_url, headers=headers, follow_redirects=True, verify=False).data
            logger.log('NEW DATA: \n' + new_data)
            if new_data:
                data = new_data

    real_url = page_url
    if "Not Found" in data or "File was deleted" in data or 'Video is processing' in data or 'Sorry this video is unavailable' in data:
        return False, config.get_localized_string(70449) % 'Wstream'
    else:
        return True, ""


# Returns an array of possible video url's from the page_url
def get_video_url(page_url, premium=False, user="", password="", video_password=""):

    def int_bckup_method():
        global data,headers
        page_url = scrapertools.find_single_match(data, r"""<center><a href='(https?:\/\/wstream[^']+)'\s*title='bkg'""")
        if not page_url:
            page_url = scrapertools.find_single_match(data, r"""<form action=['"]([^'"]+)['"]""")
        if page_url.startswith('/'):
            page_url = 'https://wstream.video' + page_url
        if page_url:
            data = httptools.downloadpage(page_url, headers=headers, follow_redirects=True, post={'g-recaptcha-response': captcha}, verify=False).data

    def getSources(data):
        possibileSources = scrapertools.find_multiple_matches(data, r'sources:\s*(\[[^\]]+\])')
        for data in possibileSources:
            try:
                data = re.sub('([A-z]+):(?!/)', '"\\1":', data)
                keys = json.loads(data)
                for key in keys:
                    if 'label' in key:
                        if not 'type' in key:
                            key['type'] = 'mp4'
                        if not 'src' in key and 'file' in key:
                            key['src'] = key['file']
                        video_urls.append(['%s [%s]' % (key['type'].replace('video/', ''), key['label']), key['src'].replace('https', 'http') + '|' + _headers])
                    elif type(key) != dict:
                        filetype = key.split('.')[-1]
                        if '?' in filetype: filetype = filetype.split('?')[0]
                        video_urls.append([filetype, key.replace('https', 'http') + '|' + _headers])
                    else:
                        if not 'src' in key and 'file' in key: key['src'] = key['file']
                        if key['src'].split('.')[-1] == 'mpd': pass
                        video_urls.append([key['src'].split('.')[-1], key['src'].replace('https', 'http') + '|' + _headers])
            except:
                pass

    logger.log("[Wstream] url=" + page_url)
    video_urls = []
    global data, real_url, headers

    sitekey = scrapertools.find_multiple_matches(data, """data-sitekey=['"] *([^"']+)""")
    if sitekey: sitekey = sitekey[-1]
    captcha = platformtools.show_recaptcha(sitekey, page_url.replace('116.202.226.34', headers[1][1]).replace('nored.icu', headers[1][1])) if sitekey else ''

    possibleParam = scrapertools.find_multiple_matches(data,r"""<input.*?(?:name=["']([^'"]+).*?value=["']([^'"]*)['"]>|>)""")
    if possibleParam[0][0]:
        post = {param[0]: param[1] for param in possibleParam if param[0]}
        if captcha: post['g-recaptcha-response'] = captcha
        if post:
            data = httptools.downloadpage(real_url, headers=headers, post=post, follow_redirects=True, verify=False).data
        elif captcha:
            int_bckup_method()
    elif captcha or not sitekey:
        int_bckup_method()
    else:
        platformtools.dialog_ok(config.get_localized_string(20000), config.get_localized_string(707434))
        return []

    headers.append(['Referer', real_url.replace('116.202.226.34', headers[1][1]).replace('nored.icu', headers[1][1])])
    _headers = urllib.urlencode(dict(headers))

    post_data = scrapertools.find_single_match(data, r"<script type='text/javascript'>(eval.function.p,a,c,k,e,.*?)\s*</script>")
    if post_data != "":
        from lib import jsunpack
        data = jsunpack.unpack(post_data)
        getSources(data)
    else:
        getSources(data)

    if not video_urls:
        media_urls = scrapertools.find_multiple_matches(data, r'(http[^\s]*?\.(?:mp4|m3u8))')

        for media_url in media_urls:
            video_urls.append([media_url.split('.')[-1] + " [Wstream] ", media_url + '|' + _headers])
    video_urls.sort(key=lambda x: x[0])
    return video_urls

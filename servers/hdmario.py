# -*- coding: utf-8 -*-
import xbmc

from core import httptools, scrapertools, filetools
from platformcode import logger, config

baseUrl = 'https://hdmario.live'

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global page, data

    page = httptools.downloadpage(page_url)
    data = page.data
    logger.info(page.url)

    if "the page you are looking for could not be found" in data:
        return False, config.get_localized_string(70449) % "HDmario"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    global page, data
    page_url = page_url.replace('?', '')
    logger.info("url=" + page_url)
    if 'unconfirmed' in page.url:
        from lib import onesecmail
        id = page_url.split('/')[-1]
        mail = onesecmail.getRandom()
        postData = {
            'email': mail,
            'hls_video_id': id
        }
        httptools.downloadpage(page.url, post=postData)
        jsonMail = onesecmail.waitForMail(mail)
        logger.info(jsonMail)
        if jsonMail:
            code = jsonMail['subject'].split(' - ')[0]
            page = httptools.downloadpage(page_url + '?code=' + code)
            data = page.data
    logger.info(data)
    from lib import jsunpack_js2py
    unpacked = jsunpack_js2py.unpack(scrapertools.find_single_match(data, '<script type="text/javascript">\n*\s*\n*(eval.*)'))
    # p,a,c,k,e,d data -> xhr.setRequestHeader
    secureProof = scrapertools.find_single_match(unpacked, """X-Secure-Proof['"]\s*,\s*['"]([^"']+)""")
    logger.info('X-Secure-Proof=' + secureProof)

    data = httptools.downloadpage(baseUrl + '/pl/' + page_url.split('/')[-1].replace('?', '') + '.m3u8', headers=[['X-Secure-Proof', secureProof]]).data
    filetools.write(xbmc.translatePath('special://temp/hdmario.m3u8'), data, 'w')

    video_urls = [['.m3u8 [HDmario]', 'special://temp/hdmario.m3u8']]

    return video_urls

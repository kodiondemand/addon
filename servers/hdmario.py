# -*- coding: utf-8 -*-
from threading import Thread

from core import httptools, scrapertools
from platformcode import logger, config
from BaseHTTPServer import BaseHTTPRequestHandler

baseUrl = 'https://hdmario.live'

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    data = httptools.downloadpage(page_url).data
    if "the page you are looking for could not be found" in data:
        return False, config.get_localized_string(70449) % "HDmario"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    global data
    # p,a,c,k,e,d data -> xhr.setRequestHeader
    global secureProof, server
    secureProof = scrapertools.find_single_match(data, '\|(\w{22})\|')
    logger.info('X-Secure-Proof=' + secureProof)

    from BaseHTTPServer import HTTPServer
    server = HTTPServer(('localhost', 9017), GetHandler)
    Thread(target=server.serve_forever).start()

    video_urls = [['.m3u8 [HDmario]', 'http://localhost:9017/master/' + page_url.split('/')[-1].replace('?', '')]]

    return video_urls

def shutdown():
    import time
    time.sleep(1)
    server.shutdown()

class GetHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global secureProof
        data = httptools.downloadpage(baseUrl + self.path, headers=[['X-Secure-Proof', secureProof]]).data
        self.send_response(200)
        self.end_headers()
        self.wfile.write(data)
        Thread(target=shutdown).start()
        return
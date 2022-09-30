import base64
from http.server import BaseHTTPRequestHandler, HTTPServer
import xbmc

from platformcode import logger
from urllib.parse import parse_qs
hostName = "localhost"
serverPort = 8080
cookie_ricevuto = False
call = 'kodapp://app.kod/open?s={}&cb=http://{}:{}/cb'


class MyServer(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers['content-length'])
        postvars = parse_qs(
            self.rfile.read(length),
            keep_blank_values=True)
        logger.info(postvars)
        self.send_response(200)
        global cookie_ricevuto
        cookie_ricevuto = True


def call_url(url):
    webServer = HTTPServer((hostName, serverPort), MyServer)
    logger.info("Server started http://%s:%s" % (hostName, serverPort))
    xbmc.executebuiltin('StartAndroidActivity("",{})'.format(call.format(base64.b64encode(url), hostName, serverPort)))
    while not cookie_ricevuto:
        webServer.handle_request()
    logger.info("Server stopped.")

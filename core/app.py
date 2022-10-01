import base64
from http.server import BaseHTTPRequestHandler, HTTPServer
import xbmc
from core import jsontools
from platformcode import logger
from urllib.parse import parse_qs
hostName = "localhost"
serverPort = 8080
cookie_ricevuto = False
call = 'kodapp://app.kod/open?s={}&cb=http://{}:{}/cb'


class MyServer(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers['content-length'])
        postvars = self.rfile.read(length)
        logger.info(postvars)
        self.send_response(200)
        global cookie_ricevuto
        cookie_ricevuto = True


def call_url(url):
    webServer = HTTPServer((hostName, serverPort), MyServer)
    logger.info("Server started http://%s:%s" % (hostName, serverPort))
    s = base64.b64encode(jsontools.dump({'url': url}).encode()).decode()
    activity = 'StartAndroidActivity("com.kodapp","android.intent.action.VIEW","",{})'.format(call.format(s, hostName, serverPort))
    logger.info(activity)
    xbmc.executebuiltin(activity)
    while not cookie_ricevuto:
        webServer.handle_request()
    logger.info("Server stopped.")

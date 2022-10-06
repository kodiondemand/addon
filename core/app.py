import base64
from http.server import BaseHTTPRequestHandler, HTTPServer
import xbmc
from core import jsontools, httptools
from platformcode import logger
hostName = xbmc.getIPAddress()
serverPort = 8080
ret = None
call = 'kodapp://app.kod/open?s={}&ua={}&cb=http://{}:{}/'


class MyServer(BaseHTTPRequestHandler):
    def do_POST(self):
        global ret
        length = int(self.headers['content-length'])
        postvars = self.rfile.read(length).decode()
        ret = jsontools.load(postvars)
        logger.info(ret)
        self.send_response(200)


def call_url(url):
    global cookie_ricevuto
    webServer = HTTPServer((hostName, serverPort), MyServer)
    logger.info("Server started http://%s:%s" % (hostName, serverPort))
    s = base64.b64encode(jsontools.dump({'url': url}).encode()).decode()
    activity = 'StartAndroidActivity("com.kodapp","android.intent.action.VIEW","",{})'.format(call.format(s, httptools.get_user_agent(), hostName, serverPort))
    logger.info(activity)
    xbmc.executebuiltin(activity)
    while not ret:
        webServer.handle_request()
    logger.info("Server stopped.")
    return ret

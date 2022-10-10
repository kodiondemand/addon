import base64
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
import xbmc, random
from core import jsontools, httptools
from platformcode import logger

hostName = xbmc.getIPAddress()
serverPort = random.randint(49152, 65535)
ret = []
call = 'kodapp://app.kod/open?s={}&ua={}&cb=http://{}:{}/'


class MyServer(BaseHTTPRequestHandler):
    def do_POST(self):
        global ret
        length = int(self.headers['content-length'])
        postvars = self.rfile.read(length).decode()
        ret = jsontools.load(postvars)
        logger.info(ret)
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")


def call_url(url):
    global serverPort
    webServer = None
    for t in range(10):  # try up to 10 port if already in use
        try:
            webServer = HTTPServer((hostName, serverPort), MyServer)
            break
        except socket.error:
            serverPort += 1
    if webServer:
        logger.info("Server started http://%s:%s" % (hostName, serverPort))
        s = base64.b64encode(jsontools.dump({'url': url}).encode()).decode()
        ua = base64.b64encode(httptools.get_user_agent().encode()).decode()
        uri = call.format(s, ua, hostName, serverPort)
        if logger.DEBUG_ENABLED:
            uri += '&l=1'
        activity = 'StartAndroidActivity("com.kodapp","android.intent.action.VIEW","",{})'.format(uri)
        logger.info(activity)
        xbmc.executebuiltin(activity)
        while not ret:
            webServer.handle_request()
        logger.info("Server stopped.")
    return ret

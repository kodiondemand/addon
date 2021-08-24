import sys, traceback
if sys.version_info[0] >= 3:
    from http.server import HTTPServer
    from socketserver import ThreadingMixIn
else:
    from BaseHTTPServer import HTTPServer
    from SocketServer import ThreadingMixIn

from threading import Thread
from platformcode import logger


class Server(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    timeout = 1
    def __init__(self, address, handler, client):
        HTTPServer.__init__(self,address,handler)
        self._client = client
        self.running=True
        self.request = None

    def stop(self):
        self.running=False

    # def serve(self):
    #     while self.running:
    #         try:
    #             self.handle_request()
    #         except:
    #             logger.error(traceback.format_exc())

    def run(self):
        t=Thread(target=self.serve_forever, name='HTTP Server')
        t.daemon=self.daemon_threads
        t.start()

    def handle_error(self, request, client_address):
        if not "socket.py" in traceback.format_exc():
            logger.error(traceback.format_exc())

import time, os, re, sys

if sys.version_info[0] >= 3:
    PY3 = True
    from http.server import BaseHTTPRequestHandler
    import urllib.request as urllib
    import urllib.parse as urlparse
else:
    PY3 = False
    from BaseHTTPServer import BaseHTTPRequestHandler
    import urlparse
    import urllib

from platformcode import logger


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, format, *args):
        pass


    def do_GET(self):
        """
        " Got request
        " We are going to handle the request path in order to proxy each manifest
        """
        url = urlparse.urlparse(self.path).path

        logger.debug('HANDLER:', url)

        response = None

        # Default content-type for each manifest
        cType = "application/vnd.apple.mpegurl"

        if url == "/manifest.m3u8":
            response = self.server._client.get_main_manifest_content()

        elif url.startswith('/video/'):
            response = self.server._client.get_video_manifest_content(url)

        elif url.startswith('/audio/'):
            response = self.server._client.get_audio_manifest_content(url)

        elif url.endswith('enc.key'):
            # This path should NOT be used, see get_video_manifest_content function
            response = self.server._client.get_enc_key( url )
            cType = "application/octet-stream"


        if response == None:
            # Default 404 response
            self.send_error(404, 'Not Found')
            logger.warn('Responding 404 for url', url)

        else:
            # catch OK response and send it to client
            self.send_response(200)
            self.send_header("Content-Type", cType )
            self.send_header("Content-Length", str( len(response.encode('utf-8')) ) )
            self.end_headers()

            self.wfile.write( response.encode() )

            # force flush just to be sure
            self.wfile.flush()

            logger.info('HANDLER flushed:', cType , str( len(response.encode('utf-8')) ) )
            logger.debug( response.encode('utf-8') )



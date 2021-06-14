import base64, json, random, struct, time, sys, traceback
if sys.version_info[0] >= 3:
    PY3 = True
    import urllib.request as urllib
    xrange = range
else:
    PY3 = False
    import urllib

from core import httptools, jsontools, support
from threading import Thread

import re

from lib.streamingcommunity.handler import Handler
from platformcode import logger
from lib.streamingcommunity.server import Server


class Client(object):

    def __init__(self, url, port=None, ip=None, auto_shutdown=True, wait_time=20, timeout=5, is_playing_fnc=None, video_id=None):

        self.port = port if port else random.randint(8000,8099)
        self.ip = ip if ip else "127.0.0.1"
        self.connected = False
        self.start_time = None
        self.last_connect = None
        self.is_playing_fnc = is_playing_fnc
        self.auto_shutdown =  auto_shutdown
        self.wait_time =  wait_time
        self.timeout =  timeout
        self.running = False
        self.file = None
        self.files = []


        # video_id is the ID in the webpage path
        self._video_id = video_id

        # Get json_data for entire details from video page
        jsonDataStr = httptools.downloadpage('https://streamingcommunityws.com/videos/1/{}'.format(self._video_id), CF=False ).data
        logger.debug( jsonDataStr )
        self._jsonData = jsontools.load( jsonDataStr )

        # going to calculate token and expiration time
        # These values will be used for manifests request
        self._token, self._expires = self.calculateToken( self._jsonData['client_ip'] )

        # Starting web server
        self._server = Server((self.ip, self.port), Handler, client=self)
        self.start()



    def start(self):
        """
        " Starting client and server in a separated thread
        """
        self.start_time = time.time()
        self.running = True
        self._server.run()
        t= Thread(target=self._auto_shutdown)
        t.setDaemon(True)
        t.start()
        logger.info("SC Server Started", (self.ip, self.port))

    def _auto_shutdown(self):
        while self.running:
            time.sleep(1)
            if self.file and self.file.cursor:
                self.last_connect = time.time()

            if self.is_playing_fnc and  self.is_playing_fnc():
                self.last_connect = time.time()

            if self.auto_shutdown:
                #shudown por haber cerrado el reproductor
                if self.connected and self.last_connect and self.is_playing_fnc and not self.is_playing_fnc():
                    if time.time() - self.last_connect - 1 > self.timeout:
                        self.stop()

                #shutdown por no realizar ninguna conexion
                if (not self.file or not self.file.cursor) and self.start_time and self.wait_time and not self.connected:
                    if time.time() - self.start_time - 1 > self.wait_time:
                        self.stop()

                #shutdown tras la ultima conexion
                if (not self.file or not self.file.cursor) and self.timeout and self.connected and self.last_connect and not self.is_playing_fnc:
                    if time.time() - self.last_connect - 1 > self.timeout:
                        self.stop()

    def stop(self):
        self.running = False
        self._server.stop()
        logger.info("SC Server Stopped")


    def get_manifest_url(self):
        # remap request path for main manifest
        # it must point to local server ip:port
        return "http://" + self.ip + ":" + str(self.port) + "/manifest.m3u8"


    def get_main_manifest_content(self):
        # get the manifest file for entire video/audio chunks
        # it must remap each urls in order to catch all chunks

        url = 'https://streamingcommunityws.com/master/{}?token={}&expires={}'.format(self._video_id, self._token, self._expires)

        m3u8_original = httptools.downloadpage(url, CF=False).data

        logger.debug('CLIENT: m3u8:', m3u8_original);

        # remap video/audio manifests url
        # they must point to local server:
        # /video/RES.m3u8
        # /audio/RES.m3u8

        r_video = re.compile(r'(\.\/video\/(\d+p)\/playlist.m3u8)', re.MULTILINE)
        r_audio = re.compile(r'(\.\/audio\/(\d+k)\/playlist.m3u8)', re.MULTILINE)


        for match in r_video.finditer(m3u8_original):
            line = match.groups()[0]
            res = match.groups()[1]
            video_url = "/video/" + res + ".m3u8"

            # logger.info('replace', match.groups(), line, res, video_url)

            m3u8_original = m3u8_original.replace( line, video_url )


        for match in r_audio.finditer(m3u8_original):
            line = match.groups()[0]
            res = match.groups()[1]
            audio_url = "/audio/" + res + ".m3u8"

            # logger.info('replace', match.groups(), line, res, audio_url)

            m3u8_original = m3u8_original.replace( line, audio_url )


        # m_video = re.search(, m3u8_original)
        # self._video_res = m_video.group(1)
        # m_audio = re.search(r'\.\/audio\/(\d+k)\/playlist.m3u8', m3u8_original)
        # self._audio_res = m_audio.group(1)

        # video_url = "/video/" + self._video_res + ".m3u8"
        # audio_url = "/audio/" + self._audio_res + ".m3u8"

        # m3u8_original = m3u8_original.replace( m_video.group(0),  video_url )
        # m3u8_original = m3u8_original.replace( m_audio.group(0),  audio_url )

        return m3u8_original


    def get_video_manifest_content(self, url):
        """
        " Based on `default_start`, `default_count` and `default_domain`
        " this method remap each video chunks url in order to make them point to
        " the remote domain switching from `default_start` to `default_count` values
        """

        m_video = re.search( r'\/video\/(\d+p)\.m3u8', url)
        video_res = m_video.groups()[0]

        logger.info('Video res: ', video_res)

        # get the original manifest file for video chunks
        url = 'https://streamingcommunityws.com/master/{}?token={}&expires={}&type=video&rendition={}'.format(self._video_id, self._token, self._expires, video_res)
        original_manifest = httptools.downloadpage(url, CF=False).data

        manifest_to_parse = original_manifest

        # remap each chunks
        r = re.compile(r'^(\w+\.ts)$', re.MULTILINE)

        default_start = self._jsonData[ "proxies" ]["default_start"]
        default_count = self._jsonData[ "proxies" ]["default_count"]
        default_domain = self._jsonData[ "proxies" ]["default_domain"]
        storage_id = self._jsonData[ "storage_id" ]
        folder_id = self._jsonData[ "folder_id" ]

        for match in r.finditer(manifest_to_parse):
            # getting all single chunks and replace in the original manifest file content
            ts = match.groups()[0]

            # compute final url pointing to given domain
            url = 'https://au-{default_start}.{default_domain}/hls/{storage_id}/{folder_id}/video/{video_res}/{ts}'.format(
                default_start = default_start,
                default_domain = default_domain,
                storage_id = storage_id,
                folder_id = folder_id,
                video_res = video_res,
                ts = ts
            )

            original_manifest = original_manifest.replace( ts, url )

            default_start = default_start + 1
            if default_start > default_count:
                default_start = 1

        # replace the encryption file url pointing to remote streamingcommunity server
        original_manifest = re.sub(r'"(\/.*[enc]?\.key)"', '"https://streamingcommunityws.com\\1"', original_manifest)

        return original_manifest



    def get_audio_manifest_content(self, url):
        """
        " Based on `default_start`, `default_count` and `default_domain`
        " this method remap each video chunks url in order to make them point to
        " the remote domain switching from `default_start` to `default_count` values
        """
        m_audio = re.search( r'\/audio\/(\d+k)\.m3u8', url)
        audio_res = m_audio.groups()[0]

        logger.info('Audio res: ', audio_res)

        # get the original manifest file for video chunks
        url = 'https://streamingcommunityws.com/master/{}?token={}&expires={}&type=audio&rendition={}'.format(self._video_id, self._token, self._expires, audio_res)
        original_manifest = httptools.downloadpage(url, CF=False).data

        manifest_to_parse = original_manifest

        # remap each chunks
        r = re.compile(r'^(\w+\.ts)$', re.MULTILINE)

        default_start = self._jsonData[ "proxies" ]["default_start"]
        default_count = self._jsonData[ "proxies" ]["default_count"]
        default_domain = self._jsonData[ "proxies" ]["default_domain"]
        storage_id = self._jsonData[ "storage_id" ]
        folder_id = self._jsonData[ "folder_id" ]

        for match in r.finditer(manifest_to_parse):
            # getting all single chunks and replace in the original manifest file content
            ts = match.groups()[0]

            # compute final url pointing to given domain
            url = 'https://au-{default_start}.{default_domain}/hls/{storage_id}/{folder_id}/audio/{audio_res}/{ts}'.format(
                default_start = default_start,
                default_domain = default_domain,
                storage_id = storage_id,
                folder_id = folder_id,
                audio_res = audio_res,
                ts = ts
            )

            original_manifest = original_manifest.replace( ts, url )

            default_start = default_start + 1
            if default_start > default_count:
                default_start = 1


        # replace the encryption file url pointing to remote streamingcommunity server
        original_manifest = re.sub(r'"(\/.*[enc]?\.key)"', '"https://streamingcommunityws.com\\1"', original_manifest)

        return original_manifest


    def calculateToken(self, ip):
        """
        " Compute the `token` and the `expires` values in order to perform each next requests
        """

        from time import time
        from base64 import b64encode as b64
        import hashlib
        o = 48

        # NOT USED: it has been computed by `jsondata` in the constructor method
        # n = support.match('https://au-1.scws-content.net/get-ip').data

        i = 'Yc8U6r8KjAKAepEA'
        t = int(time() + (3600 * o))
        l = '{}{} {}'.format(t, ip, i)
        md5 = hashlib.md5(l.encode())
        #s = '?token={}&expires={}'.format(, t)
        token = b64( md5.digest() ).decode().replace( '=', '' ).replace( '+', "-" ).replace( '\\', "_" )
        expires = t
        return token, expires

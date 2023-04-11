# -*- coding: utf-8 -*-

"""
Downloader class
Downloader(url, path [, filename, headers, resume])

  url : string - url to download
  path : string - Directory where the download is saved
  filename : [opt] string - File name to save
  headers : [opt] dict - Headers to use for download
  resume : [opt] bool - continue a previous download if it exists, by default True


metodos:
  start_dialog() Start the download showing the progress
  start() Download starts in the background
  stop(erase = False) Stop the download, with erase = True it deletes the downloaded data

"""
from __future__ import division

import xbmc
from future import standard_library

from core.item import Item

standard_library.install_aliases()
from builtins import range
from builtins import object
from past.utils import old_div
# from builtins import str
import sys
PY3 = False
VFS = True
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import urllib.request, urllib.parse, urllib.error

import mimetypes
import os
import re
import threading
import time

from threading import Thread, Lock

from core import filetools, jsontools
from platformcode import logger, config


class Downloader(object):
    @property
    def state(self):
        return self._state

    @property
    def connections(self):
        return len([c for c in self._download_info["parts"] if c["status"] in [self.states.downloading, self.states.connecting]]), self._max_connections

    @property
    def downloaded(self):
        return self.__change_units__(sum([c["current"] - c["start"] for c in self._download_info["parts"]]))

    @property
    def average_speed(self):
        return self.__change_units__(self._average_speed)

    @property
    def speed(self):
        return self.__change_units__(self._speed)

    @property
    def remaining_time(self):
        if self.speed[0] and self._file_size:
            t = old_div((self.size[0] - self.downloaded[0]), self.speed[0])
        else:
            t = 0

        return time.strftime("%H:%M:%S", time.gmtime(t))

    @property
    def download_url(self):
        return self.url

    @property
    def size(self):
        return self.__change_units__(self._file_size)

    @property
    def progress(self):
        if self._file_size:
            return float(self.downloaded[0]) * 100 / float(self._file_size)
        elif self._state == self.states.completed:
            return 100
        else:
            return 0

    @property
    def filename(self):
        return self._filename

    @property
    def fullpath(self):
        return os.path.abspath(filetools.join(self._path, self._filename))

    # Features
    def start_dialog(self, title=config.get_localized_string(60200)):
        from platformcode import platformtools
        progreso = platformtools.dialog_progress_bg(title, config.get_localized_string(60201))
        try:
            self.start()
            while self.state == self.states.downloading:
                xbmc.sleep(200)
                line1 = "%s" % (self.filename)
                line2 = config.get_localized_string(59983) % ( self.downloaded[1], self.downloaded[2], self.size[1], self.size[2], self.speed[1], self.speed[2], self.connections[0], self.connections[1])
                line3 = config.get_localized_string(60202) % (self.remaining_time)

                progreso.update(int(self.progress), line1 + '\n' + line2 + " " + line3)
                self.__update_json()
        finally:
            progreso.close()

    def start(self):
        self.__update_json(started=False)
        if self._state == self.states.error: return
        conns = []
        for x in range(self._max_connections):
            try:
                conns.append(self.__open_connection__("0", ""))
            except:
                self._max_connections = x
                self._threads = [ Thread(target=self.__start_part__, name="Downloader %s/%s" % (x + 1, self._max_connections)) for x in range(self._max_connections)]
                break
        del conns
        self._start_time = time.time() - 1
        self._state = self.states.downloading
        self._speed_thread.start()
        self._save_thread.start()

        for t in self._threads: t.start()

    def stop(self, erase=False):
        if self._state == self.states.downloading:
            # We stop downloading
            self._state = self.states.stopped
            for t in self._threads:
                if t.is_alive(): t.join()

            if self._save_thread.is_alive(): self._save_thread.join()

            if self._seekable:
                # Guardamos la info al final del archivo
                self.file.seek(0, 2)
                try:
                    offset = self.file.tell()
                except:
                    offset = self.file.seek(0, 1)
                if not PY3:
                    self.file.write(str(self._download_info))
                    self.file.write("%0.16d" % offset)
                else:
                    download_info_dump = jsontools.dump(self._download_info).encode('utf-8')
                    self.file.write(download_info_dump)
                    self.file.write(b"%0.16d" % offset)

        self.file.close()

        if erase: os.remove(filetools.join(self._path, self._filename))

    def __speed_metter__(self):
        self._speed = 0
        self._average_speed = 0

        downloaded = self._start_downloaded
        downloaded2 = self._start_downloaded
        t = time.time()
        t2 = time.time()
        xbmc.sleep(1000)

        while self.state == self.states.downloading:
            self._average_speed = old_div((self.downloaded[0] - self._start_downloaded), (time.time() - self._start_time))
            self._speed = old_div((self.downloaded[0] - self._start_downloaded), (time.time() - self._start_time))
            # self._speed = (self.downloaded[0] - downloaded) / (time.time()  -t)

            if time.time() - t > 5:
                t = t2
                t2 = time.time()
                downloaded2 = self.downloaded[0]

            xbmc.sleep(500)

    # Internal functions
    def __init__(self, url, path, filename=None, headers=[], resume=True, max_connections=10, block_size=2 ** 17,
                 part_size=2 ** 24, max_buffer=10, json_path=None):
        # Parameters
        self._resume = resume
        self._path = path
        self._filename = filename
        self._max_connections = max_connections
        self._block_size = block_size
        self._part_size = part_size
        self._max_buffer = max_buffer
        self._json_path = json_path
        self._json_text = ''
        self._json_item = Item()

        try:
            import xbmc
            self.tmp_path = xbmc.translatePath("special://temp/")
        except:
            self.tmp_path = os.getenv("TEMP") or os.getenv("TMP") or os.getenv("TMPDIR")

        self.states = type('states', (), {"stopped": 0, "connecting": 1, "downloading": 2, "completed": 3, "error": 4, "saving": 5})

        self._state = self.states.stopped
        self._download_lock = Lock()
        self._headers = {"User-Agent": "Kodi/15.2 (Windows NT 10.0; WOW64) App_Bitness/32 Version/15.2-Git:20151019-02e7013"}
        self._speed = 0
        self._buffer = {}
        self._seekable = True

        self._threads = [Thread(target=self.__start_part__, name="Downloader %s/%s" % (x + 1, self._max_connections)) for x in range(self._max_connections)]
        self._speed_thread = Thread(target=self.__speed_metter__, name="Speed Meter")
        self._save_thread = Thread(target=self.__save_file__, name="File Writer")

        # We update the headers
        self._headers.update(dict(headers))

        # We separate the headers from the url
        self.__url_to_headers__(url)

        # We get the server info
        self.__get_download_headers__()

        self._file_size = int(self.response_headers.get("content-length", "0"))

        if not self.response_headers.get("accept-ranges") == "bytes" or self._file_size == 0:
            self._max_connections = 1
            self._part_size = 0
            self._resume = False

        # We get the file name
        self.__get_download_filename__()

        # We open in "a+" mode to create the file if it does not exist, then in "r + b" mode to be able to do seek ()
        self.file = filetools.file_open(filetools.join(self._path, self._filename), "a+", vfs=VFS)
        if self.file: self.file.close()
        self.file = filetools.file_open(filetools.join(self._path, self._filename), "r+b", vfs=VFS)
        if not self.file:
            return

        if self._file_size >= 2 ** 31 or not self._file_size:
            try:
                self.file.seek(2 ** 31, 0)
            except OverflowError:
                self._seekable = False
                logger.error("Cannot do seek() or tell() in files larger than 2GB")

        self.__get_download_info__()

        try:
            logger.info("Download started: Parts: %s | Path: %s | File: %s | Size: %s" % (str(len(self._download_info["parts"])), self._pathencode('utf-8'), self._filenameencode('utf-8'), str(self._download_info["size"])))
        except:
            pass

    def __url_to_headers__(self, url):
        # We separate the url from the additional headers
        self.url = url.split("|")[0]

        # additional headers
        if "|" in url:
            self._headers.update(dict([[header.split("=")[0], urllib.parse.unquote_plus(header.split("=")[1])] for header in url.split("|")[1].split("&")]))

    def __get_download_headers__(self):
        if self.url.startswith("https"):
            try:
                conn = urllib.request.urlopen(urllib.request.Request(self.url.replace("https", "http"), headers=self._headers))
                conn.fp._sock.close()
                self.url = self.url.replace("https", "http")
            except:
                pass

        for x in range(3):
            try:
                if not sys.hexversion > 0x0204FFFF:
                    conn = urllib.request.urlopen(urllib.request.Request(self.url, headers=self._headers))
                    conn.fp._sock.close()
                else:
                    conn = urllib.request.urlopen(urllib.request.Request(self.url, headers=self._headers), timeout=5)

            except:
                self.response_headers = dict()
                self._state = self.states.error
            else:
                self.response_headers = conn.headers
                self._state = self.states.stopped
                break

    def __get_download_filename__(self):
        # We get file name and extension
        if "filename" in self.response_headers.get("content-disposition", "") and "attachment" in self.response_headers.get("content-disposition", ""):
            cd_filename, cd_ext = os.path.splitext(urllib.parse.unquote_plus( re.compile("attachment; filename ?= ?[\"|']?([^\"']+)[\"|']?").match(self.response_headers.get("content-disposition")).group(1)))
        elif "filename" in self.response_headers.get("content-disposition", "") and "inline" in self.response_headers.get("content-disposition", ""):
            cd_filename, cd_ext = os.path.splitext(urllib.parse.unquote_plus(re.compile("inline; filename ?= ?[\"|']?([^\"']+)[\"|']?").match(self.response_headers.get("content-disposition")).group(1)))
        else:
            cd_filename, cd_ext = "", ""

        url_filename, url_ext = os.path.splitext(urllib.parse.unquote_plus(filetools.basename(urllib.parse.urlparse(self.url)[2])))
        if self.response_headers.get("content-type", "application/octet-stream") != "application/octet-stream":
            mime_ext = mimetypes.guess_extension(self.response_headers.get("content-type"))
        else:
            mime_ext = ""

        # We select the most suitable name
        if cd_filename:
            self.remote_filename = cd_filename
            if not self._filename:
                self._filename = cd_filename

        elif url_filename:
            self.remote_filename = url_filename
            if not self._filename:
                self._filename = url_filename

        # We select the most suitable extension
        if cd_ext:
            if not cd_ext in self._filename: self._filename += cd_ext
            if self.remote_filename: self.remote_filename += cd_ext
        elif mime_ext:
            if not mime_ext in self._filename: self._filename += mime_ext
            if self.remote_filename: self.remote_filename += mime_ext
        elif url_ext:
            if not url_ext in self._filename: self._filename += url_ext
            if self.remote_filename: self.remote_filename += url_ext

    def __change_units__(self, value):
        import math
        units = ["B", "KB", "MB", "GB"]
        if value <= 0:
            return 0, 0, units[0]
        else:
            return value, old_div(value, 1024.0 ** int(math.log(value, 1024))), units[int(math.log(value, 1024))]

    def __get_download_info__(self):
        # We continue with a download that contains the info at the end of the file
        self._download_info = {}

        try:
            if not self._resume:
                raise Exception()
            self.file.seek(-16, 2)
            offset = int(self.file.read())
            self.file.seek(offset, 0)
            data = self.file.read()[:-16]
            self._download_info = eval(data)
            if not self._download_info["size"] == self._file_size:
                raise Exception()
            self.file.seek(offset, 0)
            try:
                self.file.truncate()
            except:
                pass

            if not self._seekable:
                for part in self._download_info["parts"]:
                    if part["start"] >= 2 ** 31 and part["status"] == self.states.completed:
                        part["status"] == self.states.stopped
                        part["current"] == part["start"]

            self._start_downloaded = sum([c["current"] - c["start"] for c in self._download_info["parts"]])
            self.pending_parts = set([x for x, a in enumerate(self._download_info["parts"]) if not a["status"] == self.states.completed])
            self.completed_parts = set([x for x, a in enumerate(self._download_info["parts"]) if a["status"] == self.states.completed])
            self.save_parts = set()
            self.download_parts = set()

        # The info does not exist or is not correct, we start from 0
        except:
            self._download_info["parts"] = []
            if self._file_size and self._part_size:
                for x in range(0, self._file_size, self._part_size):
                    end = x + self._part_size - 1
                    if end >= self._file_size: end = self._file_size - 1
                    self._download_info["parts"].append({"start": x, "end": end, "current": x, "status": self.states.stopped})
            else:
                self._download_info["parts"].append({"start": 0, "end": self._file_size - 1, "current": 0, "status": self.states.stopped})

            self._download_info["size"] = self._file_size
            self._start_downloaded = 0
            self.pending_parts = set([x for x in range(len(self._download_info["parts"]))])
            self.completed_parts = set()
            self.save_parts = set()
            self.download_parts = set()

            self.file.seek(0, 0)
            try:
                self.file.truncate()
            except:
                pass

    def __open_connection__(self, start, end):
        headers = self._headers.copy()
        if not end: end = ""
        headers.update({"Range": "bytes=%s-%s" % (start, end)})
        if not sys.hexversion > 0x0204FFFF:
            conn = urllib.request.urlopen(urllib.request.Request(self.url, headers=headers))
        else:
            conn = urllib.request.urlopen(urllib.request.Request(self.url, headers=headers), timeout=5)
        return conn

    def __check_consecutive__(self, id):
        return id == 0 or (len(self.completed_parts) >= id and sorted(self.completed_parts)[id - 1] == id - 1)

    def __save_file__(self):
        logger.info("Thread started: %s" % threading.current_thread().name)

        while self._state == self.states.downloading:
            xbmc.sleep(100)
            if not self.pending_parts and not self.download_parts and not self.save_parts:  # Download finished
                self._state = self.states.completed
                self.file.close()
                continue

            elif not self.save_parts:
                continue

            save_id = min(self.save_parts)

            if not self._seekable and self._download_info["parts"][save_id]["start"] >= 2 ** 31 and not self.__check_consecutive__(save_id):
                continue

            if self._seekable or self._download_info["parts"][save_id]["start"] < 2 ** 31:
                self.file.seek(self._download_info["parts"][save_id]["start"], 0)

            try:
                # file = open(os.path.join(self.tmp_path, self._filename + ".part%s" % save_id), "rb")
                # self.file.write(file.read())
                # file.close()
                # os.remove(os.path.join(self.tmp_path, self._filename + ".part%s" % save_id))
                for a in self._buffer.pop(save_id):
                    self.file.write(a)
                self.save_parts.remove(save_id)
                self.completed_parts.add(save_id)
                self._download_info["parts"][save_id]["status"] = self.states.completed
            except:
                import traceback
                logger.error(traceback.format_exc())
                self._state = self.states.error

        if self.save_parts:
            for s in self.save_parts:
                self._download_info["parts"][s]["status"] = self.states.stopped
                self._download_info["parts"][s]["current"] = self._download_info["parts"][s]["start"]

        logger.info("Thread stopped: %s" % threading.current_thread().name)

    def __get_part_id__(self):
        self._download_lock.acquire()
        if len(self.pending_parts):
            id = min(self.pending_parts)
            self.pending_parts.remove(id)
            self.download_parts.add(id)
            self._download_lock.release()
            return id
        else:
            self._download_lock.release()
            return None

    def __set_part_connecting__(self, id):
        logger.info("ID: %s Establishing connection" % id)
        self._download_info["parts"][id]["status"] = self.states.connecting

    def __set_part__error__(self, id):
        logger.info("ID: %s Download failed" % id)
        self._download_info["parts"][id]["status"] = self.states.error
        self.pending_parts.add(id)
        self.download_parts.remove(id)

    def __set_part__downloading__(self, id):
        logger.info("ID: %s Downloading data ..." % id)
        self._download_info["parts"][id]["status"] = self.states.downloading

    def __set_part_completed__(self, id):
        logger.info("ID: %s Download finished!" % id)
        self._download_info["parts"][id]["status"] = self.states.saving
        self.download_parts.remove(id)
        self.save_parts.add(id)
        while self._state == self.states.downloading and len(self._buffer) > self._max_connections + self._max_buffer:
            xbmc.sleep(100)

    def __set_part_stopped__(self, id):
        if self._download_info["parts"][id]["status"] == self.states.downloading:
            self._download_info["parts"][id]["status"] = self.states.stopped
            self.download_parts.remove(id)
            self.pending_parts.add(id)

    def __open_part_file__(self, id):
        #file = open(os.path.join(self.tmp_path, self._filename + ".part%s" % id), "a+")
        #file = open(os.path.join(self.tmp_path, self._filename + ".part%s" % id), "r+b")
        self.file = filetools.file_open(filetools.join(self.tmp_path, self._filename + ".part%s" % id), "a+", vfs=VFS)
        self.file.close()
        self.file = filetools.file_open(filetools.join(self.tmp_path, self._filename + ".part%s" % id), "r+b", vfs=VFS)
        file.seek(self._download_info["parts"][id]["current"] - self._download_info["parts"][id]["start"], 0)
        return file

    def __start_part__(self):
        logger.info("Thread Started: %s" % threading.current_thread().name)
        while self._state == self.states.downloading:
            id = self.__get_part_id__()
            if id is None: break

            self.__set_part_connecting__(id)

            try:
                connection = self.__open_connection__(self._download_info["parts"][id]["current"], self._download_info["parts"][id]["end"])
            except:
                self.__set_part__error__(id)
                xbmc.sleep(5000)
                continue

            self.__set_part__downloading__(id)
            # file = self.__open_part_file__(id)

            if not id in self._buffer:
                self._buffer[id] = []
            speed = []

            while self._state == self.states.downloading:
                try:
                    start = time.time()
                    buffer = connection.read(self._block_size)
                    speed.append(old_div(len(buffer), ((time.time() - start) or 0.001)))
                except:
                    logger.info("ID: %s Error downloading data" % id)
                    self._download_info["parts"][id]["status"] = self.states.error
                    self.pending_parts.add(id)
                    self.download_parts.remove(id)
                    break
                else:
                    if len(buffer) and self._download_info["parts"][id]["current"] < self._download_info["parts"][id]["end"]:
                        # file.write(buffer)
                        self._buffer[id].append(buffer)
                        self._download_info["parts"][id]["current"] += len(buffer)
                        if len(speed) > 10:
                            velocidad_minima = old_div(old_div(sum(speed), len(speed)), 3)
                            velocidad = speed[-1]
                            vm = self.__change_units__(velocidad_minima)
                            v = self.__change_units__(velocidad)

                            if velocidad_minima > speed[-1] and velocidad_minima > speed[-2] and self._download_info["parts"][id]["current"] < self._download_info["parts"][id]["end"]:
                                if connection.fp: connection.fp._sock.close()
                                logger.info("ID: %s Restarting connection! | Minimum Speed: %.2f %s/s | Speed: %.2f %s/s" % (id, vm[1], vm[2], v[1], v[2]))
                                # file.close()
                                break
                    else:
                        self.__set_part_completed__(id)
                        if connection.fp: connection.fp._sock.close()
                        # file.close()
                        break

            self.__set_part_stopped__(id)
        logger.info("Thread stopped: %s" % threading.current_thread().name)

    def __update_json(self, started=True):
        text = filetools.read(self._json_path)
        # load item only if changed
        if self._json_text != text:
            self._json_text = text
            self._json_item = Item().fromjson(text)
            logger.info('item loaded')
        progress = int(self.progress)
        if started and self._json_item.downloadStatus == 0:  # stopped
            logger.info('Download paused')
            self.stop()
        elif self._json_item.downloadProgress != progress or not started:
            params = {"downloadStatus": 4, "downloadComplete": 0, "downloadProgress": progress}
            self._json_item.__dict__.update(params)
            self._json_text = self._json_item.tojson()
            filetools.write(self._json_path, self._json_text)

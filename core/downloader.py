# -*- coding: utf-8 -*-

"""
Clase Downloader
Downloader(url, path [, filename, headers, resume])

  url : string - url para descargar
  path : string - Directorio donde se guarda la descarga
  filename : [opt] string - Nombre de archivo para guardar
  headers : [opt] dict - Headers para usar en la descarga
  resume : [opt] bool - continuar una descarga previa en caso de existir, por defecto True


metodos:
  start_dialog() Inicia la descarga mostrando el progreso
  start() Inicia la descarga en segundo plano
  stop(erase = False)  Detiene la descarga, con erase = True elimina los datos descargados

"""
import mimetypes
import os
import re
import sys
import threading
import time
import urllib
from threading import Thread, Lock

import urllib2
import urlparse

from core import filetools
from platformcode import logger, config


class Downloader:
    @property
    def state(self):
        return self._state

    @property
    def connections(self):
        return len([c for c in self._download_info["parts"] if
                    c["status"] in [self.states.downloading, self.states.connecting]]), self._max_connections

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
            t = (self.size[0] - self.downloaded[0]) / self.speed[0]
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

    # Funciones
    def start_dialog(self, title=config.get_localized_string(60200)):
        from platformcode import platformtools
        progreso = platformtools.dialog_progress(title, config.get_localized_string(60201))
        self.start()
        while self.state == self.states.downloading and not progreso.iscanceled():
            time.sleep(0.1)
            line1 = "%s" % (self.filename)
            line2 = config.get_localized_string(59983) % (
                self.progress, self.downloaded[1], self.downloaded[2], self.size[1], self.size[2],
                self.speed[1], self.speed[2], self.connections[0], self.connections[1])
            line3 = config.get_localized_string(60202) % (self.remaining_time)

            progreso.update(int(self.progress), line1, line2, line3)
        if self.state == self.states.downloading:
            self.stop()
        progreso.close()

    def start(self):
        if self._state == self.states.error: return
        conns = []
        for x in range(self._max_connections):
            try:
                conns.append(self.__open_connection__("0", ""))
            except:
                self._max_connections = x
                self._threads = [
                    Thread(target=self.__start_part__, name="Downloader %s/%s" % (x + 1, self._max_connections)) for x
                    in range(self._max_connections)]
                break
        del conns
        self._start_time = time.time() - 1
        self._state = self.states.downloading
        self._speed_thread.start()
        self._save_thread.start()

        for t in self._threads: t.start()

    def stop(self, erase=False):
        if self._state == self.states.downloading:
            # Detenemos la descarga
            self._state = self.states.stopped
            for t in self._threads:
                if t.isAlive(): t.join()

            if self._save_thread.isAlive(): self._save_thread.join()

            if self._seekable:
                # Guardamos la info al final del archivo
                self.file.seek(0, 2)
                offset = self.file.tell()
                self.file.write(str(self._download_info))
                self.file.write("%0.16d" % offset)

        self.file.close()

        if erase: os.remove(filetools.join(self._path, self._filename))

    def __speed_metter__(self):
        self._speed = 0
        self._average_speed = 0

        downloaded = self._start_downloaded
        downloaded2 = self._start_downloaded
        t = time.time()
        t2 = time.time()
        time.sleep(1)

        while self.state == self.states.downloading:
            self._average_speed = (self.downloaded[0] - self._start_downloaded) / (time.time() - self._start_time)
            self._speed = (self.downloaded[0] - self._start_downloaded) / (time.time() - self._start_time)
            # self._speed = (self.downloaded[0] - downloaded) / (time.time()  -t)

            if time.time() - t > 5:
                t = t2
                downloaded = downloaded2
                t2 = time.time()
                downloaded2 = self.downloaded[0]

            time.sleep(0.5)

    # Funciones internas
    def __init__(self, url, path, filename=None, headers=[], resume=True, max_connections=10, block_size=2 ** 17,
                 part_size=2 ** 24, max_buffer=10):
        # Parametros
        self._resume = resume
        self._path = path
        self._filename = filename
        self._max_connections = max_connections
        self._block_size = block_size
        self._part_size = part_size
        self._max_buffer = max_buffer

        try:
            import xbmc
            self.tmp_path = xbmc.translatePath("special://temp/")
        except:
            self.tmp_path = os.getenv("TEMP") or os.getenv("TMP") or os.getenv("TMPDIR")

        self.states = type('states', (),
                           {"stopped": 0, "connecting": 1, "downloading": 2, "completed": 3, "error": 4, "saving": 5})

        self._state = self.states.stopped
        self._download_lock = Lock()
        self._headers = {
            "User-Agent": "Kodi/15.2 (Windows NT 10.0; WOW64) App_Bitness/32 Version/15.2-Git:20151019-02e7013"}
        self._speed = 0
        self._buffer = {}
        self._seekable = True

        self._threads = [Thread(target=self.__start_part__, name="Downloader %s/%s" % (x + 1, self._max_connections))
                         for x in range(self._max_connections)]
        self._speed_thread = Thread(target=self.__speed_metter__, name="Speed Meter")
        self._save_thread = Thread(target=self.__save_file__, name="File Writer")

        # Actualizamos los headers
        self._headers.update(dict(headers))

        # Separamos los headers de la url
        self.__url_to_headers__(url)

        # Obtenemos la info del servidor
        self.__get_download_headers__()

        self._file_size = int(self.response_headers.get("content-length", "0"))

        if not self.response_headers.get("accept-ranges") == "bytes" or self._file_size == 0:
            self._max_connections = 1
            self._part_size = 0
            self._resume = False

        # Obtenemos el nombre del archivo
        self.__get_download_filename__()

        # Abrimos en modo "a+" para que cree el archivo si no existe, luego en modo "r+b" para poder hacer seek()
        self.file = filetools.file_open(filetools.join(self._path, self._filename), "a+")
        self.file = filetools.file_open(filetools.join(self._path, self._filename), "r+b")

        if self._file_size >= 2 ** 31 or not self._file_size:
            try:
                self.file.seek(2 ** 31)
            except OverflowError:
                self._seekable = False
                logger.info("No se puede hacer seek() ni tell() en ficheros mayores de 2GB")

        self.__get_download_info__()

        logger.info("Descarga inicializada: Partes: %s | Ruta: %s | Archivo: %s | Tamaño: %s" % (
        len(self._download_info["parts"]), self._path, self._filename, self._download_info["size"]))

    def __url_to_headers__(self, url):
        # Separamos la url de los headers adicionales
        self.url = url.split("|")[0]

        # headers adicionales
        if "|" in url:
            self._headers.update(dict([[header.split("=")[0], urllib.unquote_plus(header.split("=")[1])] for header in
                                       url.split("|")[1].split("&")]))

    def __get_download_headers__(self):
        if self.url.startswith("https"):
            try:
                conn = urllib2.urlopen(urllib2.Request(self.url.replace("https", "http"), headers=self._headers))
                conn.fp._sock.close()
                self.url = self.url.replace("https", "http")
            except:
                pass

        for x in range(3):
            try:
                if not sys.hexversion > 0x0204FFFF:
                    conn = urllib2.urlopen(urllib2.Request(self.url, headers=self._headers))
                    conn.fp._sock.close()
                else:
                    conn = urllib2.urlopen(urllib2.Request(self.url, headers=self._headers), timeout=5)

            except:
                self.response_headers = dict()
                self._state = self.states.error
            else:
                self.response_headers = conn.headers.dict
                self._state = self.states.stopped
                break

    def __get_download_filename__(self):
        # Obtenemos nombre de archivo y extension
        if "filename" in self.response_headers.get("content-disposition",
                                                   "") and "attachment" in self.response_headers.get(
                "content-disposition", ""):
            cd_filename, cd_ext = os.path.splitext(urllib.unquote_plus(
                re.compile("attachment; filename ?= ?[\"|']?([^\"']+)[\"|']?").match(
                    self.response_headers.get("content-disposition")).group(1)))
        if "filename" in self.response_headers.get("content-disposition", "") and "inline" in self.response_headers.get(
                "content-disposition", ""):
            cd_filename, cd_ext = os.path.splitext(urllib.unquote_plus(
                re.compile("inline; filename ?= ?[\"|']?([^\"']+)[\"|']?").match(
                    self.response_headers.get("content-disposition")).group(1)))
        else:
            cd_filename, cd_ext = "", ""

        url_filename, url_ext = os.path.splitext(
            urllib.unquote_plus(filetools.basename(urlparse.urlparse(self.url)[2])))
        if self.response_headers.get("content-type", "application/octet-stream") <> "application/octet-stream":
            mime_ext = mimetypes.guess_extension(self.response_headers.get("content-type"))
        else:
            mime_ext = ""

        # Seleccionamos el nombre mas adecuado
        if cd_filename:
            self.remote_filename = cd_filename
            if not self._filename:
                self._filename = cd_filename

        elif url_filename:
            self.remote_filename = url_filename
            if not self._filename:
                self._filename = url_filename

        # Seleccionamos la extension mas adecuada
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
            return value, value / 1024.0 ** int(math.log(value, 1024)), units[int(math.log(value, 1024))]

    def __get_download_info__(self):
        # Continuamos con una descarga que contiene la info al final del archivo
        self._download_info = {}

        try:
            if not self._resume:
                raise Exception()
            self.file.seek(-16, 2)
            offset = int(self.file.read())
            self.file.seek(offset)
            data = self.file.read()[:-16]
            self._download_info = eval(data)
            if not self._download_info["size"] == self._file_size:
                raise Exception()
            self.file.seek(offset)
            self.file.truncate()

            if not self._seekable:
                for part in self._download_info["parts"]:
                    if part["start"] >= 2 ** 31 and part["status"] == self.states.completed:
                        part["status"] == self.states.stopped
                        part["current"] == part["start"]

            self._start_downloaded = sum([c["current"] - c["start"] for c in self._download_info["parts"]])
            self.pending_parts = set(
                [x for x, a in enumerate(self._download_info["parts"]) if not a["status"] == self.states.completed])
            self.completed_parts = set(
                [x for x, a in enumerate(self._download_info["parts"]) if a["status"] == self.states.completed])
            self.save_parts = set()
            self.download_parts = set()

        # La info no existe o no es correcta, comenzamos de 0
        except:
            self._download_info["parts"] = []
            if self._file_size and self._part_size:
                for x in range(0, self._file_size, self._part_size):
                    end = x + self._part_size - 1
                    if end >= self._file_size: end = self._file_size - 1
                    self._download_info["parts"].append(
                        {"start": x, "end": end, "current": x, "status": self.states.stopped})
            else:
                self._download_info["parts"].append(
                    {"start": 0, "end": self._file_size - 1, "current": 0, "status": self.states.stopped})

            self._download_info["size"] = self._file_size
            self._start_downloaded = 0
            self.pending_parts = set([x for x in range(len(self._download_info["parts"]))])
            self.completed_parts = set()
            self.save_parts = set()
            self.download_parts = set()

            self.file.seek(0)
            self.file.truncate()

    def __open_connection__(self, start, end):
        headers = self._headers.copy()
        if not end: end = ""
        headers.update({"Range": "bytes=%s-%s" % (start, end)})
        if not sys.hexversion > 0x0204FFFF:
            conn = urllib2.urlopen(urllib2.Request(self.url, headers=headers))
        else:
            conn = urllib2.urlopen(urllib2.Request(self.url, headers=headers), timeout=5)
        return conn

    def __check_consecutive__(self, id):
        return id == 0 or (len(self.completed_parts) >= id and sorted(self.completed_parts)[id - 1] == id - 1)

    def __save_file__(self):
        logger.info("Thread iniciado: %s" % threading.current_thread().name)

        while self._state == self.states.downloading:
            if not self.pending_parts and not self.download_parts and not self.save_parts:  # Descarga finalizada
                self._state = self.states.completed
                self.file.close()
                continue

            elif not self.save_parts:
                continue

            save_id = min(self.save_parts)

            if not self._seekable and self._download_info["parts"][save_id][
                "start"] >= 2 ** 31 and not self.__check_consecutive__(save_id):
                continue

            if self._seekable or self._download_info["parts"][save_id]["start"] < 2 ** 31:
                self.file.seek(self._download_info["parts"][save_id]["start"])

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

        logger.info("Thread detenido: %s" % threading.current_thread().name)

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
        logger.info("ID: %s Estableciendo conexión" % id)
        self._download_info["parts"][id]["status"] = self.states.connecting

    def __set_part__error__(self, id):
        logger.info("ID: %s Error al descargar" % id)
        self._download_info["parts"][id]["status"] = self.states.error
        self.pending_parts.add(id)
        self.download_parts.remove(id)

    def __set_part__downloading__(self, id):
        logger.info("ID: %s Descargando datos..." % id)
        self._download_info["parts"][id]["status"] = self.states.downloading

    def __set_part_completed__(self, id):
        logger.info("ID: %s ¡Descarga finalizada!" % id)
        self._download_info["parts"][id]["status"] = self.states.saving
        self.download_parts.remove(id)
        self.save_parts.add(id)
        while self._state == self.states.downloading and len(self._buffer) > self._max_connections + self._max_buffer:
            time.sleep(0.1)

    def __set_part_stopped__(self, id):
        if self._download_info["parts"][id]["status"] == self.states.downloading:
            self._download_info["parts"][id]["status"] = self.states.stopped
            self.download_parts.remove(id)
            self.pending_parts.add(id)

    def __open_part_file__(self, id):
        file = open(os.path.join(self.tmp_path, self._filename + ".part%s" % id), "a+")
        file = open(os.path.join(self.tmp_path, self._filename + ".part%s" % id), "r+b")
        file.seek(self._download_info["parts"][id]["current"] - self._download_info["parts"][id]["start"])
        return file

    def __start_part__(self):
        logger.info("Thread Iniciado: %s" % threading.current_thread().name)
        while self._state == self.states.downloading:
            id = self.__get_part_id__()
            if id is None: break

            self.__set_part_connecting__(id)

            try:
                connection = self.__open_connection__(self._download_info["parts"][id]["current"],
                                                      self._download_info["parts"][id]["end"])
            except:
                self.__set_part__error__(id)
                time.sleep(5)
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
                    speed.append(len(buffer) / ((time.time() - start) or 0.001))
                except:
                    logger.info("ID: %s Error al descargar los datos" % id)
                    self._download_info["parts"][id]["status"] = self.states.error
                    self.pending_parts.add(id)
                    self.download_parts.remove(id)
                    break
                else:
                    if len(buffer) and self._download_info["parts"][id]["current"] < self._download_info["parts"][id][
                        "end"]:
                        # file.write(buffer)
                        self._buffer[id].append(buffer)
                        self._download_info["parts"][id]["current"] += len(buffer)
                        if len(speed) > 10:
                            velocidad_minima = sum(speed) / len(speed) / 3
                            velocidad = speed[-1]
                            vm = self.__change_units__(velocidad_minima)
                            v = self.__change_units__(velocidad)

                            if velocidad_minima > speed[-1] and velocidad_minima > speed[-2] and \
                                            self._download_info["parts"][id]["current"] < \
                                            self._download_info["parts"][id]["end"]:
                                connection.fp._sock.close()
                                logger.info(
                                    "ID: %s ¡Reiniciando conexión! | Velocidad minima: %.2f %s/s | Velocidad: %.2f %s/s" % \
                                    (id, vm[1], vm[2], v[1], v[2]))
                                # file.close()
                                break
                    else:
                        self.__set_part_completed__(id)
                        connection.fp._sock.close()
                        # file.close()
                        break

            self.__set_part_stopped__(id)
        logger.info("Thread detenido: %s" % threading.current_thread().name)

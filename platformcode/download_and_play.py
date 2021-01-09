# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Download and play
# ------------------------------------------------------------
# Based on code from the Mega add-on (xbmchub.com)
# ---------------------------------------------------------------------------

from __future__ import division
from future import standard_library
standard_library.install_aliases()
#from builtins import str
from past.utils import old_div
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import urllib.request, urllib.parse, urllib.error, os, re, socket, threading, time, xbmc, xbmcgui
from core import downloadtools
from platformcode import config, logger


# Download a file and start playing while downloading
def download_and_play(url, file_name, download_path):
    # Start thread
    logger.info("Active threads " + str(threading.active_count()))
    logger.info("" + repr(threading.enumerate()))
    logger.info("Starting download thread...")
    download_thread = DownloadThread(url, file_name, download_path)
    download_thread.start()
    logger.info("Download thread started")
    logger.info("Active threads " + str(threading.active_count()))
    logger.info("" + repr(threading.enumerate()))

    # Wait
    logger.info("Waiting...")

    while True:
        cancelled = False
        dialog = xbmcgui.DialogProgress()
        dialog.create(config.get_localized_string(60200), config.get_localized_string(60312))
        dialog.update(0)

        while not cancelled and download_thread.is_alive():
            dialog.update(download_thread.get_progress(), config.get_localized_string(60313) + '\n' +
                          config.get_localized_string(60314) + str(int(old_div(download_thread.get_speed(), 1024))) + " KB/s " + str(
                              download_thread.get_actual_size()) + config.get_localized_string(60316) + str( download_thread.get_total_size()) + "MB",
                          config.get_localized_string(60202) % (str(downloadtools.sec_to_hms(download_thread.get_remaining_time()))))
            xbmc.sleep(1000)

            if dialog.iscanceled():
                cancelled = True
                break

        dialog.close()

        logger.info("End of waiting")

        # Launch the player
        player = CustomPlayer()
        player.set_download_thread(download_thread)
        player.PlayStream(download_thread.get_file_name())

        # End of playback
        logger.info("End of playback")

        if player.is_stopped():
            logger.info("Terminated by user")
            break
        else:
            if not download_thread.is_alive():
                logger.info("Download has finished")
                break
            else:
                logger.info("Continua la descarga")

    # When the player finishes, if you continue downloading it for now
    logger.info("Download thread alive=" + str(download_thread.is_alive()))
    if download_thread.is_alive():
        logger.info("Killing download thread")
        download_thread.force_stop()


class CustomPlayer(xbmc.Player):
    def __init__(self, *args, **kwargs):
        logger.info()
        self.actualtime = 0
        self.totaltime = 0
        self.stopped = False
        xbmc.Player.__init__(self)

    def PlayStream(self, url):
        logger.info("url=" + url)
        self.play(url)
        self.actualtime = 0
        self.url = url
        while self.isPlaying():
            self.actualtime = self.getTime()
            self.totaltime = self.getTotalTime()
            logger.info("actualtime=" + str(self.actualtime) + " totaltime=" + str(self.totaltime))
            xbmc.sleep(3000)

    def set_download_thread(self, download_thread):
        logger.info()
        self.download_thread = download_thread

    def force_stop_download_thread(self):
        logger.info()

        if self.download_thread.is_alive():
            logger.info("Killing download thread")
            self.download_thread.force_stop()

            # while self.download_thread.is_alive():
            #    xbmc.sleep(1000)

    def onPlayBackStarted(self):
        logger.info("PLAYBACK STARTED")

    def onPlayBackEnded(self):
        logger.info("PLAYBACK ENDED")

    def onPlayBackStopped(self):
        logger.info("PLAYBACK STOPPED")
        self.stopped = True
        self.force_stop_download_thread()

    def is_stopped(self):
        return self.stopped


# Download in background
class DownloadThread(threading.Thread):
    def __init__(self, url, file_name, download_path):
        # logger.info(repr(file))
        self.url = url
        self.download_path = download_path
        self.file_name = os.path.join(download_path, file_name)
        self.progress = 0
        self.force_stop_file_name = os.path.join(self.download_path, "force_stop.tmp")
        self.velocidad = 0
        self.tiempofalta = 0
        self.actual_size = 0
        self.total_size = 0

        if os.path.exists(self.force_stop_file_name):
            os.remove(self.force_stop_file_name)

        threading.Thread.__init__(self)

    def run(self):
        logger.info("Download starts...")

        if "megacrypter.com" in self.url:
            self.download_file_megacrypter()
        else:
            self.download_file()
        logger.info("Download ends")

    def force_stop(self):
        logger.info()
        force_stop_file = open(self.force_stop_file_name, "w")
        force_stop_file.write("0")
        force_stop_file.close()

    def get_progress(self):
        return self.progress

    def get_file_name(self):
        return self.file_name

    def get_speed(self):
        return self.velocidad

    def get_remaining_time(self):
        return self.tiempofalta

    def get_actual_size(self):
        return self.actual_size

    def get_total_size(self):
        return self.total_size

    def download_file_megacrypter(self):
        logger.info()

        comando = "./megacrypter.sh"
        logger.info("command= " + comando)

        oldcwd = os.getcwd()
        logger.info("oldcwd= " + oldcwd)

        cwd = os.path.join(config.get_runtime_path(), "tools")
        logger.info("cwd= " + cwd)
        os.chdir(cwd)
        logger.info("directory changed to= " + os.getcwd())

        logger.info("destination= " + self.download_path)

        os.system(comando + " '" + self.url + "' \"" + self.download_path + "\"")
        # p = subprocess.Popen([comando , self.url , self.download_path], cwd=cwd, stdout=subprocess.PIPE , stderr=subprocess.PIPE )
        # out, err = p.communicate()
        # logger.info("DownloadThread.download_file out="+out)

        os.chdir(oldcwd)

    def download_file(self):
        logger.info("Direct download")

        headers = []

        # Ensures that the file can be created
        logger.info("filename= " + self.file_name)
        self.file_name = xbmc.makeLegalFilename(self.file_name)
        logger.info("filename= " + self.file_name)
        logger.info("url= " + self.url)

        # Create the file
        existSize = 0
        f = open(self.file_name, 'wb')
        grabado = 0

        # Interpret headers in a URL like in XBMC
        if "|" in self.url:
            additional_headers = self.url.split("|")[1]
            if "&" in additional_headers:
                additional_headers = additional_headers.split("&")
            else:
                additional_headers = [additional_headers]

            for additional_header in additional_headers:
                logger.info("additional_header: " + additional_header)
                name = re.findall("(.*?)=.*?", additional_header)[0]
                value = urllib.parse.unquote_plus(re.findall(".*?=(.*?)$", additional_header)[0])
                headers.append([name, value])

            self.url = self.url.split("|")[0]
            logger.info("url= " + self.url)

        # Timeout del socket a 60 segundos
        socket.setdefaulttimeout(60)

        # Crea la petición y añade las cabeceras
        h = urllib.request.HTTPHandler(debuglevel=0)
        request = urllib.request.Request(self.url)
        for header in headers:
            logger.info("Header= " + header[0] + ": " + header[1])
            request.add_header(header[0], header[1])

        # Lanza la petición
        opener = urllib.request.build_opener(h)
        urllib.request.install_opener(opener)
        try:
            connexion = opener.open(request)
        except urllib.error.HTTPError as e:
            logger.error("error %d (%s) opening url %s" % (e.code, e.msg, self.url))
            # print e.code
            # print e.msg
            # print e.hdrs
            # print e.fp
            f.close()

            # Error 416 is that the requested range is greater than the file => is that it is already complete
            if e.code == 416:
                return 0
            else:
                return -2

        try:
            totalfichero = int(connexion.headers["Content-Length"])
        except:
            totalfichero = 1

        self.total_size = int(float(totalfichero) / float(1024 * 1024))

        logger.info("Content-Length=%s" % totalfichero)
        blocksize = 100 * 1024

        bloqueleido = connexion.read(blocksize)
        logger.info("Starting file download, blocked= %s" % len(bloqueleido))

        maxreintentos = 10

        while len(bloqueleido) > 0:
            try:
                if os.path.exists(self.force_stop_file_name):
                    logger.info("Force_stop file detected, download is interrupted")
                    f.close()

                    xbmc.executebuiltin("Notification(%s,%s,300)" % (config.get_localized_string(60319),config.get_localized_string(60320)))

                    return

                # Write the block read
                # try:
                #    import xbmcvfs
                #    f.write( bloqueleido )
                # except:
                f.write(bloqueleido)
                grabado = grabado + len(bloqueleido)
                logger.info("grabado=%d de %d" % (grabado, totalfichero))
                percent = int(float(grabado) * 100 / float(totalfichero))
                self.progress = percent
                totalmb = float(float(totalfichero) / (1024 * 1024))
                descargadosmb = float(float(grabado) / (1024 * 1024))
                self.actual_size = int(descargadosmb)

                #Read the next block, retrying not to stop everything at the first timeout
                reintentos = 0
                while reintentos <= maxreintentos:
                    try:

                        before = time.time()
                        bloqueleido = connexion.read(blocksize)
                        after = time.time()
                        if (after - before) > 0:
                            self.velocidad = old_div(len(bloqueleido), ((after - before)))
                            falta = totalfichero - grabado
                            if self.velocidad > 0:
                                self.tiempofalta = old_div(falta, self.velocidad)
                            else:
                                self.tiempofalta = 0
                        break
                    except:
                        import sys
                        reintentos = reintentos + 1
                        logger.info("ERROR in block download, retry %d" % reintentos)
                        for line in sys.exc_info():
                            logger.error("%s" % line)

                # There was an error in the download
                if reintentos > maxreintentos:
                    logger.error("ERROR in the file download")
                    f.close()

                    return -2

            except:
                import traceback, sys
                from pprint import pprint
                exc_type, exc_value, exc_tb = sys.exc_info()
                lines = traceback.format_exception(exc_type, exc_value, exc_tb)
                for line in lines:
                    line_splits = line.split("\n")
                    for line_split in line_splits:
                        logger.error(line_split)

                f.close()
                return -2

        return

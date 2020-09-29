# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# Download Tools - Original based from code of VideoMonkey XBMC Plugin
# ---------------------------------------------------------------------------------

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
#from builtins import str
from past.utils import old_div
import sys
PY3 = False
VFS = True
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int; VFS = False

import urllib.request, urllib.parse, urllib.error

import re
import socket
import time

from platformcode import config, logger
from core import filetools

entitydefs2 = {
    '$': '%24',
    '&': '%26',
    '+': '%2B',
    ',': '%2C',
    '/': '%2F',
    ':': '%3A',
    ';': '%3B',
    '=': '%3D',
    '?': '%3F',
    '@': '%40',
    ' ': '%20',
    '"': '%22',
    '<': '%3C',
    '>': '%3E',
    '#': '%23',
    '%': '%25',
    '{': '%7B',
    '}': '%7D',
    '|': '%7C',
    '\\': '%5C',
    '^': '%5E',
    '~': '%7E',
    '[': '%5B',
    ']': '%5D',
    '`': '%60'
}

entitydefs3 = {
    u'ÂÁÀÄÃÅ': u'A',
    u'âáàäãå': u'a',
    u'ÔÓÒÖÕ': u'O',
    u'ôóòöõðø': u'o',
    u'ÛÚÙÜ': u'U',
    u'ûúùüµ': u'u',
    u'ÊÉÈË': u'E',
    u'êéèë': u'e',
    u'ÎÍÌÏ': u'I',
    u'îìíï': u'i',
    u'ñ': u'n',
    u'ß': u'B',
    u'÷': u'%',
    u'ç': u'c',
    u'æ': u'ae'
}


def limpia_nombre_caracteres_especiales(s):
    if not s:
        return ''
    badchars = '\\/:*?\"<>|'
    for c in badchars:
        s = s.replace(c, '')
        return s


def limpia_nombre_sin_acentos(s):
    if not s:
        return ''
    for key, value in entitydefs3.items():
        for c in key:
            s = s.replace(c, value)
            return s


def limpia_nombre_excepto_1(s):
    if not s:
        return ''
    # Entrance title
    # Convert to unicode
    try:
        s = unicode(s, "utf-8")
    except UnicodeError:
        # logger.info("no es utf-8")
        try:
            s = unicode(s, "iso-8859-1")
        except UnicodeError:
            # logger.info("no es iso-8859-1")
            pass
    # Remove accents
    s = limpia_nombre_sin_acentos(s)
    # Remove prohibited characters
    validchars = " ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890!#$%&'()-@[]^_`{}~."
    stripped = ''.join(c for c in s if c in validchars)
    # Convert to iso
    s = stripped.encode("iso-8859-1")
    if PY3:
        s = s.decode('utf-8')
    return s


def limpia_nombre_excepto_2(s):
    if not s:
        return ''
    validchars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890."
    stripped = ''.join(c for c in s if c in validchars)
    return stripped


def getfilefromtitle(url, title):
    # Print in the log what you will discard
    logger.info("title=" + title)
    logger.info("url=" + url)
    plataforma = config.get_system_platform()
    logger.info("platform=" + plataforma)

    # filename = xbmc.makeLegalFilename(title + url[-4:])
    from core import scrapertools

    nombrefichero = title + scrapertools.get_filename_from_url(url)[-4:]
    logger.info("filename= %s" % nombrefichero)
    if "videobb" in url or "videozer" in url or "putlocker" in url:
        nombrefichero = title + ".flv"
    if "videobam" in url:
        nombrefichero = title + "." + url.rsplit(".", 1)[1][0:3]

    logger.info("filename= %s" % nombrefichero)

    nombrefichero = limpia_nombre_caracteres_especiales(nombrefichero)

    logger.info("filename= %s" % nombrefichero)

    fullpath = filetools.join(config.get_setting("downloadpath"), nombrefichero)
    logger.info("fullpath= %s" % fullpath)

    if config.is_xbmc() and fullpath.startswith("special://"):
        import xbmc
        fullpath = xbmc.translatePath(fullpath)

    return fullpath


def downloadtitle(url, title):
    fullpath = getfilefromtitle(url, title)
    return downloadfile(url, fullpath)


def downloadbest(video_urls, title, continuar=False):
    logger.info()

    # Flip it over, to put the highest quality one first (list () is for you to make a copy of)
    invertida = list(video_urls)
    invertida.reverse()

    for elemento in invertida:
        # videotitle = elemento[0]
        url = elemento[1]
        if not PY3:
            logger.info("Downloading option " + title + " " + url.encode('ascii', 'ignore'))
        else:
            logger.info("Downloading option " + title + " " + url.encode('ascii', 'ignore').decode('utf-8'))

        # Calculate the file where you should record
        try:
            fullpath = getfilefromtitle(url, title.strip())
        # If it fails, it is because the URL is useless
        except:
            import traceback
            logger.error(traceback.format_exc())
            continue

        # Descarga
        try:
            ret = downloadfile(url, fullpath, continuar=continuar)
        # At this point, it is usually a timeout.
        except urllib.error.URLError as e:
            import traceback
            logger.error(traceback.format_exc())
            ret = -2

        # The user has canceled the download
        if ret == -1:
            return -1
        else:
            # EThe file doesn't even exist
            if not filetools.exists(fullpath):
                logger.info("-> You have not downloaded anything, testing with the following option if there is")
            # The file exists
            else:
                tamanyo = filetools.getsize(fullpath)

                # It has size 0
                if tamanyo == 0:
                    logger.info("-> Download a file with size 0, testing with the following option if it exists")
                    os.remove(fullpath)
                else:
                    logger.info("-> Download a file with size %d, he takes it for good" % tamanyo)
                    return 0

    return -2


def downloadfile(url, nombrefichero, headers=None, silent=False, continuar=False, resumir=True, header=''):
    logger.info("url= " + url)
    logger.info("filename= " + nombrefichero)

    if headers is None:
        headers = []
    if not header:
        header = "plugin"

    progreso = None

    if config.is_xbmc() and nombrefichero.startswith("special://"):
        import xbmc
        nombrefichero = xbmc.translatePath(nombrefichero)

    try:
        # If it is not XBMC, always "Silent"
        from platformcode import platformtools

        # before
        # f=open(nombrefichero,"wb")
        try:
            import xbmc
            nombrefichero = xbmc.makeLegalFilename(nombrefichero)
        except:
            pass
        logger.info("filename= " + nombrefichero)

        # The file exists and you want to continue
        if filetools.exists(nombrefichero) and continuar:
            f = filetools.file_open(nombrefichero, 'r+b', vfs=VFS)
            if resumir:
                exist_size = filetools.getsize(nombrefichero)
                logger.info("the file exists, size= %d" % exist_size)
                grabado = exist_size
                f.seek(exist_size)
            else:
                exist_size = 0
                grabado = 0

        # the file already exists and you don't want to continue, it aborts
        elif filetools.exists(nombrefichero) and not continuar:
            logger.info("the file exists, it does not download again")
            return -3

        # the file does not exist
        else:
            exist_size = 0
            logger.info("the file does not exist")

            f = filetools.file_open(nombrefichero, 'wb', vfs=VFS)
            grabado = 0

        # Create the progress dialog
        if not silent:
            progreso = platformtools.dialog_progress(header, "Downloading..." + '\n' + url + '\n' + nombrefichero)

        # If the platform does not return a valid dialog box, it assumes silent mode
        if progreso is None:
            silent = True

        if "|" in url:
            additional_headers = url.split("|")[1]
            if "&" in additional_headers:
                additional_headers = additional_headers.split("&")
            else:
                additional_headers = [additional_headers]

            for additional_header in additional_headers:
                logger.info("additional_header: " + additional_header)
                name = re.findall("(.*?)=.*?", additional_header)[0]
                value = urllib.parse.unquote_plus(re.findall(".*?=(.*?)$", additional_header)[0])
                headers.append([name, value])

            url = url.split("|")[0]
            logger.info("url=" + url)

        # Socket timeout at 60 seconds
        socket.setdefaulttimeout(60)

        h = urllib.request.HTTPHandler(debuglevel=0)
        request = urllib.request.Request(url)
        for header in headers:
            logger.info("Header= " + header[0] + ": " + header[1])
            request.add_header(header[0], header[1])

        if exist_size > 0:
            request.add_header('Range', 'bytes= %d-' % (exist_size,))

        opener = urllib.request.build_opener(h)
        urllib.request.install_opener(opener)
        try:
            connexion = opener.open(request)
        except urllib.error.HTTPError as e:
            logger.error("error %d (%s) opening url %s" % (e.code, e.msg, url))
            f.close()
            if not silent:
                progreso.close()
            # Error 416 is that the requested range is greater than the file => is that it is already complete
            if e.code == 416:
                return 0
            else:
                return -2

        try:
            totalfichero = int(connexion.headers["Content-Length"])
        except ValueError:
            totalfichero = 1

        if exist_size > 0:
            totalfichero = totalfichero + exist_size

        logger.info("Content-Length= %s" % totalfichero)

        blocksize = 100 * 1024

        bloqueleido = connexion.read(blocksize)
        logger.info("Starting downloading the file, blocked= %s" % len(bloqueleido))

        maxreintentos = 10

        while len(bloqueleido) > 0:
            try:
                # Write the block read
                f.write(bloqueleido)
                grabado += len(bloqueleido)
                percent = int(float(grabado) * 100 / float(totalfichero))
                totalmb = float(float(totalfichero) / (1024 * 1024))
                descargadosmb = float(float(grabado) / (1024 * 1024))

                # Read the next block, retrying not to stop everything at the first timeout
                reintentos = 0
                while reintentos <= maxreintentos:
                    try:
                        before = time.time()
                        bloqueleido = connexion.read(blocksize)
                        after = time.time()
                        if (after - before) > 0:
                            velocidad = old_div(len(bloqueleido), (after - before))
                            falta = totalfichero - grabado
                            if velocidad > 0:
                                tiempofalta = old_div(falta, velocidad)
                            else:
                                tiempofalta = 0
                            # logger.info(sec_to_hms(tiempofalta))
                            if not silent:
                                progreso.update(percent, "%.2fMB/%.2fMB (%d%%) %.2f Kb/s %s" %
                                                (descargadosmb, totalmb, percent, old_div(velocidad, 1024),
                                                 sec_to_hms(tiempofalta)))
                        break
                    except:
                        reintentos += 1
                        logger.info("ERROR in block download, retry %d" % reintentos)
                        import traceback
                        logger.error(traceback.print_exc())

                # The user cancels the download
                try:
                    if progreso.iscanceled():
                        logger.info("Download of file canceled")
                        f.close()
                        progreso.close()
                        return -1
                except:
                    pass

                # There was an error in the download
                if reintentos > maxreintentos:
                    logger.info("ERROR in the file download")
                    f.close()
                    if not silent:
                        progreso.close()

                    return -2

            except:
                import traceback
                logger.error(traceback.print_exc())

                f.close()
                if not silent:
                    progreso.close()

                # platformtools.dialog_ok('Error al descargar' , 'Se ha producido un error' , 'al descargar el archivo')

                return -2

    except:
        if url.startswith("rtmp"):
            error = downloadfileRTMP(url, nombrefichero, silent)
            if error and not silent:
                from platformcode import platformtools
            platformtools.dialog_ok("You cannot download that video "," RTMP downloads not yet supported")
        else:
            import traceback
            from pprint import pprint
            exc_type, exc_value, exc_tb = sys.exc_info()
            lines = traceback.format_exception(exc_type, exc_value, exc_tb)
            for line in lines:
                line_splits = line.split("\n")
                for line_split in line_splits:
                    logger.error(line_split)

    try:
        f.close()
    except:
        pass

    if not silent:
        try:
            progreso.close()
        except:
            pass

    logger.info("End of file download")


def downloadfileRTMP(url, nombrefichero, silent):
    ''' 
    Do not use librtmp as it is not always available.
    Launch a thread with rtmpdump. In Windows it is necessary to install it.
    It doesn't use threads so it doesn't show any progress bar nor the actual end of the download is marked in the log info.
    '''
    Programfiles = os.getenv('Programfiles')
    if Programfiles:  # Windows
        rtmpdump_cmd = Programfiles + "/rtmpdump/rtmpdump.exe"
        nombrefichero = '"' + nombrefichero + '"'  # Windows needs the quotes in the name
    else:
        rtmpdump_cmd = "/usr/bin/rtmpdump"

    if not filetools.isfile(rtmpdump_cmd) and not silent:
        from platformcode import platformtools
        advertencia = platformtools.dialog_ok("Lack " + rtmpdump_cmd, "Check that rtmpdump is installed")
        return True

    valid_rtmpdump_options = ["help", "url", "rtmp", "host", "port", "socks", "protocol", "playpath", "playlist",
                              "swfUrl", "tcUrl", "pageUrl", "app", "swfhash", "swfsize", "swfVfy", "swfAge", "auth",
                              "conn", "flashVer", "live", "subscribe", "realtime", "flv", "resume", "timeout", "start",
                              "stop", "token", "jtv", "hashes", "buffer", "skip", "quiet", "verbose",
                              "debug"]  # for rtmpdump 2.4

    url_args = url.split(' ')
    rtmp_url = url_args[0]
    rtmp_args = url_args[1:]

    rtmpdump_args = ["--rtmp", rtmp_url]
    for arg in rtmp_args:
        n = arg.find('=')
        if n < 0:
            if arg not in valid_rtmpdump_options:
                continue
            rtmpdump_args += ["--" + arg]
        else:
            if arg[:n] not in valid_rtmpdump_options:
                continue
            rtmpdump_args += ["--" + arg[:n], arg[n + 1:]]

    try:
        rtmpdump_args = [rtmpdump_cmd] + rtmpdump_args + ["-o", nombrefichero]
        from os import spawnv, P_NOWAIT
        logger.info("Initiating file download: %s" % " ".join(rtmpdump_args))
        rtmpdump_exit = spawnv(P_NOWAIT, rtmpdump_cmd, rtmpdump_args)
        if not silent:
            from platformcode import platformtools
            advertencia = platformtools.dialog_ok("RTMP download option is experimental", "and the video will download in the background. \n No progress bar will be displayed.")
    except:
        return True

    return


def downloadfileGzipped(url, pathfichero):
    logger.info("url= " + url)
    nombrefichero = pathfichero
    logger.info("filename= " + nombrefichero)

    import xbmc
    nombrefichero = xbmc.makeLegalFilename(nombrefichero)
    logger.info("filename= " + nombrefichero)
    patron = "(http://[^/]+)/.+"
    matches = re.compile(patron, re.DOTALL).findall(url)

    if len(matches):
        logger.info("Main URL: " + matches[0])
        url1 = matches[0]
    else:
        url1 = url

    txheaders = {
        'User-Agent': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; SLCC1; .NET CLR 2.0.50727; '
                      'Media Center PC 5.0; .NET CLR 3.0.04506)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'es-es,es;q=0.8,en-us;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip,deflate',
        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
        'Keep-Alive': '115',
        'Connection': 'keep-alive',
        'Referer': url1,
    }

    txdata = ""

    # Create the progress dialog
    from platformcode import platformtools
    progreso = platformtools.dialog_progress("addon", config.get_localized_string(60200) + '\n' + url.split("|")[0] + '\n' + nombrefichero)

    # Socket timeout at 60 seconds
    socket.setdefaulttimeout(10)

    h = urllib.request.HTTPHandler(debuglevel=0)
    request = urllib.request.Request(url, txdata, txheaders)
    # if existSize > 0:
    #    request.add_header('Range', 'bytes=%d-' % (existSize, ))

    opener = urllib.request.build_opener(h)
    urllib.request.install_opener(opener)
    try:
        connexion = opener.open(request)
    except urllib.error.HTTPError as e:
        logger.error("error %d (%s) when opening the url %s" %
                     (e.code, e.msg, url))
        progreso.close()
        # Error 416 is that the requested range is greater than the file => is that it is already complete
        if e.code == 416:
            return 0
        else:
            return -2

    nombre_fichero_base = filetools.basename(nombrefichero)
    if len(nombre_fichero_base) == 0:
        logger.info("Searching for name in the answer Headers")
        nombre_base = connexion.headers["Content-Disposition"]
        logger.info(nombre_base)
        patron = 'filename="([^"]+)"'
        matches = re.compile(patron, re.DOTALL).findall(nombre_base)
        if len(matches) > 0:
            titulo = matches[0]
            titulo = GetTitleFromFile(titulo)
            nombrefichero = filetools.join(pathfichero, titulo)
        else:
            logger.info("Name of the file not found, Placing temporary name: no_name.txt")
            titulo = "no_name.txt"
            nombrefichero = filetools.join(pathfichero, titulo)
    totalfichero = int(connexion.headers["Content-Length"])

    # then
    f = filetools.file_open(nombrefichero, 'w', vfs=VFS)

    logger.info("new file open")

    grabado = 0
    logger.info("Content-Length= %s" % totalfichero)

    blocksize = 100 * 1024

    bloqueleido = connexion.read(blocksize)

    try:
        import io
        compressedstream = io.StringIO(bloqueleido)
        import gzip
        gzipper = gzip.GzipFile(fileobj=compressedstream)
        bloquedata = gzipper.read()
        gzipper.close()
        logger.info("Starting downloading the file, blocked= %s" % len(bloqueleido))
    except:
        logger.error("ERROR: The file to be downloaded is not compressed with Gzip")
        f.close()
        progreso.close()
        return -2

    maxreintentos = 10

    while len(bloqueleido) > 0:
        try:
            # Write the block read
            f.write(bloquedata)
            grabado += len(bloqueleido)
            percent = int(float(grabado) * 100 / float(totalfichero))
            totalmb = float(float(totalfichero) / (1024 * 1024))
            descargadosmb = float(float(grabado) / (1024 * 1024))

            # Read the next block, retrying not to stop everything at the first timeout
            reintentos = 0
            while reintentos <= maxreintentos:
                try:
                    before = time.time()
                    bloqueleido = connexion.read(blocksize)

                    import gzip
                    import io
                    compressedstream = io.StringIO(bloqueleido)
                    gzipper = gzip.GzipFile(fileobj=compressedstream)
                    bloquedata = gzipper.read()
                    gzipper.close()
                    after = time.time()
                    if (after - before) > 0:
                        velocidad = old_div(len(bloqueleido), (after - before))
                        falta = totalfichero - grabado
                        if velocidad > 0:
                            tiempofalta = old_div(falta, velocidad)
                        else:
                            tiempofalta = 0
                        logger.info(sec_to_hms(tiempofalta))
                        progreso.update(percent, "%.2fMB/%.2fMB (%d%%) %.2f Kb/s %s left " % (descargadosmb, totalmb, percent, old_div(velocidad, 1024), sec_to_hms(tiempofalta)))
                    break
                except:
                    reintentos += 1
                    logger.info("ERROR in block download, retry %d" % reintentos)
                    for line in sys.exc_info():
                        logger.error("%s" % line)

            # The user cancels the download
            if progreso.iscanceled():
                logger.info("Download of file canceled")
                f.close()
                progreso.close()
                return -1

            # There was an error in the download
            if reintentos > maxreintentos:
                logger.info("ERROR in the file download")
                f.close()
                progreso.close()

                return -2

        except:
            logger.info("ERROR in the file download")
            for line in sys.exc_info():
                logger.error("%s" % line)
            f.close()
            progreso.close()

            return -2
    f.close()

    # print data
    progreso.close()
    logger.info("End download of the file")
    return nombrefichero


def GetTitleFromFile(title):
    # Print in the log what you will discard
    logger.info("title= " + title)
    plataforma = config.get_system_platform()
    logger.info("plataform= " + plataforma)

    # nombrefichero = xbmc.makeLegalFilename(title + url[-4:])
    nombrefichero = title
    return nombrefichero


def sec_to_hms(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return "%02d:%02d:%02d" % (h, m, s)


def downloadIfNotModifiedSince(url, timestamp):
    logger.info("(" + url + "," + time.ctime(timestamp) + ")")

    # Convert date to GMT
    fecha_formateada = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime(timestamp))
    logger.info("Formatted date= %s" % fecha_formateada)

    # Check if it has changed
    inicio = time.clock()
    req = urllib.request.Request(url)
    req.add_header('If-Modified-Since', fecha_formateada)
    req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; es-ES; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12')

    updated = False

    try:
        response = urllib.request.urlopen(req)
        data = response.read()

        # If it gets this far, it has changed
        updated = True
        response.close()

    except urllib.error.URLError as e:
        # If it returns 304 it is that it has not changed
        if hasattr(e, 'code'):
            logger.info("HTTP response code : %d" % e.code)
            if e.code == 304:
                logger.info("It has not changed")
                updated = False
        # Grab errors with response code from requested external server
        else:
            for line in sys.exc_info():
                logger.error("%s" % line)
        data = ""

    fin = time.clock()
    logger.info("Downloaded in %d seconds " % (fin - inicio + 1))

    return updated, data


def download_all_episodes(item, channel, first_episode="", preferred_server="vidspot", filter_language=""):
    logger.info("show= " + item.show)
    show_title = item.show

    # Gets the listing from which it was called
    action = item.extra

    # This mark is because the item has something else apart in the "extra" attribute
    if "###" in item.extra:
        action = item.extra.split("###")[0]
        item.extra = item.extra.split("###")[1]

    episode_itemlist = getattr(channel, action)(item)

    # Sort episodes for the first_episode filter to work
    episode_itemlist = sorted(episode_itemlist, key=lambda it: it.title)

    from core import servertools
    from core import scrapertools

    best_server = preferred_server
    # worst_server = "moevideos"

    # For each episode
    if first_episode == "":
        empezar = True
    else:
        empezar = False

    for episode_item in episode_itemlist:
        try:
            logger.info("episode= " + episode_item.title)
            episode_title = scrapertools.find_single_match(episode_item.title, r"(\d+x\d+)")
            logger.info("episode= " + episode_title)
        except:
            import traceback
            logger.error(traceback.format_exc())
            continue

        if first_episode != "" and episode_title == first_episode:
            empezar = True

        if episodio_ya_descargado(show_title, episode_title):
            continue

        if not empezar:
            continue

        # Extract the mirrors
        try:
            mirrors_itemlist = channel.findvideos(episode_item)
        except:
            mirrors_itemlist = servertools.find_video_items(episode_item)
        print(mirrors_itemlist)

        descargado = False

        new_mirror_itemlist_1 = []
        new_mirror_itemlist_2 = []
        new_mirror_itemlist_3 = []
        new_mirror_itemlist_4 = []
        new_mirror_itemlist_5 = []
        new_mirror_itemlist_6 = []

        for mirror_item in mirrors_itemlist:

            # If it is in Spanish it goes to the beginning, if it does not go to the end
            if "(Italiano)" in mirror_item.title:
                if best_server in mirror_item.title.lower():
                    new_mirror_itemlist_1.append(mirror_item)
                else:
                    new_mirror_itemlist_2.append(mirror_item)
            if "(Español)" in mirror_item.title:
                if best_server in mirror_item.title.lower():
                    new_mirror_itemlist_1.append(mirror_item)
                else:
                    new_mirror_itemlist_2.append(mirror_item)
            elif "(Latino)" in mirror_item.title:
                if best_server in mirror_item.title.lower():
                    new_mirror_itemlist_3.append(mirror_item)
                else:
                    new_mirror_itemlist_4.append(mirror_item)
            elif "(VOS)" in mirror_item.title:
                if best_server in mirror_item.title.lower():
                    new_mirror_itemlist_3.append(mirror_item)
                else:
                    new_mirror_itemlist_4.append(mirror_item)
            else:
                if best_server in mirror_item.title.lower():
                    new_mirror_itemlist_5.append(mirror_item)
                else:
                    new_mirror_itemlist_6.append(mirror_item)

        mirrors_itemlist = (new_mirror_itemlist_1 + new_mirror_itemlist_2 + new_mirror_itemlist_3 +
                            new_mirror_itemlist_4 + new_mirror_itemlist_5 + new_mirror_itemlist_6)

        for mirror_item in mirrors_itemlist:
            logger.info("mirror= " + mirror_item.title)

            if "(Italiano)" in mirror_item.title:
                idioma = "(Italiano)"
                codigo_idioma = "it"
            if "(Español)" in mirror_item.title:
                idioma = "(Español)"
                codigo_idioma = "es"
            elif "(Latino)" in mirror_item.title:
                idioma = "(Latino)"
                codigo_idioma = "lat"
            elif "(VOS)" in mirror_item.title:
                idioma = "(VOS)"
                codigo_idioma = "vos"
            elif "(VO)" in mirror_item.title:
                idioma = "(VO)"
                codigo_idioma = "vo"
            else:
                idioma = "(Desconocido)"
                codigo_idioma = "desconocido"

            logger.info("filter_language=#" + filter_language + "#, codigo_idioma=#" + codigo_idioma + "#")
            if filter_language == "" or (filter_language != "" and filter_language == codigo_idioma):
                logger.info("downloading mirror")
            else:
                logger.info("language " + codigo_idioma + " filtered, skipping")
                continue

            if hasattr(channel, 'play'):
                video_items = channel.play(mirror_item)
            else:
                video_items = [mirror_item]

            if len(video_items) > 0:
                video_item = video_items[0]

                # Check that it is available
                video_urls, puedes, motivo = servertools.resolve_video_urls_for_playing(video_item.server, video_item.url, video_password="", muestra_dialogo=False)

                # Adds it to the download list
                if puedes:
                    logger.info("downloading mirror started...")
                    # The highest quality video is the latest
                    # mediaurl = video_urls[len(video_urls) - 1][1]
                    devuelve = downloadbest(video_urls, show_title + " " + episode_title + " " + idioma +
                                            " [" + video_item.server + "]", continuar=False)

                    if devuelve == 0:
                        logger.info("download ok")
                        descargado = True
                        break
                    elif devuelve == -1:
                        try:
                            from platformcode import platformtools
                            platformtools.dialog_ok("plugin", "Descarga abortada")
                        except:
                            pass
                        return
                    else:
                        logger.info("download error, try another mirror")
                        continue

                else:
                    logger.info("downloading mirror not available... trying next")

        if not descargado:
            logger.info("UNDOWNLOADED EPISODE " + episode_title)


def episodio_ya_descargado(show_title, episode_title):
    from core import scrapertools
    ficheros = filetools.listdir(".")

    for fichero in ficheros:
        # logger.info("fichero="+fichero)
        if fichero.lower().startswith(show_title.lower()) and scrapertools.find_single_match(fichero, "(\d+x\d+)") == episode_title:
            logger.info("found!")
            return True

    return False

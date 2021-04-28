# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# filetools
# File management with xbmcvfs / samba / local discrimination
# ------------------------------------------------------------

from __future__ import division
# from builtins import str
import io

from past.utils import old_div
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import os
import traceback

from core import scrapertools
from platformcode import platformtools, logger

xbmc_vfs = True                                                 # False to disable XbmcVFS, True to enable
if xbmc_vfs:
    try:
        import xbmcvfs
        if not PY3:
            reload(sys)                                         # Workoround. Review on migration to Python 3
            sys.setdefaultencoding('utf-8')                     # xbmcvfs demeans the value of defaultencoding. It is reestablished
        xbmc_vfs = True
    except:
        xbmc_vfs = False

samba = None
if not xbmc_vfs:
    try:
        from lib.sambatools import libsmb as samba
    except:
        samba = None
        # Python 2.4 Not compatible with samba module, you have to check
# Windows is "mbcs" linux, osx, android is "utf8"
if os.name == "nt":
    fs_encoding = ""
else:
    fs_encoding = "utf8"

# per android è necessario, su kodi 18, usare FileIO
# https://forum.kodi.tv/showthread.php?tid=330124
# per xbox invece, è necessario usare open perchè _io è rotto :(
# https://github.com/jellyfin/jellyfin-kodi/issues/115#issuecomment-538811017
fileIo = platformtools.xbmc.getCondVisibility('system.platform.linux') and platformtools.xbmc.getCondVisibility('system.platform.android')


def validate_path(path):
    """
    Eliminate illegal characters
    @param path: string to validate
    @type path: str
    @rtype: str
    @return: returns the string without the characters not allowed
    """
    chars = ":*?<>|"
    if scrapertools.find_single_match(path, r'(^\w+:\/\/)'):
        protocolo = scrapertools.find_single_match(path, r'(^\w+:\/\/)')
        import re
        parts = re.split(r'^\w+:\/\/(.+?)/(.+)', path)[1:3]
        return protocolo + parts[0] + "/" + ''.join([c for c in parts[1] if c not in chars])

    else:
        if path.find(":\\") == 1:
            unidad = path[0:3]
            path = path[2:]
        else:
            unidad = ""

        return unidad + ''.join([c for c in path if c not in chars])


def encode(path, _samba=False):
    """
    It encodes a path according to the operating system we are using.
    The path argument has to be encoded in utf-8
    @type unicode or str path with utf-8 encoding
    @param path parameter to encode
    @type _samba bool
    @para _samba if the path is samba or not
    @rtype: str
    @return path encoded in system character set or utf-8 if samba
    """
    if not isinstance(path, unicode):
        path = unicode(path, "utf-8", "ignore")

    if not PY3:
        if scrapertools.find_single_match(path, r'(^\w+:\/\/)') or _samba:
            path = path.encode("utf-8", "ignore")
        else:
            if fs_encoding:
                path = path.encode(fs_encoding, "ignore")

    # if PY3 and isinstance(path, bytes):
    #     if fs_encoding:
    #         path = path.decode(fs_encoding)
    #     else:
    #         path = path.decode()

    return path


def decode(path):
    """
    Converts a text string to the utf-8 character set
    removing characters that are not allowed in utf-8
    @type: str, unicode, list of str o unicode
    @param path:can be a path or a list () with multiple paths
    @rtype: str
    @return: ruta encoded in UTF-8
    """
    if isinstance(path, list):
        for x in range(len(path)):
            if not isinstance(path[x], unicode):
                path[x] = path[x].decode(fs_encoding, "ignore")
            path[x] = path[x].encode("utf-8", "ignore")
    else:
        if not isinstance(path, unicode):
            path = path.decode(fs_encoding, "ignore")
        path = path.encode("utf-8", "ignore")
    return path


def read(path, linea_inicio=0, total_lineas=None, whence=0, silent=False, vfs=True):
    """
    Read the contents of a file and return the data
    @param path: file path
    @type path: str
    @param linea_inicio: first line to read from the file
    @type linea_inicio: positive int
    @param total_lineas: maximum number of lines to read. If it is None or greater than the total lines, the file will be read until the end.
    @type total_lineas: positive int
    @rtype: str
    @return: data contained in the file
    """
    path = encode(path)
    try:
        if not isinstance(linea_inicio, int):
            try:
                linea_inicio = int(linea_inicio)
            except:
                logger.error('Read: Start_line ERROR: %s' % str(linea_inicio))
                linea_inicio = 0
        if total_lineas != None and not isinstance(total_lineas, int):
            try:
                total_lineas = int(total_lineas)
            except:
                logger.error('Read: ERROR of total_lineas: %s' % str(total_lineas))
                total_lineas = None
        if xbmc_vfs and vfs:
            if not exists(path): return False
            f = xbmcvfs.File(path, "r")
            data = f.read()

            if total_lineas == None:
                total_lineas = 9999999999
            if linea_inicio > 0:
                if not isinstance(whence, int):
                    try:
                        whence = int(whence)
                    except:
                        return False
                data = '\n'.join(data.split('\n')[linea_inicio:total_lineas])

            return data
        elif path.lower().startswith("smb://"):
            f = samba.smb_open(path, "rb")
        else:
            f = open(path, "rb")

        data = []
        for x, line in enumerate(f):
            if x < linea_inicio: continue
            if len(data) == total_lineas: break
            data.append(line)
        f.close()
    except:
        if not silent:
            logger.error("ERROR reading file: %s" % path)
            logger.error(traceback.format_exc())
        return False

    else:
        if not PY3:
            return unicode("".join(data))
        else:
            return unicode(b"".join(data))


def write(path, data, mode="w", silent=False, vfs=True):
    """
    Save the data to a file
    @param path: file path to save
    @type path: str
    @param data: data to save
    @type data: str
    @rtype: bool
    @return: returns True if it was written correctly or False if it gave an error
    """
    path = encode(path)
    try:
        if xbmc_vfs and vfs:
            f = xbmcvfs.File(path, mode)
            result = f.write(data)
            f.close()
            return bool(result)
        elif path.lower().startswith("smb://"):
            f = samba.smb_open(path, mode)
        else:
            f = open(path, mode)

        f.write(data)
        f.close()
    except:
        logger.error("ERROR saving file: %s" % path)
        if not silent:
            logger.error(traceback.format_exc())
        return False
    else:
        return True


def file_open(path, mode="r", silent=False, vfs=True):
    """
    Open a file
    @param path: path
    @type path: str
    @rtype: str
    @return: file object
    """
    path = encode(path)
    try:
        if xbmc_vfs and vfs:
            if 'r' in mode and '+' in mode:
                mode = mode.replace('r', 'w').replace('+', '')
                logger.debug('Open MODE changed to: %s' % mode)
            if 'a' in mode:
                mode = mode.replace('a', 'w').replace('+', '')
                logger.debug('Open MODE changed to: %s' % mode)
            return xbmcvfs.File(path, mode)
        elif path.lower().startswith("smb://"):
            return samba.smb_open(path, mode)
        else:
            if fileIo:
                return io.FileIO(path, mode)
            else:
                # return io.open(path, mode, decode='utf-8')
                return open(path, mode)
    except:
        logger.error("ERROR when opening file: %s, %s" % (path, mode))
        if not silent:
            logger.error(traceback.format_exc())
            platformtools.dialog_notification("Error Opening", path)
        return False


def file_stat(path, silent=False, vfs=True):
    """
    Stat of a file
    @param path: path
    @type path: str
    @rtype: str
    @return: file object
    """
    path = encode(path)
    try:
        if xbmc_vfs and vfs:
            if not exists(path): return False
            return xbmcvfs.Stat(path)
        raise
    except:
        logger.error("File_Stat not supported: %s" % path)
        if not silent:
            logger.error(traceback.format_exc())
        return False


def rename(path, new_name, silent=False, strict=False, vfs=True):
    """
    Rename a file or folder
    @param path: path of the file or folder to rename
    @type path: str
    @param new_name: new name
    @type new_name: str
    @rtype: bool
    @return: returns False on error
    """
    path = encode(path)
    try:
        if xbmc_vfs and vfs:
            path_end = path
            if path_end.endswith('/') or path_end.endswith('\\'):
                path_end = path_end[:-1]
            dest = encode(join(dirname(path_end), new_name))
            result = xbmcvfs.rename(path, dest)
            if not result and not strict:
                logger.error("ERROR RENAME file: %s. Copying and deleting" % path)
                if not silent:
                    dialogo = platformtools.dialog_progress("Copying file", "")
                result = xbmcvfs.copy(path, dest)
                if not result:
                    return False
                xbmcvfs.delete(path)
            return bool(result)
        elif path.lower().startswith("smb://"):
            new_name = encode(new_name, True)
            samba.rename(path, join(dirname(path), new_name))
        else:
            new_name = encode(new_name, False)
            os.rename(path, os.path.join(os.path.dirname(path), new_name))
    except:
        logger.error("ERROR when renaming the file: %s" % path)
        if not silent:
            logger.error(traceback.format_exc())
            platformtools.dialog_notification("Error renaming", path)
        return False
    else:
        return True


def move(path, dest, silent=False, strict=False, vfs=True):
    """
    Move a file
    @param path: path of the file to move
    @type path: str
    @param dest: path where to move
    @type dest: str
    @rtype: bool
    @return: returns False on error
    """
    try:
        if xbmc_vfs and vfs:
            if not exists(path): return False
            path = encode(path)
            dest = encode(dest)
            result = xbmcvfs.rename(path, dest)
            if not result and not strict:
                logger.error("ERROR when MOVING the file: %s. Copying and deleting" % path)
                if not silent:
                    dialogo = platformtools.dialog_progress("Copying file", "")
                result = xbmcvfs.copy(path, dest)
                if not result:
                    return False
                xbmcvfs.delete(path)
            return bool(result)
        # samba/samba
        elif path.lower().startswith("smb://") and dest.lower().startswith("smb://"):
            dest = encode(dest, True)
            path = encode(path, True)
            samba.rename(path, dest)

        # local/local
        elif not path.lower().startswith("smb://") and not dest.lower().startswith("smb://"):
            dest = encode(dest)
            path = encode(path)
            os.rename(path, dest)
        # mixed In this case the file is copied and then the source file is deleted
        else:
            if not silent:
                dialogo = platformtools.dialog_progress("Copying file", "")
            return copy(path, dest) == True and remove(path) == True
    except:
        logger.error("ERROR when moving file: %s to %s" % (path, dest))
        if not silent:
            logger.error(traceback.format_exc())
        return False
    else:
        return True


def copy(path, dest, silent=False, vfs=True):
    """
    Copy a file
    @param path: path of the file to copy
    @type path: str
    @param dest: path to copy
    @type dest: str
    @param silent: the dialog box is displayed or not
    @type silent: bool
    @rtype: bool
    @return: returns False on error
    """
    try:
        if xbmc_vfs and vfs:
            path = encode(path)
            dest = encode(dest)
            if not silent:
                dialogo = platformtools.dialog_progress("Copying file", "")
            return bool(xbmcvfs.copy(path, dest))

        fo = file_open(path, "rb")
        fd = file_open(dest, "wb")
        if fo and fd:
            if not silent:
                dialogo = platformtools.dialog_progress("Copying file", "")
            size = getsize(path)
            copiado = 0
            while True:
                if not silent:
                    dialogo.update(old_div(copiado * 100, size), basename(path))
                buf = fo.read(1024 * 1024)
                if not buf:
                    break
                if not silent and dialogo.iscanceled():
                    dialogo.close()
                    return False
                fd.write(buf)
                copiado += len(buf)
            if not silent:
                dialogo.close()
    except:
        logger.error("ERROR when copying the file: %s" % path)
        if not silent:
            logger.error(traceback.format_exc())
        return False
    else:
        return True


def exists(path, silent=False, vfs=True):
    """
    Check if there is a folder or file
    @param path: path
    @type path: str
    @rtype: bool
    @return: Returns True if the path exists, whether it is a folder or a file
    """
    path = encode(path)
    try:
        if xbmc_vfs and vfs:
            result = bool(xbmcvfs.exists(path))
            if not result and not path.endswith('/') and not path.endswith('\\'):
                result = bool(xbmcvfs.exists(join(path, ' ').rstrip()))
            return result
        elif path.lower().startswith("smb://"):
            return samba.exists(path)
        else:
            return os.path.exists(path)
    except:
        logger.error("ERROR when checking the path: %s" % path)
        if not silent:
            logger.error(traceback.format_exc())
        return False


def isfile(path, silent=False, vfs=True):
    """
    Check if the path is a file
    @param path: path
    @type path: str
    @rtype: bool
    @return: Returns True if the path exists and is a file
    """
    path = encode(path)
    try:
        if xbmc_vfs and vfs:
            if not scrapertools.find_single_match(path, r'(^\w+:\/\/)'):
                return os.path.isfile(path)
            if path.endswith('/') or path.endswith('\\'):
                path = path[:-1]
            dirs, files = xbmcvfs.listdir(dirname(path))
            base_name = basename(path)
            for file in files:
                if base_name == file:
                    return True
            return False
        elif path.lower().startswith("smb://"):
            return samba.isfile(path)
        else:
            return os.path.isfile(path)
    except:
        logger.error("ERROR when checking file: %s" % path)
        if not silent:
            logger.error(traceback.format_exc())
        return False


def isdir(path, silent=False, vfs=True):
    """
    Check if the path is a directory
    @param path: path
    @type path: str
    @rtype: bool
    @return: Returns True if the path exists and is a directory
    """
    path = encode(path)
    try:
        if xbmc_vfs and vfs:
            if not scrapertools.find_single_match(path, r'(^\w+:\/\/)'):
                return os.path.isdir(path)
            if path.endswith('/') or path.endswith('\\'):
                path = path[:-1]
            dirs, files = xbmcvfs.listdir(dirname(path))
            base_name = basename(path)
            for dir in dirs:
                if base_name == dir:
                    return True
            return False
        elif path.lower().startswith("smb://"):
            return samba.isdir(path)
        else:
            return os.path.isdir(path)
    except:
        logger.error("ERROR when checking the directory: %s" % path)
        if not silent:
            logger.error(traceback.format_exc())
        return False


def getsize(path, silent=False, vfs=True):
    """
    Gets the size of a file
    @param path: file path
    @type path: str
    @rtype: str
    @return: file size
    """
    path = encode(path)
    try:
        if xbmc_vfs and vfs:
            if not exists(path): return long(0)
            f = xbmcvfs.File(path)
            s = f.size()
            f.close()
            return s
        elif path.lower().startswith("smb://"):
            return long(samba.get_attributes(path).file_size)
        else:
            return os.path.getsize(path)
    except:
        logger.error("ERROR when getting the size: %s" % path)
        if not silent:
            logger.error(traceback.format_exc())
        return long(0)


def remove(path, silent=False, vfs=True):
    """
    Delete a file
    @param path: path of the file to delete
    @type path: str
    @rtype: bool
    @return: returns False on error
    """
    path = encode(path)
    try:
        if xbmc_vfs and vfs:
            return bool(xbmcvfs.delete(path))
        elif path.lower().startswith("smb://"):
            samba.remove(path)
        else:
            os.remove(path)
    except:
        logger.error("ERROR deleting file: %s" % path)
        if not silent:
            logger.error(traceback.format_exc())
            platformtools.dialog_notification("ERROR deleting file", path)
        return False
    else:
        return True


def rmdirtree(path, silent=False, vfs=True):
    """
    Delete a directory and its contents
    @param path: path to remove
    @type path: str
    @rtype: bool
    @return: returns False on error
    """
    path = encode(path)
    try:
        if xbmc_vfs and vfs:
            if not exists(path): return True
            if not path.endswith('/') and not path.endswith('\\'):
                path = join(path, ' ').rstrip()
            for raiz, subcarpetas, ficheros in walk(path, topdown=False):
                for f in ficheros:
                    xbmcvfs.delete(join(raiz, f))
                for s in subcarpetas:
                    xbmcvfs.rmdir(join(raiz, s))
            xbmcvfs.rmdir(path)
        elif path.lower().startswith("smb://"):
            for raiz, subcarpetas, ficheros in samba.walk(path, topdown=False):
                for f in ficheros:
                    samba.remove(join(decode(raiz), decode(f)))
                for s in subcarpetas:
                    samba.rmdir(join(decode(raiz), decode(s)))
            samba.rmdir(path)
        else:
            import shutil
            shutil.rmtree(path, ignore_errors=True)
    except:
        logger.error("ERROR deleting directory: %s" % path)
        if not silent:
            logger.error(traceback.format_exc())
            platformtools.dialog_notification("ERROR deleting directory", path)
        return False
    else:
        return not exists(path)


def rmdir(path, silent=False, vfs=True):
    """
    Delete a directory
    @param path: path to remove
    @type path: str
    @rtype: bool
    @return: returns False on error
    """
    path = encode(path)
    try:
        if xbmc_vfs and vfs:
            if not path.endswith('/') and not path.endswith('\\'):
                path = join(path, ' ').rstrip()
            return bool(xbmcvfs.rmdir(path))
        elif path.lower().startswith("smb://"):
            samba.rmdir(path)
        else:
            os.rmdir(path)
    except:
        logger.error("ERROR deleting directory: %s" % path)
        if not silent:
            logger.error(traceback.format_exc())
            platformtools.dialog_notification("ERROR deleting directory", path)
        return False
    else:
        return True


def mkdir(path, silent=False, vfs=True):
    """
    Create a directory
    @param path: path to create
    @type path: str
    @rtype: bool
    @return: returns False on error
    """
    path = encode(path)
    try:
        if xbmc_vfs and vfs:
            if not path.endswith('/') and not path.endswith('\\'):
                path = join(path, ' ').rstrip()
            result = bool(xbmcvfs.mkdirs(path))
            if not result:
                import time
                time.sleep(0.1)
                result = exists(path)
            return result
        elif path.lower().startswith("smb://"):
            samba.mkdir(path)
        else:
            os.mkdir(path)
    except:
        logger.error("ERROR when creating directory: %s" % path)
        if not silent:
            logger.error(traceback.format_exc())
            platformtools.dialog_notification("ERROR when creating directory", path)
        return False
    else:
        return True


def walk(top, topdown=True, onerror=None, vfs=True):
    """
    List a directory recursively
    @param top: Directory to list, must be a str "UTF-8"
    @type top: str
    @param topdown: scanned from top to bottom
    @type topdown: bool
    @param onerror: show error to continue listing if you have something set but raise an exception
    @type onerror: bool
    ***The followlinks parameter, which by default is True, is not used here, since in samba it does not discriminate links
    """
    top = encode(top)
    if xbmc_vfs and vfs:
        for a, b, c in walk_vfs(top, topdown, onerror):
            # list (b) is for you to make a copy of the directory listing
            # if it doesn't give error when you have to recursively enter directories with special characters
            yield a, list(b), c
    elif top.lower().startswith("smb://"):
        for a, b, c in samba.walk(top, topdown, onerror):
            # list (b) is for you to make a copy of the directory listing
            # if it doesn't give error when you have to recursively enter directories with special characters
            yield decode(a), decode(list(b)), decode(c)
    else:
        for a, b, c in os.walk(top, topdown, onerror):
            # list (b) is for you to make a copy of the directory listing
            # if it doesn't give error when you have to recursively enter directories with special characters
            yield decode(a), decode(list(b)), decode(c)


def walk_vfs(top, topdown=True, onerror=None):
    """
    List a directory recursively
    Since xmbcvfs does not have this function, the logic of libsmb (samba) is copied to carry out the pre-Walk
    """
    top = encode(top)
    dirs, nondirs = xbmcvfs.listdir(top)

    if topdown:
        yield top, dirs, nondirs

    for name in dirs:
        if isinstance(name, unicode):
            name = name.encode("utf8")
            if PY3: name = name.decode("utf8")
        elif PY3 and isinstance(name, bytes):
            name = name.decode("utf8")
        elif not PY3:
            name = unicode(name, "utf8")
        new_path = "/".join(top.split("/") + [name])
        for x in walk_vfs(new_path, topdown, onerror):
            yield x
    if not topdown:
        yield top, dirs, nondirs


def listdir(path, silent=False, vfs=True):
    """
    List a directory
    @param path: Directory to list, must be a str "UTF-8"
    @type path: str
    @rtype: str
    @return: content of a directory
    """

    path = encode(path)
    try:
        if xbmc_vfs and vfs:
            dirs, files = xbmcvfs.listdir(path)
            return dirs + files
        elif path.lower().startswith("smb://"):
            return decode(samba.listdir(path))
        else:
            return decode(os.listdir(path))
    except:
        logger.error("ERROR when reading the directory: %s" % path)
        if not silent:
            logger.error(traceback.format_exc())
        return False


def join(*paths):
    """
    Join several directories
    Correct the bars "/" or "\" according to the operating system and whether or not it is smaba
    @rytpe: str
    @return: the concatenated path
    """
    list_path = []
    if paths[0].startswith("/"):
        list_path.append("")
    for path in paths:
        if path:
            if xbmc_vfs and type(path) != str:
                path = encode(path)
            list_path += path.replace("\\", "/").strip("/").split("/")

    if scrapertools.find_single_match(paths[0], r'(^\w+:\/\/)'):
        return str("/".join(list_path))
    else:
        return str(os.sep.join(list_path))


def split(path, vfs=True):
    """
    Returns a tuple consisting of the directory and filename of a path
    @param path: ruta
    @type path: str
    @return: (dirname, basename)
    @rtype: tuple
    """
    if scrapertools.find_single_match(path, r'(^\w+:\/\/)'):
        protocol = scrapertools.find_single_match(path, r'(^\w+:\/\/)')
        if '/' not in path[6:]:
            path = path.replace(protocol, protocol + "/", 1)
        return path.rsplit('/', 1)
    else:
        return os.path.split(path)


def basename(path, vfs=True):
    """
    Returns the file name of a path
    @param path: path
    @type path: str
    @return: path file
    @rtype: str
    """
    return split(path)[1]


def dirname(path, vfs=True):
    """
    Returns the directory of a path
    @param path: path
    @type path: str
    @return: path directory
    @rtype: str
    """
    return split(path)[0]


def is_relative(path):
    return "://" not in path and not path.startswith("/") and ":\\" not in path


def remove_tags(title):
    """
    returns the title without tags as color
    @type title: str
    @param title: title
    @rtype: str
    @return: string without tags
    """
    logger.debug()

    title_without_tags = scrapertools.find_single_match(title, r'\[color .+?\](.+)\[\/color\]')

    if title_without_tags:
        return title_without_tags
    else:
        return title


def remove_smb_credential(path):
    """
    returns the path without password / user for SMB paths
    @param path: path
    @type path: str
    @return: chain without credentials
    @rtype: str
    """
    logger.debug()

    if not scrapertools.find_single_match(path, r'(^\w+:\/\/)'):
        return path

    protocol = scrapertools.find_single_match(path, r'(^\w+:\/\/)')
    path_without_credentials = scrapertools.find_single_match(path, r'^\w+:\/\/(?:[^;\n]+;)?(?:[^:@\n]+[:|@])?(?:[^@\n]+@)?(.*?$)')

    if path_without_credentials:
        return (protocol + path_without_credentials)
    else:
        return path

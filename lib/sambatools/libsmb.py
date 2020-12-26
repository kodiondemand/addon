# -*- coding: utf-8 -*-

import os
import re
import sys
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

from nmb.NetBIOS import NetBIOS
from platformcode import logger
from smb.SMBConnection import SMBConnection

GitHub = 'https://github.com/miketeo/pysmb'  # check here from time to time for the latest version of SMB-pysmb
vesion_actual_pysmb = '1.2.6'  #updated on 26/12/2020

remote = None


def parse_url(url):
    # logger.info("Url: %s" % url)
    url = url.strip()
    patron = "^smb://(?:([^;\n]+);)?(?:([^:@\n]+)[:|@])?(?:([^@\n]+)@)?([^/]+)/([^/\n]+)([/]?.*?)$"
    domain, user, password, server_name, share_name, path = re.compile(patron, re.DOTALL).match(url).groups()

    server_name, server_ip = get_server_name_ip(server_name)

    if not user: user = 'guest'
    if not password: password = ""
    if not domain: domain = ""
    if path.endswith("/"): path = path[:-1]
    if not path: path = "/"

    # logger.info("Dominio: '%s' |Usuario: '%s' | Password: '%s' | Servidor: '%s' | IP: '%s' | Share Name: '%s' | Path: '%s'" % (domain, user, password, server_name, server_ip, share_name, path))
    return server_name, server_ip, share_name, unicode(path, "utf8"), user, password, domain


def get_server_name_ip(server):
    if re.compile("^\d+.\d+.\d+.\d+$").findall(server) or re.compile("^([^\.]+\.(?:[^\.]+\.)?(?:\w+)?)$").findall(server):
        server_ip = server
        server_name = None
    else:
        server_ip = None
        server_name = server.upper()

    if not server_ip: server_ip = NetBIOS().queryName(server_name)[0]
    if not server_name: server_name = NetBIOS().queryIPForName(server_ip)[0]

    return server_name, server_ip


def connect(url):
    # logger.info("Url: %s" % url)
    global remote
    server_name, server_ip, share_name, path, user, password, domain = parse_url(url)
    
    #Da problemas asumir que la sesión está abierta.  Si se abrió pero ha caducado, dará error.  Mejor conectar siempre
    """
    if not remote or not remote.sock or not server_name == remote.remote_name:
        remote = SMBConnection(user, password, domain, server_name)
        remote.connect(server_ip, 139)
    """
    remote = SMBConnection(user, password, domain, server_name)
    remote.connect(ip=server_ip, timeout=20)

    return remote, share_name, path


def listdir(url):
    logger.info("Url: %s" % url)
    remote, share_name, path = connect(url)
    files = [f.filename for f in remote.listPath(share_name, path) if not f.filename in [".", ".."]]
    return files


def walk(url, topdown=True, onerror=None):
    logger.info("Url: %s" % url)
    remote, share_name, path = connect(url)

    try:
        names = remote.listPath(share_name, path)
    except Exception as _err:
        if onerror is not None:
            onerror(_err)
        return

    dirs, nondirs = [], []
    for name in names:
        if name.filename in [".", ".."]:
            continue
        if name.isDirectory:
            dirs.append(name.filename)
        else:
            nondirs.append(name.filename)
    if topdown:
        yield unicode(url, "utf8"), dirs, nondirs

    for name in dirs:
        new_path = "/".join(url.split("/") + [name.encode("utf8")])
        for x in walk(new_path, topdown, onerror):
            yield x
    if not topdown:
        yield unicode(url, "utf8"), dirs, nondirs


def get_attributes(url):
    logger.info("Url: %s" % url)
    remote, share_name, path = connect(url)
    try:
        return remote.getAttributes(share_name, path)
    except Exception as e:
        raise type(e)(e.message, "")


def mkdir(url):
    logger.info("Url: %s" % url)
    remote, share_name, path = connect(url)
    try:
        remote.createDirectory(share_name, path)
    except Exception as e:
        raise type(e)(e.message, "")


def smb_open(url, mode):
    logger.info("Url: %s" % url)
    return SMBFile(url, mode)


def isfile(url):
    logger.info("Url: %s" % url)
    remote, share_name, path = connect(url)
    try:
        files = [f.filename for f in remote.listPath(share_name, os.path.dirname(path)) if not f.isDirectory]
    except Exception as e:
        raise type(e)(e.message, "")
    return os.path.basename(path) in files


def isdir(url):
    logger.info("Url: %s" % url)
    remote, share_name, path = connect(url)
    try:
        folders = [f.filename for f in remote.listPath(share_name, os.path.dirname(path)) if f.isDirectory]
    except Exception as e:
        raise type(e)(e.message, "")
    return os.path.basename(path) in folders or path == "/"


def exists(url):
    logger.info("Url: %s" % url)
    remote, share_name, path = connect(url)
    try:
        files = [f.filename for f in remote.listPath(share_name, os.path.dirname(path))]
    except Exception as e:
        raise type(e)(e.message, "")
    return os.path.basename(path) in files or path == "/"


def remove(url):
    logger.info("Url: %s" % url)
    remote, share_name, path = connect(url)
    try:
        remote.deleteFiles(share_name, path)
    except Exception as e:
        raise type(e)(e.message, "")


def rmdir(url):
    logger.info("Url: %s" % url)
    remote, share_name, path = connect(url)
    try:
        remote.deleteDirectory(share_name, path)
    except Exception as e:
        raise type(e)(e.message, "")


def rename(url, new_name):
    logger.info("Url: %s" % url)
    remote, share_name, path = connect(url)
    _, _, _, new_name, _, _, _ = parse_url(new_name)
    try:
        remote.rename(share_name, path, new_name)
    except Exception as e:
        raise type(e)(e.message, "")


class SMBFile(object):
    def __init__(self, url, mode="r"):
        import random
        try:
            import xbmc
        except:
            xbmc = None
        self.url = url
        self.remote, self.share, self.path = path = connect(url)
        self.mode = mode
        self.binary = False
        self.canread = False
        self.canwrite = False
        self.closed = True
        self.size = 0
        self.pos = 0
        if xbmc:
            self.tmp_path = os.path.join(xbmc.translatePath("special://temp/"), "%08x" % (random.getrandbits(32)))
        else:
            self.tmp_path = os.path.join(os.getenv("TEMP") or os.getenv("TMP") or os.getenv("TMPDIR"),
                                         "%08x" % (random.getrandbits(32)))
        self.tmp_file = None

        self.__get_mode__()

    def __del__(self):
        if self.tmp_file:
            self.tmp_file.close()

        if os.path.isfile(self.tmp_path):
            os.remove(self.tmp_path)

    def tmpfile(self):
        if self.tmp_file:
            self.tmp_file.close()
        self.tmp_file = open(self.tmp_path, "w+b")
        return self.tmp_file

    def __get_mode__(self):
        if "r+" in self.mode:
            try:
                attr = self.remote.getAttributes(self.share, self.path)
            except Exception as e:
                raise type(e)(e.message, "")

            self.size = attr.file_size
            self.canread = True
            self.canwrite = True
            self.closed = False

        elif "r" in self.mode:
            try:
                attr = self.remote.getAttributes(self.share, self.path)
            except Exception as e:
                raise type(e)(e.message, "")

            self.size = attr.file_size
            self.canread = True
            self.closed = False

        elif "w+" in self.mode:
            try:
                self.remote.storeFileFromOffset(self.share, self.path, self.tmpfile(), 0, truncate=True)
            except Exception as e:
                raise type(e)(e.message, "")

            self.canread = True
            self.canwrite = True
            self.closed = False

        elif "w" in self.mode:
            try:
                self.remote.storeFileFromOffset(self.share, self.path, self.tmpfile(), 0, truncate=True)
            except Exception as e:
                raise type(e)(e.message, "")

            self.canwrite = True
            self.closed = False

        elif "a+" in self.mode:
            try:
                self.remote.storeFileFromOffset(self.share, self.path, self.tmpfile(), 0)
                attr = self.remote.getAttributes(self.share, self.path)
            except Exception as e:
                raise type(e)(e.message, "")

            self.size = attr.file_size
            self.pos = self.size
            self.canwrite = True
            self.canread = True
            self.closed = False

        elif "a" in self.mode:
            try:
                self.remote.storeFileFromOffset(self.share, self.path, self.tmpfile(), 0)
                attr = self.remote.getAttributes(self.share, self.path)
            except Exception as e:
                raise type(e)(e.message, "")

            self.size = attr.file_size
            self.pos = self.size
            self.canwrite = True
            self.closed = False

        if "b" in self.mode:
            self.binary = True

    def seek(self, offset, whence=0):
        if whence == 0:
            self.pos = offset
        if whence == 1:
            self.pos += offset
        if whence == 2:
            self.pos = self.size + offset

        if self.pos < 0: self.pos = 0

    def tell(self):
        return self.pos

    def write(self, data):
        if not self.canwrite:
            raise IOError("File not open for writing")
        f = self.tmpfile()
        f.write(data)
        f.seek(0)
        self.remote.storeFileFromOffset(self.share, self.path, f, self.pos)
        self.pos += len(data)
        if self.pos > self.size:
            self.size = self.pos

    def read(self, size=-1):
        if not self.canread:
            raise IOError("File not open for reading")
        f = self.tmpfile()
        self.remote.retrieveFileFromOffset(self.share, self.path, f, self.pos, size)
        f.seek(0)
        data = f.read()
        self.seek(len(data), 1)
        return data

    def truncate(self, size=None):
        if not self.canwrite:
            raise IOError("File not open for writing")
        data = self.read(size)
        f = self.tmpfile()
        self.pos = 0
        f.write(data)
        f.seek(0)
        self.remote.storeFileFromOffset(self.share, self.path, f, self.pos, truncate=True)

    def close(self):
        self.remote.close()
        self.closed = True
        self.canwrite = False
        self.canread = False

    def flush(self):
        pass

    def writelines(self, sequence):
        for line in sequence:
            self.write(line)

    def readlines(self, sizehint=0):
        if not self.canread:
            raise IOError("File not open for reading")
        f = self.tmpfile()
        self.remote.retrieveFileFromOffset(self.share, self.path, f, self.pos)
        f.seek(0)
        data = f.readlines(sizehint)
        self.pos += len(data)

        if not self.binary:
            data = [l.replace("\r", "") for l in data]
        return data

    def readline(self, size=-1):
        if not self.canread:
            raise IOError("File not open for reading")
        f = self.tmpfile()
        self.remote.retrieveFileFromOffset(self.share, self.path, f, self.pos, size)
        f.seek(0)
        data = f.readline(size)
        self.pos += len(data)

        if not self.binary:
            data = data.replace("\r", "")
        return data

    def __iter__(self):
        return self.readlines().__iter__()

    def xreadlines(self):
        return self.__iter__()

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "<open SMBFile '%s', mode '%s' at %s>" % (self.url, self.mode, hex(id(self)))

    @property
    def __class__(self):
        return "<type 'file'>"

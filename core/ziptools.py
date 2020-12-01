# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# Zip Tools
# --------------------------------------------------------------------------------

from builtins import object
import sys
PY3 = False
VFS = True
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int; VFS = False

import zipfile

from platformcode import config, logger
from core import filetools


class ziptools(object):
    def extract(self, file, dir, folder_to_extract="", overwrite_question=False, backup=False):
        logger.debug("file= %s" % file)
        logger.debug("dir= %s" % dir)

        if not dir.endswith(':') and not filetools.exists(dir):
            filetools.mkdir(dir)

        zf = zipfile.ZipFile(filetools.file_open(file, vfs=False))
        if not folder_to_extract:
            self._createstructure(file, dir)
        num_files = len(zf.namelist())

        for nameo in zf.namelist():
            name = nameo.replace(':', '_').replace('<', '_').replace('>', '_').replace('|', '_').replace('"', '_').replace('?', '_').replace('*', '_')
            logger.debug("name=%s" % nameo)
            if not name.endswith('/'):
                logger.debug("it's not a directory")
                try:
                    (path, filename) = filetools.split(filetools.join(dir, name))
                    logger.debug("path=%s" % path)
                    logger.debug("name=%s" % name)
                    if folder_to_extract:
                        if path != filetools.join(dir, folder_to_extract):
                            break
                    else:
                        filetools.mkdir(path)
                except:
                    pass
                if folder_to_extract:
                    outfilename = filetools.join(dir, filename)

                else:
                    outfilename = filetools.join(dir, name)
                logger.debug("outfilename=%s" % outfilename)
                try:
                    if filetools.exists(outfilename) and overwrite_question:
                        from platformcode import platformtools
                        dyesno = platformtools.dialog_yesno("File already exists "," File %s to unzip already exists, do you want to overwrite it?" % filetools.basename(outfilename))
                        if not dyesno:
                            break
                        if backup:
                            import time
                            hora_folder = "Backup [%s]" % time.strftime("%d-%m_%H-%M", time.localtime())
                            backup = filetools.join(config.get_data_path(), 'backups', hora_folder, folder_to_extract)
                            if not filetools.exists(backup):
                                filetools.mkdir(backup)
                            filetools.copy(outfilename, filetools.join(backup, filetools.basename(outfilename)))

                    if not filetools.write(outfilename, zf.read(nameo), silent=True, vfs=VFS):  #TRUNCA en FINAL en Kodi 19 con VFS
                        logger.error("File error " + nameo)
                except:
                    import traceback
                    logger.error(traceback.format_exc())
                    logger.error("File error " + nameo)

        try:
            zf.close()
        except:
            logger.error("Error closing .zip " + file)

    def _createstructure(self, file, dir):
        self._makedirs(self._listdirs(file), dir)

    def create_necessary_paths(filename):
        try:
            (path, name) = filetools.split(filename)
            filetools.mkdir(path)
        except:
            pass

    def _makedirs(self, directories, basedir):
        for dir in directories:
            curdir = filetools.join(basedir, dir)
            if not filetools.exists(curdir):
                filetools.mkdir(curdir)

    def _listdirs(self, file):
        zf = zipfile.ZipFile(filetools.file_open(file, vfs=False))
        dirs = []
        for name in zf.namelist():
            if name.endswith('/'):
                dirs.append(name)

        dirs.sort()
        return dirs

    def zip(self, dir, file):
        import os
        zf = zipfile.ZipFile(filetools.file_open(file, "w", vfs=False), "w", zipfile.ZIP_DEFLATED)
        abs_src = os.path.abspath(dir)
        for dirname, subdirs, files in os.walk(dir):
            for filename in files:
                absname = os.path.abspath(os.path.join(dirname, filename))
                arcname = absname[len(abs_src) + 1:]
                zf.write(absname, arcname)
        zf.close()
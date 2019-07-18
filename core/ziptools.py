# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# Zip Tools
# --------------------------------------------------------------------------------

import os
import zipfile

from platformcode import config, logger


class ziptools:
    def extract(self, file, dir, folder_to_extract="", overwrite_question=False, backup=False):
        logger.info("file=%s" % file)
        logger.info("dir=%s" % dir)

        if not dir.endswith(':') and not os.path.exists(dir):
            os.mkdir(dir)

        zf = zipfile.ZipFile(file)
        if not folder_to_extract:
            self._createstructure(file, dir)
        num_files = len(zf.namelist())

        for nameo in zf.namelist():
            name = nameo.replace(':', '_').replace('<', '_').replace('>', '_').replace('|', '_').replace('"', '_').replace('?', '_').replace('*', '_')
            logger.info("name=%s" % nameo)
            if not name.endswith('/'):
                logger.info("no es un directorio")
                try:
                    (path, filename) = os.path.split(os.path.join(dir, name))
                    logger.info("path=%s" % path)
                    logger.info("name=%s" % name)
                    if folder_to_extract:
                        if path != os.path.join(dir, folder_to_extract):
                            break
                    else:
                        os.makedirs(path)
                except:
                    pass
                if folder_to_extract:
                    outfilename = os.path.join(dir, filename)

                else:
                    outfilename = os.path.join(dir, name)
                logger.info("outfilename=%s" % outfilename)
                try:
                    if os.path.exists(outfilename) and overwrite_question:
                        from platformcode import platformtools
                        dyesno = platformtools.dialog_yesno("El archivo ya existe",
                                                            "El archivo %s a descomprimir ya existe" \
                                                            ", ¿desea sobrescribirlo?" \
                                                            % os.path.basename(outfilename))
                        if not dyesno:
                            break
                        if backup:
                            import time
                            import shutil
                            hora_folder = "Copia seguridad [%s]" % time.strftime("%d-%m_%H-%M", time.localtime())
                            backup = os.path.join(config.get_data_path(), 'backups', hora_folder, folder_to_extract)
                            if not os.path.exists(backup):
                                os.makedirs(backup)
                            shutil.copy2(outfilename, os.path.join(backup, os.path.basename(outfilename)))

                    outfile = open(outfilename, 'wb')
                    outfile.write(zf.read(nameo))
                except:
                    logger.error("Error en fichero " + nameo)

    def _createstructure(self, file, dir):
        self._makedirs(self._listdirs(file), dir)

    def create_necessary_paths(filename):
        try:
            (path, name) = os.path.split(filename)
            os.makedirs(path)
        except:
            pass

    def _makedirs(self, directories, basedir):
        for dir in directories:
            curdir = os.path.join(basedir, dir)
            if not os.path.exists(curdir):
                os.mkdir(curdir)

    def _listdirs(self, file):
        zf = zipfile.ZipFile(file)
        dirs = []
        for name in zf.namelist():
            if name.endswith('/'):
                dirs.append(name)

        dirs.sort()
        return dirs

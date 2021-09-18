# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Backup and restore video library
# ------------------------------------------------------------

import datetime, xbmc, os, shutil, sys

from zipfile import ZipFile
from core import videolibrarytools, filetools
from platformcode import logger, config, platformtools, xbmc_videolibrary
from distutils.dir_util import copy_tree
from specials import videolibrary

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

temp_path = unicode(xbmc.translatePath("special://userdata/addon_data/plugin.video.kod/temp/"))
videolibrary_temp_path = unicode(xbmc.translatePath("special://userdata/addon_data/plugin.video.kod/temp/videolibrary"))
movies_path = unicode(filetools.join(videolibrary_temp_path, "movies"))
tvshows_path = unicode(filetools.join(videolibrary_temp_path, "tvshows"))
videolibrary_movies_path = unicode(videolibrarytools.MOVIES_PATH)
videolibrary_tvshows_path = unicode(videolibrarytools.TVSHOWS_PATH)


def export_videolibrary(item):
    logger.info()

    zip_file_folder = platformtools.dialog_browse(3, config.get_localized_string(80002))
    if zip_file_folder == "":
        return
    zip_file = unicode(xbmc.translatePath(zip_file_folder + "KoD_video_library-" + str(datetime.date.today()) + ".zip"))

    p_dialog = platformtools.dialog_progress_bg(config.get_localized_string(20000), config.get_localized_string(80003))
    # p_dialog.update(0)

    if filetools.exists(videolibrary_temp_path):
        shutil.rmtree(videolibrary_temp_path)
    filetools.mkdir(videolibrary_temp_path)
    p_dialog.update(25)
    filetools.mkdir(movies_path)
    copy_tree(videolibrary_movies_path, movies_path)
    p_dialog.update(50)
    filetools.mkdir(tvshows_path)
    copy_tree(videolibrary_tvshows_path, tvshows_path)
    p_dialog.update(75)

    zip(videolibrary_temp_path, zip_file)
    shutil.rmtree(temp_path)

    p_dialog.update(100)
    xbmc.sleep(1000)
    p_dialog.close()
    platformtools.dialog_notification(config.get_localized_string(20000), config.get_localized_string(80004), time=5000, sound=False)


def import_videolibrary(item):
    logger.info()

    zip_file = unicode(platformtools.dialog_browse(1, config.get_localized_string(80005), mask=".zip"))
    if zip_file == "":
        return
    if not platformtools.dialog_yesno(config.get_localized_string(20000), config.get_localized_string(80006)):
        return

    p_dialog = platformtools.dialog_progress_bg(config.get_localized_string(20000), config.get_localized_string(80007))
    # p_dialog.update(0)

    if filetools.exists(temp_path):
        shutil.rmtree(temp_path)
    filetools.mkdir(videolibrary_temp_path)

    unzip(videolibrary_temp_path, zip_file)
    p_dialog.update(20)

    if config.is_xbmc() and config.get_setting("videolibrary_kodi"):
        xbmc_videolibrary.clean()
    p_dialog.update(30)
    shutil.rmtree(videolibrary_movies_path)
    shutil.rmtree(videolibrary_tvshows_path)
    p_dialog.update(50)

    config.verify_directories_created()
    if filetools.exists(movies_path):
        copy_tree(movies_path, videolibrary_movies_path)
    p_dialog.update(70)
    if filetools.exists(tvshows_path):
        copy_tree(tvshows_path, videolibrary_tvshows_path)
    p_dialog.update(90)
    shutil.rmtree(temp_path)

    p_dialog.update(100)
    xbmc.sleep(1000)
    p_dialog.close()
    platformtools.dialog_notification(config.get_localized_string(20000), config.get_localized_string(80008), time=5000, sound=False)

    videolibrary.update_videolibrary()
    if config.is_xbmc() and config.get_setting("videolibrary_kodi"):
        xbmc_videolibrary.update()


def zip(dir, file):
    smb = False
    if file.lower().startswith('smb://'):
        temp = file
        file = filetools.join(temp_path, os.path.split(file)[-1])
        smb = True
    with ZipFile(filetools.file_open(file, 'wb', vfs=False), "w") as zf:
        abs_src = os.path.abspath(dir)
        for dirname, subdirs, files in os.walk(dir):
            for filename in files:
                absname = os.path.abspath(os.path.join(dirname, filename))
                arcname = absname[len(abs_src) + 1:]
                zf.write(absname, arcname)
        zf.close()
    if smb:
        filetools.move(file, temp)


def unzip(dir, file):
    if file.lower().startswith('smb://'):
        temp = filetools.join(temp_path, os.path.split(file)[-1])
        filetools.copy(file, temp)
        file = temp

    with ZipFile(filetools.file_open(file, 'rb', vfs=False), 'r') as zf:
        zf.extractall(dir)

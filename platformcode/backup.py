# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Backup and restore video library
# ------------------------------------------------------------

import datetime,  xbmc

from core import ziptools, videolibrarytools, filetools
from platformcode import logger, config, platformtools, xbmc_videolibrary
from distutils.dir_util import copy_tree
from specials import videolibrary

temp_path = u'' + xbmc.translatePath("special://userdata/addon_data/plugin.video.kod/temp/")
movies_path = u'' + filetools.join(temp_path, "movies")
tvshows_path = u'' + filetools.join(temp_path, "tvshows")
videolibrary_movies_path = u'' + videolibrarytools.MOVIES_PATH
videolibrary_tvshows_path = u'' + videolibrarytools.TVSHOWS_PATH


def export_videolibrary(item):
    logger.info()

    zip_file_folder = platformtools.dialog_browse(3, config.get_localized_string(80002))
    if zip_file_folder == "":
        return
    zip_file = u'' + xbmc.translatePath(zip_file_folder + "KoD_video_library-" + str(datetime.date.today()) + ".zip")

    p_dialog = platformtools.dialog_progress_bg(config.get_localized_string(20000), config.get_localized_string(80003))
    p_dialog.update(0)

    if filetools.exists(temp_path):
        filetools.rmdirtree(temp_path)
    filetools.mkdir(temp_path)
    p_dialog.update(25)
    filetools.mkdir(movies_path)
    copy_tree(videolibrary_movies_path, movies_path)
    p_dialog.update(50)
    filetools.mkdir(tvshows_path)
    copy_tree(videolibrary_tvshows_path, tvshows_path)
    p_dialog.update(75)

    zipper = ziptools.ziptools()
    zipper.zip(temp_path, zip_file)

    filetools.rmdirtree(temp_path)

    p_dialog.update(100)
    xbmc.sleep(1000)
    p_dialog.close()
    platformtools.dialog_notification(config.get_localized_string(20000), config.get_localized_string(80004), time=5000, sound=False)


def import_videolibrary(item):
    logger.info()

    zip_file = u'' + platformtools.dialog_browse(1, config.get_localized_string(80005), mask=".zip")
    if zip_file == "":
        return
    if not platformtools.dialog_yesno(config.get_localized_string(20000), config.get_localized_string(80006)):
        return

    p_dialog = platformtools.dialog_progress_bg(config.get_localized_string(20000), config.get_localized_string(80007))
    p_dialog.update(0)

    if filetools.exists(temp_path):
        filetools.rmdirtree(temp_path)
    filetools.mkdir(temp_path)

    unzipper = ziptools.ziptools()
    unzipper.extract(zip_file, temp_path)
    p_dialog.update(20)

    if config.is_xbmc() and config.get_setting("videolibrary_kodi"):
        xbmc_videolibrary.clean()
    p_dialog.update(30)
    filetools.rmdirtree(videolibrary_movies_path)
    filetools.rmdirtree(videolibrary_tvshows_path)
    p_dialog.update(50)

    config.verify_directories_created()
    if filetools.exists(movies_path):
        copy_tree(movies_path, videolibrary_movies_path)
    p_dialog.update(70)
    if filetools.exists(tvshows_path):
        copy_tree(tvshows_path, videolibrary_tvshows_path)
    p_dialog.update(90)
    filetools.rmdirtree(temp_path)

    p_dialog.update(100)
    xbmc.sleep(1000)
    p_dialog.close()
    platformtools.dialog_notification(config.get_localized_string(20000), config.get_localized_string(80008), time=5000, sound=False)

    videolibrary.update_videolibrary()
    if config.is_xbmc() and config.get_setting("videolibrary_kodi"):
        xbmc_videolibrary.update()
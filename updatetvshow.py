# -*- coding: utf-8 -*-
import xbmc, sys, xbmcgui, os, xbmcvfs, traceback
from platformcode import config, logger

librerias = xbmc.translatePath(os.path.join(config.get_runtime_path(), 'lib'))
sys.path.insert(0, librerias)

from core.item import Item
from lib.sambatools import libsmb as samba
from core import scrapertools


def exists(path, silent=False, vfs=True):
    path = xbmc.translatePath(path)
    try:
        if vfs:
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

def join(*paths):
    list_path = []
    if paths[0].startswith("/"):
        list_path.append("")
    for path in paths:
        if path:
            list_path += path.replace("\\", "/").strip("/").split("/")

    if scrapertools.find_single_match(paths[0], r'(^\w+:\/\/)'):
        return str("/".join(list_path))
    else:
        return str(os.sep.join(list_path))


def search_paths(Id):
    records = execute_sql('SELECT idPath FROM tvshowlinkpath WHERE idShow LIKE "%s"' % Id)
    if len(records) >= 1:
        for record in records:
            path_records = execute_sql('SELECT strPath FROM path WHERE idPath LIKE "%s"' % record[0])
            for path in path_records:
                if config.get_setting('videolibrarypath') in path[0] and exists(join(path[0], 'tvshow.nfo')):
                    return path[0]
    return ''


def execute_sql(sql):
    logger.debug()
    file_db = ""
    records = None

    # We look for the archive of the video database according to the version of kodi
    video_db = config.get_platform(True)['video_db']
    if video_db:
        file_db = os.path.join(xbmc.translatePath("special://userdata/Database"), video_db)

    # alternative method to locate the database
    if not file_db or not os.path.exists(file_db):
        file_db = ""
        for f in os.path.listdir(xbmc.translatePath("special://userdata/Database")):
            path_f = os.path.join(xbmc.translatePath("special://userdata/Database"), f)

            if os.path.pathoos.pathols.isfile(path_f) and f.lower().startswith('myvideos') and f.lower().endswith('.db'):
                file_db = path_f
                break

    if file_db:
        logger.debug("DB file: %s" % file_db)
        conn = None
        try:
            import sqlite3
            conn = sqlite3.connect(file_db)
            cursor = conn.cursor()

            logger.debug("Running sql: %s" % sql)
            cursor.execute(sql)
            conn.commit()

            records = cursor.fetchall()
            if sql.lower().startswith("select"):
                if len(records) == 1 and records[0][0] is None:
                    records = []

            conn.close()
            logger.debug("Query executed. Records: %s" % len(records))

        except:
            logger.error("Error executing sql query")
            if conn:
                conn.close()

    else:
        logger.debug("Database not found")

    return records

if __name__ == '__main__':
    path = search_paths(sys.listitem.getVideoInfoTag().getDbId())
    if path:
        item = Item(action="update_tvshow", channel="videolibrary", path=path)
        # Why? I think it is not necessary, just commented
        # item.tourl()
        xbmc.executebuiltin("RunPlugin(plugin://plugin.video.kod/?" + item.tourl() + ")")
    else:
        dialog = xbmcgui.Dialog()
        title = sys.listitem.getVideoInfoTag().getTitle()
        if dialog.yesno(title, config.get_localized_string(70817) % title, nolabel=config.get_localized_string(70170), yeslabel=config.get_localized_string(30022)):
            item = Item(action="new_search", channel="search", mode="tvshow", search_text=sys.listitem.getVideoInfoTag().getTitle())
            xbmc.executebuiltin("ActivateWindow(10025,plugin://plugin.video.kod/?" + item.tourl() + ")")

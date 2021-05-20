# -*- coding: utf-8 -*-
# from specials import videolibrary
import os, sys, xbmc

try:
    import xbmcvfs
    xbmc.translatePath = xbmcvfs.translatePath
    xbmc.validatePath = xbmcvfs.validatePath
    xbmc.makeLegalFilename = xbmcvfs.makeLegalFilename
except:
    pass

from platformcode import config, logger
librerias = xbmc.translatePath(os.path.join(config.get_runtime_path(), 'lib'))
sys.path.insert(0, librerias)

from core.item import Item
from core import scrapertools
from core.videolibrarydb import videolibrarydb
from platformcode.xbmc_videolibrary import execute_sql_kodi
from specials.videolibrary import update_videolibrary


def search_id(Id):
    n, records = execute_sql_kodi('SELECT idPath FROM tvshowlinkpath WHERE idShow= {}'.format(Id))
    if records:
        n, records = execute_sql_kodi('SELECT strPath FROM path WHERE idPath= "{}"'.format(records[0][0]))
    if records:
        return scrapertools.find_single_match(records[0][0], r'\[(tt[^\]]+)')
    return ''


if __name__ == '__main__':
    videolibrary_id = search_id(sys.listitem.getVideoInfoTag().getDbId())
    if videolibrary_id:
        tvshows_ids = list(videolibrarydb['tvshow'].keys())
        videolibrarydb.close()
        if videolibrary_id in tvshows_ids:
            item = Item(videolibrary_id=videolibrary_id)
            update_videolibrary(item)

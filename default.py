# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# XBMC entry point
# ------------------------------------------------------------

import os
import sys

import xbmc

# functions that on kodi 19 moved to xbmcvfs
try:
    import xbmcvfs
    xbmc.translatePath = xbmcvfs.translatePath
    xbmc.validatePath = xbmcvfs.validatePath
    xbmc.makeLegalFilename = xbmcvfs.makeLegalFilename
except:
    pass
from platformcode import config, logger

logger.info("init...")

librerias = xbmc.translatePath(os.path.join(config.get_runtime_path(), 'lib'))
sys.path.insert(0, librerias)

from platformcode import launcher

if sys.argv[2] == "":
    launcher.start()

launcher.run()
# import sqlitedict
#
# d = sqlitedict.SqliteDict('/home/marco/.kodi/userdata/addon_data/plugin.video.kod/videolibrary/videolibrary.sqlite', 'tvshow')
# for k, v in d.items():
#     print(k, v['item'])

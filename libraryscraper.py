# -*- coding: utf-8 -*-
# scraper for Kodi Library based on db
import xbmc, xbmcplugin, sys, os
from platformcode import logger, config

try:
    import xbmcvfs
    xbmc.translatePath = xbmcvfs.translatePath
    xbmc.validatePath = xbmcvfs.validatePath
    xbmc.makeLegalFilename = xbmcvfs.makeLegalFilename
except:
    pass

librerias = xbmc.translatePath(os.path.join(config.get_runtime_path(), 'lib'))
sys.path.insert(0, librerias)


from core.videolibrarytools import MOVIES_PATH, TVSHOWS_PATH, videolibrarydb

try:
    from urlparse import parse_qsl
except ImportError: # py2 / py3
    from urllib.parse import parse_qsl

def get_params(argv):
    result = {'handle': int(argv[0])}
    if len(argv) < 2 or not argv[1]:
        return result

    result.update(parse_qsl(argv[1].lstrip('?')))
    return result

if __name__ == '__main__':
    # params = get_params(sys.argv[1:])
    logger.debug('PARAMS')
    # run()
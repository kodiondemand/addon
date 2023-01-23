# functions that on kodi 19 moved to xbmcvfs
import xbmc
try:
    import xbmcvfs
    xbmc.translatePath = xbmcvfs.translatePath
    xbmc.validatePath = xbmcvfs.validatePath
    xbmc.makeLegalFilename = xbmcvfs.makeLegalFilename
except:
    pass
from platformcode import config, logger
import sys, xbmc, xbmcgui, os

librerias = xbmc.translatePath(os.path.join(config.get_runtime_path(), 'lib'))
sys.path.insert(0, librerias)

from core import jsontools
addon_id = config.get_addon_core().getAddonInfo('id')

LOCAL_FILE = os.path.join(config.get_runtime_path(), "platformcode/contextmenu/contextmenu.json")
f = open(LOCAL_FILE)
contextmenu_settings = jsontools.load(open(LOCAL_FILE).read())
f.close()


def build_menu():
    # from core.support import dbg;dbg()
    tmdbid = xbmc.getInfoLabel('ListItem.Property(tmdb_id)')
    mediatype = xbmc.getInfoLabel('ListItem.DBTYPE')
    title = xbmc.getInfoLabel('ListItem.Title')
    year = xbmc.getInfoLabel('ListItem.Year')
    imdb = xbmc.getInfoLabel('ListItem.IMDBNumber')
    filePath = xbmc.getInfoLabel('ListItem.FileNameAndPath')
    containerPath = xbmc.getInfoLabel('Container.FolderPath')

    logstr = "Selected ListItem is: 'IMDB: {}' - TMDB: {}' - 'Title: {}' - 'Year: {}'' - 'Type: {}'".format(imdb, tmdbid, title, year, mediatype)
    logger.debug(logstr)
    logger.debug(filePath)
    logger.debug(containerPath)

    contextmenuitems = []
    contextmenuactions = []

    for itemmodule in contextmenu_settings:
        logger.debug('check contextmenu', itemmodule)
        module = __import__(itemmodule, None, None, [itemmodule])

        logger.debug('Add contextmenu item ->', itemmodule)
        module_item_actions = module.get_menu_items()
        contextmenuitems.extend([item for item, fn in module_item_actions])
        contextmenuactions.extend([fn for item, fn in module_item_actions])

    if len(contextmenuitems) == 0:
        logger.debug('No contextmodule found, build an empty one')
        contextmenuitems.append(empty_item())
        contextmenuactions.append(lambda: None)

    ret = xbmcgui.Dialog().contextmenu(contextmenuitems)

    if ret > -1:
        logger.debug('Contextmenu module index', ret, ', label=' + contextmenuitems[ret])
        contextmenuactions[ret]()


def empty_item():
    return config.get_localized_string(90004)


if __name__ == '__main__':
    build_menu()




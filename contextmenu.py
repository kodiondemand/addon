import os
from platformcode import config, logger
import xbmc, sys, xbmcgui, os

librerias = xbmc.translatePath(os.path.join(config.get_runtime_path(), 'lib'))
sys.path.insert(0, librerias)

from core import jsontools, support

addon_id = config.get_addon_core().getAddonInfo('id')

LOCAL_FILE = os.path.join(config.get_runtime_path(), "platformcode/contextmenu/contextmenu.json")
f = open(LOCAL_FILE)
try:
    contextmenu_settings = jsontools.load( f.read() )
except:
    contextmenu_settings = []
f.close()




def build_menu():

    tmdbid = xbmc.getInfoLabel('ListItem.Property(tmdb_id)')
    mediatype = xbmc.getInfoLabel('ListItem.DBTYPE')
    title = xbmc.getInfoLabel('ListItem.Title')
    year = xbmc.getInfoLabel('ListItem.Year')
    imdb = xbmc.getInfoLabel('ListItem.IMDBNumber')
    filePath = xbmc.getInfoLabel('ListItem.FileNameAndPath')
    containerPath = xbmc.getInfoLabel('Container.FolderPath')

    logstr = "Selected ListItem is: 'IMDB: {}' - TMDB: {}' - 'Title: {}' - 'Year: {}'' - 'Type: {}'".format(imdb, tmdbid, title, year, mediatype)
    logger.info(logstr)
    logger.info(filePath)
    logger.info(containerPath)

    contextmenumodules = []
    contextmenu = []

    for itemmodule in contextmenu_settings:
        logger.debug('check contextmenu', itemmodule )
        module = __import__(itemmodule, None, None, [ itemmodule] )

        # if module.check_condition():
        logger.info('Add contextmenu item ->',itemmodule )
        contextmenumodules.append( module )


    contextmenuitems = []
    contextmenuactions = []
    empty = False
    if len(contextmenumodules) == 0:
        logger.info('No contextmodule found, build an empty one')
        contextmenucontextmenuitems.append( empty_item() )
        empty = True
    else:
        support.dbg()
        for itemmodule in contextmenumodules:
            module_item_actions = itemmodule.get_menu_items()
            contextmenuitems = contextmenuitems + [item for item, fn in module_item_actions ]
            contextmenuactions = contextmenuactions + [fn for item, fn in module_item_actions ]

    ret = xbmcgui.Dialog().contextmenu( contextmenuitems )

    if not empty and ret > -1:
        module_function = contextmenuactions[ ret ]
        logger.info( 'Contextmenu module index', ret,  'for -> {}', itemmodule )
        if module_function:
            module_function()
        else:
            logger.warn('No function for menu item: {}'.format(contextmenuitems[ret]) )


def empty_item():
    return config.get_localized_string(90004)


if __name__ == '__main__':
    build_menu()




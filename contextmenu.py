from platformcode import config, logger
import xbmc, sys, xbmcgui, os

librerias = xbmc.translatePath(os.path.join(config.getRuntimePath(), 'lib'))
sys.path.insert(0, librerias)

from core import jsontools, support

addon_id = config.getAddonCore().getAddonInfo('id')

LOCAL_FILE = os.path.join(config.getRuntimePath(), "platformcode/contextmenu/contextmenu.json")
f = open(LOCAL_FILE)
contextmenu_settings = jsontools.load(open(LOCAL_FILE).read())
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

    contextmenuitems = []
    contextmenuactions = []

    for itemmodule in contextmenu_settings:
        logger.debug('check contextmenu', itemmodule)
        module = __import__(itemmodule, None, None, [itemmodule])

        logger.info('Add contextmenu item ->', itemmodule)
        module_item_actions = module.get_menu_items()
        contextmenuitems.extend([item for item, fn in module_item_actions])
        contextmenuactions.extend([fn for item, fn in module_item_actions])

    if len(contextmenuitems) == 0:
        logger.info('No contextmodule found, build an empty one')
        contextmenuitems.append(empty_item())
        contextmenuactions.append(lambda: None)

    ret = xbmcgui.Dialog().contextmenu(contextmenuitems)

    if ret > -1:
        logger.info('Contextmenu module index', ret, ', label=' + contextmenuitems[ret])
        contextmenuactions[ret]()


def empty_item():
    return config.getLocalizedString(90004)


if __name__ == '__main__':
    build_menu()




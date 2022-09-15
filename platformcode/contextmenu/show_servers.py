import xbmc

from core.item import Item
from platformcode import config


def get_menu_items():
    mediatype = xbmc.getInfoLabel('ListItem.DBTYPE')
    filePath = xbmc.getInfoLabel('ListItem.FileNameAndPath')
    res = []
    if 'kod' in filePath and mediatype in ['movie', 'episode'] and config.get_setting('autoplay'):
        res = [(config.get_localized_string(70192), execute)]
    return res


def execute():
    from core import filetools
    from platformcode.launcher import run
    filePath = xbmc.getInfoLabel('ListItem.FileNameAndPath')
    item = Item().fromurl(filetools.read(filePath))
    item.disableAutoplay = True

    run(item)

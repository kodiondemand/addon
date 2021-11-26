# -*- coding: utf-8 -*-
from core.item import Item
from core.support import thumb
from platformcode import config, logger

guideUrl = "https://github.com/kodiondemand/addon/wiki/Guida-alle-funzioni-di-Kod"

def mainlist(item):
    logger.debug()
    itemlist = []

    if config.is_xbmc():
        itemlist.append(Item(title=config.getLocalizedString(707429), channel="setting", action="report_menu",
                             thumbnail=thumb("error"), viewmode="list",folder=True))

    itemlist.append(Item(action="open_browser", title=config.getLocalizedString(60447),
                         thumbnail=thumb("help"), url=guideUrl, plot=guideUrl,
                         folder=False))
    itemlist.append(Item(channel="setting", action="check_quickfixes", folder=False, thumbnail=thumb("update"),
                         title=config.getLocalizedString(30001), plot=config.getAddonVersion(with_fix=True)))

    return itemlist


# -*- coding: utf-8 -*-
from channelselector import get_thumb
from core.item import Item
from platformcode import config, logger

guideUrl = "https://github.com/kodiondemand/addon/wiki/Guida-alle-funzioni-di-Kod"

def mainlist(item):
    logger.debug()
    itemlist = []

    if config.is_xbmc():
        itemlist.append(Item(title=config.get_localized_string(707429), channel="setting", action="report_menu",
                             thumbnail=get_thumb("error.png"), viewmode="list",folder=True))

    itemlist.append(Item(action="open_browser", title=config.get_localized_string(60447),
                         thumbnail=get_thumb("help.png"), url=guideUrl, plot=guideUrl,
                         folder=False))
    itemlist.append(Item(channel="setting", action="check_quickfixes", folder=False, thumbnail=get_thumb("update.png"),
                         title=config.get_localized_string(30001), plot=config.get_addon_version(with_fix=True)))

    return itemlist


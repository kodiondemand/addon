# -*- coding: utf-8 -*-

from core import servertools
from core.support import match, info, server
from core.item import Item
from platformcode import config, logger, platformtools


def mainlist(item):
    info()

    itemlist = []
    itemlist.append(Item(channel=item.channel, action="search", title=config.get_localized_string(60089), thumbnail=item.thumbnail, args='server', folder=False))
    itemlist.append(Item(channel=item.channel, action="search", title=config.get_localized_string(60090), thumbnail=item.thumbnail, args='direct', folder=False))
    itemlist.append(Item(channel=item.channel, action="search", title=config.get_localized_string(60091), thumbnail=item.thumbnail, folder=False))

    return itemlist


# When the function "search" is called, the launcher asks for a text to search for and adds it as a parameter
def search(item, text):
    info(text)

    if not text.startswith("http"):
        text = "http://" + text

    itemlist = []

    if "server" in item.args:
        itemlist = server(item, text)
    elif "direct" in item.args:
        itemlist.append(Item(channel=item.channel, action="play", url=text, server="directo", title=config.get_localized_string(60092)))
        itemlist = server(item, itemlist=itemlist)
    else:
        data = match(text).data
        itemlist = server(item, data=data)
        for item in itemlist:
            item.channel = "url"
            item.action = "play"

    if itemlist:
        if len(itemlist) == 1:
            from platformcode.launcher import play
            play(itemlist[0].clone(no_return=True))
        platformtools.serverWindow(item, itemlist)
    else:
        platformtools.dialog_notification(config.get_localized_string(20000), config.get_localized_string(60347))

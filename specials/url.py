# -*- coding: utf-8 -*-

from core import servertools
from core.support import match, info
from core.item import Item
from platformcode import config, logger


def mainlist(item):
    info()

    itemlist = []
    itemlist.append(Item(channel=item.channel, action="search", title=config.get_localized_string(60089), thumbnail=item.thumbnail, args='server'))
    itemlist.append(Item(channel=item.channel, action="search", title=config.get_localized_string(60090), thumbnail=item.thumbnail, args='direct'))
    itemlist.append(Item(channel=item.channel, action="search", title=config.get_localized_string(60091), thumbnail=item.thumbnail))

    return itemlist


# When the function "search" is called, the launcher asks for a text to search for and adds it as a parameter
def search(item, text):
    info(text)

    if not text.startswith("http"):
        text = "http://" + text

    itemlist = []

    if "server" in item.args:
        from core.support import server
        itemlist = server(item, text)
    elif "direct" in item.args:
        itemlist.append(Item(channel=item.channel, action="play", url=text, server="directo", title=config.get_localized_string(60092)))
    else:
        data = match(text).data
        itemlist = servertools.find_video_items(data=data)
        for item in itemlist:
            item.channel = "url"
            item.action = "play"

    if len(itemlist) == 0:
        itemlist.append(Item(channel=item.channel, action="search", title=config.get_localized_string(60093)))

    return itemlist

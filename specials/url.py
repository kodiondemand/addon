# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger


def mainlist(item):
    logger.info()

    itemlist = []
    itemlist.append(Item(channel=item.channel, action="search", title=config.get_localized_string(60089)))
    itemlist.append(Item(channel=item.channel, action="search", title=config.get_localized_string(60090)))
    itemlist.append(Item(channel=item.channel, action="search", title=config.get_localized_string(60091)))

    return itemlist


# Al llamarse "search" la función, el launcher pide un texto a buscar y lo añade como parámetro
def search(item, texto):
    logger.info("texto=" + texto)

    if not texto.startswith("http"):
        texto = "http://" + texto

    itemlist = []

    if "servidor" in item.title:
        itemlist = servertools.find_video_items(data=texto)
        for item in itemlist:
            item.channel = "url"
            item.action = "play"
    elif "directo" in item.title:
        itemlist.append(Item(channel=item.channel, action="play", url=texto, server="directo", title=config.get_localized_string(60092)))
    else:
        data = httptools.downloadpage(texto).data
        itemlist = servertools.find_video_items(data=data)
        for item in itemlist:
            item.channel = "url"
            item.action = "play"

    if len(itemlist) == 0:
        itemlist.append(Item(channel=item.channel, action="search", title=config.get_localized_string(60093)))

    return itemlist

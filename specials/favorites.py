# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# List of favorite videos
# ------------------------------------------------------------

import os, time

from core import filetools, scrapertools
from core.item import Item
from platformcode import config, logger, platformtools

try:
    # We set the path to favorites.xml
    if config.is_xbmc():
        import xbmc

        FAVOURITES_PATH = xbmc.translatePath("special://profile/favourites.xml")
    else:
        FAVOURITES_PATH = os.path.join(config.get_data_path(), "favourites.xml")
except:
    import traceback

    logger.error(traceback.format_exc())


def mainlist(item):
    logger.debug()
    itemlist = []

    for name, thumb, data in read_favourites():
        if "plugin://plugin.video.%s/?" % config.PLUGIN_NAME in data:
            url = scrapertools.find_single_match(data, 'plugin://plugin.video.%s/\?([^;]*)' % config.PLUGIN_NAME).replace("&quot", "")

            item = Item().fromurl(url)
            item.title = name
            item.thumbnail = thumb
            item.isFavourite = True

            if type(item.context) == str:
                item.context = item.context.split("|")
            elif type(item.context) != list:
                item.context = []

            item.context.extend([{"title": config.get_localized_string(30154),  # "Remove from favorites "
                                  "action": "delFavourite",
                                  "channel": "favorites",
                                  "from_title": item.title},
                                 {"title": config.get_localized_string(70278), # Rename
                                  "action": "renameFavourite",
                                  "channel": "favorites",
                                  "from_title": item.title}
                                 ])
            # logger.debug(item.tostring('\n'))
            itemlist.append(item)

    return itemlist


def read_favourites():
    favourites_list = []
    if filetools.exists(FAVOURITES_PATH):
        data = filetools.read(FAVOURITES_PATH)

        matches = scrapertools.find_multiple_matches(data, "<favourite([^<]*)</favourite>")
        for match in matches:
            name = scrapertools.find_single_match(match, 'name="([^"]*)')
            thumb = scrapertools.find_single_match(match, 'thumb="([^"]*)')
            data = scrapertools.find_single_match(match, '[^>]*>([^<]*)')
            favourites_list.append((name, thumb, data))

    return favourites_list


def save_favourites(favourites_list):
    raw = '<favourites>' + chr(10)
    for name, thumb, data in favourites_list:
        raw += '    <favourite name="%s" thumb="%s">%s</favourite>' % (name, thumb, data) + chr(10)
    raw += '</favourites>' + chr(10)

    return filetools.write(FAVOURITES_PATH, raw)


def addFavourite(item):
    logger.debug()
    # logger.debug(item.tostring('\n'))

    # If you get here through the context menu, you must retrieve the action and channel parameters
    if item.from_action:
        item.__dict__["action"] = item.__dict__.pop("from_action")
    if item.from_channel:
        item.__dict__["channel"] = item.__dict__.pop("from_channel")

    favourites_list = read_favourites()
    data = "ActivateWindow(10025,&quot;plugin://plugin.video.%s/?" % config.PLUGIN_NAME + item.tourl() + "&quot;,return)"
    titulo = item.title.replace('"', "'")
    favourites_list.append((titulo, item.thumbnail, data))

    if save_favourites(favourites_list):
        platformtools.dialog_ok(config.get_localized_string(30102), titulo + '\n' + config.get_localized_string(30108))  # 'added to favorites'


def delFavourite(item):
    logger.debug()
    # logger.debug(item.tostring('\n'))

    if item.from_title:
        item.title = item.from_title

    favourites_list = read_favourites()
    for fav in favourites_list[:]:
        if fav[0] == item.title:
            favourites_list.remove(fav)

            if save_favourites(favourites_list):
                platformtools.dialog_ok(config.get_localized_string(30102), item.title + '\n' + config.get_localized_string(30105).lower())  # 'Removed from favorites'
                platformtools.itemlist_refresh()
            break


def renameFavourite(item):
    logger.debug()
    # logger.debug(item.tostring('\n'))

    # Find the item we want to rename in favorites.xml
    favourites_list = read_favourites()
    for i, fav in enumerate(favourites_list):
        if fav[0] == item.from_title:
            # open keyboard
            new_title = platformtools.dialog_input(item.from_title, item.title)
            if new_title:
                favourites_list[i] = (new_title, fav[1], fav[2])
                if save_favourites(favourites_list):
                    platformtools.dialog_ok(config.get_localized_string(30102), item.from_title + '\n' + config.get_localized_string(60086) + '\n' + new_title)  # 'Removed from favorites'
                    platformtools.itemlist_refresh()


##################################################
# Features to migrate old favorites (.txt)
def readbookmark(filepath):
    logger.debug()
    try:
        import urllib.parse as urllib
    except ImportError:
        import urllib

    bookmarkfile = filetools.file_open(filepath)

    lines = bookmarkfile.readlines()

    try:
        titulo = urllib.unquote_plus(lines[0].strip())
    except:
        titulo = lines[0].strip()

    try:
        url = urllib.unquote_plus(lines[1].strip())
    except:
        url = lines[1].strip()

    try:
        thumbnail = urllib.unquote_plus(lines[2].strip())
    except:
        thumbnail = lines[2].strip()

    try:
        server = urllib.unquote_plus(lines[3].strip())
    except:
        server = lines[3].strip()

    try:
        plot = urllib.unquote_plus(lines[4].strip())
    except:
        plot = lines[4].strip()

    # ContentTitle and channel fields added
    if len(lines) >= 6:
        try:
            contentTitle = urllib.unquote_plus(lines[5].strip())
        except:
            contentTitle = lines[5].strip()
    else:
        contentTitle = titulo

    if len(lines) >= 7:
        try:
            canal = urllib.unquote_plus(lines[6].strip())
        except:
            canal = lines[6].strip()
    else:
        canal = ""

    bookmarkfile.close()

    return canal, titulo, thumbnail, plot, server, url, contentTitle


def check_bookmark(readpath):
    # Create a list with favorite entries
    itemlist = []

    if readpath.startswith("special://") and config.is_xbmc():
        import xbmc
        readpath = xbmc.translatePath(readpath)

    for fichero in sorted(filetools.listdir(readpath)):
        # Old files (".txt")
        if fichero.endswith(".txt"):
            # We wait 0.1 seconds between files, so that the file names do not overlap
            time.sleep(0.1)

            # We get the item from the .txt
            canal, titulo, thumbnail, plot, server, url, contentTitle = readbookmark(filetools.join(readpath, fichero))
            if canal == "":
                canal = "favorites"
            item = Item(channel=canal, action="play", url=url, server=server, title=contentTitle, thumbnail=thumbnail,
                        plot=plot, fanart=thumbnail, contentTitle=contentTitle, folder=False)

            filetools.rename(filetools.join(readpath, fichero), fichero[:-4] + ".old")
            itemlist.append(item)

    # If there are Favorites to save
    if itemlist:
        favourites_list = read_favourites()
        for item in itemlist:
            data = "ActivateWindow(10025,&quot;plugin://plugin.video.kod/?" + item.tourl() + "&quot;,return)"
            favourites_list.append((item.title, item.thumbnail, data))
        if save_favourites(favourites_list):
            logger.debug("Correct txt to xml conversion")


# This will only work when migrating from previous versions, there is no longer a "bookmarkpath"
try:
    if config.get_setting("bookmarkpath") != "":
        check_bookmark(config.get_setting("bookmarkpath"))
    else:
        logger.debug("No path to old version favorites")
except:
    pass

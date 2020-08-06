# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# XBMC Launcher (xbmc / kodi)
# ------------------------------------------------------------

import sys, os
PY3 = False
if sys.version_info[0] >= 3:PY3 = True; unicode = str; unichr = chr; long = int

from core.item import Item
from core import filetools
from platformcode import config, logger, platformtools
from platformcode.logger import WebErrorException
temp_search_file = config.get_temp_file('temp-search')


def start():
    """ First function that is executed when entering the plugin.
    Within this function all calls should go to
    functions that we want to execute as soon as we open the plugin.
    """
    logger.info()
    # config.set_setting('show_once', True)
    # Test if all the required directories are created
    config.verify_directories_created()
    # check if the user has any connection problems
    # if it has: it does not enter the addon
    # if it has DNS problems start but let in
    # if everything is ok: enter the addon

    from specials.checkhost import test_conn
    import threading
    threading.Thread(target=test_conn, args=(True, not config.get_setting('resolver_dns'), True, [], [], True)).start()

    if not config.dev_mode():
        from platformcode import updater
        updater.showSavedChangelog()

def run(item=None):
    logger.info()
    if not item:
        # Extract item from sys.argv
        if sys.argv[2]:
            sp = sys.argv[2].split('&')
            url = sp[0]
            item = Item().fromurl(url)
            if len(sp) > 1:
                for e in sp[1:]:
                    key, val = e.split('=')
                    item.__setattr__(key, val)
        # If no item, this is mainlist
        else:
            if config.get_setting("start_page"):

                if not config.get_setting("custom_start"):
                    dictCategory = {
                        config.get_localized_string(70137): 'peliculas',
                        config.get_localized_string(30123): 'series',
                        config.get_localized_string(30124): 'anime',
                        config.get_localized_string(60513): 'documentales',
                        config.get_localized_string(70171): 'torrent',
                    }
                    if not config.get_setting("category") in dictCategory.keys():
                        config.set_setting('category', config.get_localized_string(70137))
                    category = dictCategory[config.get_setting("category")]
                    item = Item(channel="news", action="novedades", extra=category, mode = 'silent')
                else:
                    from specials import side_menu
                    item= Item()
                    item = side_menu.check_user_home(item)
                    item.start = True
            else:
                item = Item(channel="channelselector", action="getmainlist", viewmode="movie")
        if not config.get_setting('show_once'):
            from platformcode import xbmc_videolibrary
            xbmc_videolibrary.ask_set_content(silent=False)
            config.set_setting('show_once', True)

    logger.info(item.tostring())

    try:
        if not config.get_setting('tmdb_active'):
            config.set_setting('tmdb_active', True)

        # If item has no action, stops here
        if item.action == "":
            logger.info("Item without action")
            return

        # Action for main menu in channelselector
        elif item.action == "getmainlist":
            import channelselector

            itemlist = channelselector.getmainlist()

            platformtools.render_items(itemlist, item)

        # Action for channel types on channelselector: movies, series, etc.
        elif item.action == "getchanneltypes":
            import channelselector
            itemlist = channelselector.getchanneltypes()

            platformtools.render_items(itemlist, item)

        # Action for channel listing on channelselector
        elif item.action == "filterchannels":
            import channelselector
            itemlist = channelselector.filterchannels(item.channel_type)

            platformtools.render_items(itemlist, item)

        # Special action for playing a video from the library
        elif item.action == "play_from_library":
            play_from_library(item)
            return

        elif item.action == "keymap":
            from platformcode import keymaptools
            if item.open:
                return keymaptools.open_shortcut_menu()
            else:
                return keymaptools.set_key()

        elif item.action == "delete_key":
            from platformcode import keymaptools
            return keymaptools.delete_key()

        elif item.action == "script":
            from core import tmdb
            if tmdb.drop_bd():
                platformtools.dialog_notification(config.get_localized_string(20000), config.get_localized_string(60011), time=2000, sound=False)
        elif item.action == "itemInfo":
            platformtools.dialog_textviewer('Item info', item.parent)
        elif item.action == "open_browser":
            import webbrowser
            if not webbrowser.open(item.url):
                import xbmc
                if xbmc.getCondVisibility('system.platform.linux') and xbmc.getCondVisibility('system.platform.android'):  # android
                    xbmc.executebuiltin('StartAndroidActivity("", "android.intent.action.VIEW", "", "%s")' % (item.url))
                else:
                    try:
                        import urllib.request as urllib
                    except ImportError:
                        import urllib
                    short = urllib.urlopen('https://u.nu/api.php?action=shorturl&format=simple&url=' + item.url).read().decode('utf-8')
                    platformtools.dialog_ok(config.get_localized_string(20000), config.get_localized_string(70740) % short)
        # Action in certain channel specified in "action" and "channel" parameters
        else:
            # Checks if channel exists
            if os.path.isfile(os.path.join(config.get_runtime_path(), 'channels', item.channel + ".py")):
                CHANNELS = 'channels'
            else:
                CHANNELS = 'specials'

            channel_file = os.path.join(config.get_runtime_path(), CHANNELS, item.channel + ".py")

            logger.info("channel_file= " + channel_file + ' - ' + CHANNELS + ' - ' + item.channel)

            channel = None

            if os.path.exists(channel_file):
                try:
                    channel = __import__('%s.%s' % (CHANNELS, item.channel), None, None, ['%s.%s' % (CHANNELS, item.channel)])
                except ImportError:
                    exec("import " + CHANNELS + "." + item.channel + " as channel")

            logger.info("Running channel %s | %s" % (channel.__name__, channel.__file__))

            # Special play action
            if item.action == "play":
                # define la info para trakt
                try:
                    from core import trakt_tools
                    trakt_tools.set_trakt_info(item)
                except:
                    pass
                logger.info("item.action=%s" % item.action.upper())
                # logger.debug("item_toPlay: " + "\n" + item.tostring('\n'))

                # First checks if channel has a "play" function
                if hasattr(channel, 'play'):
                    logger.info("Executing channel 'play' method")
                    itemlist = channel.play(item)
                    b_favourite = item.isFavourite
                    # Play should return a list of playable URLS
                    if len(itemlist) > 0 and isinstance(itemlist[0], Item):
                        item = itemlist[0]
                        if b_favourite:
                            item.isFavourite = True
                        platformtools.play_video(item)

                    # Permitir varias calidades desde play en el Channel
                    elif len(itemlist) > 0 and isinstance(itemlist[0], list):
                        item.video_urls = itemlist
                        platformtools.play_video(item)

                    # If not, shows user an error message
                    else:
                        platformtools.dialog_ok(config.get_localized_string(20000), config.get_localized_string(60339))

                # If player don't have a "play" function, not uses the standard play from platformtools
                else:
                    logger.info("Executing core 'play' method")
                    platformtools.play_video(item)

            # Special action for findvideos, where the plugin looks for known urls
            elif item.action == "findvideos":
                from core import servertools

                # First checks if channel has a "findvideos" function
                if hasattr(channel, 'findvideos'):
                    itemlist = getattr(channel, item.action)(item)

                # If not, uses the generic findvideos function
                else:
                    logger.info("No channel 'findvideos' method, "
                                "executing core method")
                    itemlist = servertools.find_video_items(item)

                if config.get_setting("max_links", "videolibrary") != 0:
                    itemlist = limit_itemlist(itemlist)

                from platformcode import subtitletools
                subtitletools.saveSubtitleName(item)

                platformtools.render_items(itemlist, item)

            # Special action for adding a movie to the library
            elif item.action == "add_pelicula_to_library":
                from core import videolibrarytools
                videolibrarytools.add_movie(item)

            # Special action for adding a serie to the library
            elif item.action == "add_serie_to_library":
                from core import videolibrarytools
                videolibrarytools.add_tvshow(item, channel)

            # Special action for downloading all episodes from a serie
            elif item.action == "download_all_episodes":
                from specials import downloads
                item.action = item.extra
                del item.extra
                downloads.save_download(item)

            # Special action for searching, first asks for the words then call the "search" function
            elif item.action == "search":
                # from core.support import dbg;dbg()
                if filetools.isfile(temp_search_file) and config.get_setting('videolibrary_kodi'):
                    itemlist = []
                    f = filetools.read(temp_search_file)
                    strList = f.split(',')
                    if strList[0] == '[V]' and strList[1] == item.channel:
                        for it in strList:
                            if it and it not in ['[V]', item.channel]:
                                itemlist.append(Item().fromurl(it))
                        filetools.write(temp_search_file, f[4:])
                        return platformtools.render_items(itemlist, item)
                    else:
                        filetools.remove(temp_search_file)

                logger.info("item.action=%s" % item.action.upper())
                from core import channeltools

                if config.get_setting('last_search'):
                    last_search = channeltools.get_channel_setting('Last_searched', 'search', '')
                else:
                    last_search = ''

                search_text = platformtools.dialog_input(last_search)

                if search_text is not None:
                    channeltools.set_channel_setting('Last_searched', search_text, 'search')
                    itemlist = new_search(item.clone(text=search_text), channel)
                else:
                    return

                platformtools.render_items(itemlist, item)

            # For all other actions
            else:
                # import web_pdb; web_pdb.set_trace()
                logger.info("Executing channel '%s' method" % item.action)
                itemlist = getattr(channel, item.action)(item)
                if config.get_setting('trakt_sync'):
                    from core import trakt_tools
                    token_auth = config.get_setting("token_trakt", "trakt")
                    if not token_auth:
                        trakt_tools.auth_trakt()
                    else:
                        import xbmc
                        if not xbmc.getCondVisibility('System.HasAddon(script.trakt)') and config.get_setting('install_trakt'):
                            trakt_tools.ask_install_script()
                    itemlist = trakt_tools.trakt_check(itemlist)
                else:
                    config.set_setting('install_trakt', True)

                platformtools.render_items(itemlist, item)


    except WebErrorException as e:
        import traceback
        from core import scrapertools

        logger.error(traceback.format_exc())

        patron = 'File "' + os.path.join(config.get_runtime_path(), "channels", "").replace("\\", "\\\\") + r'([^.]+)\.py"'
        Channel = scrapertools.find_single_match(traceback.format_exc(), patron)

        platformtools.dialog_ok(
            config.get_localized_string(59985) + Channel,
            config.get_localized_string(60013) %(e))
    except:
        import traceback
        from core import scrapertools

        logger.error(traceback.format_exc())

        patron = 'File "' + os.path.join(config.get_runtime_path(), "channels", "").replace("\\", "\\\\") + r'([^.]+)\.py"'
        Channel = scrapertools.find_single_match(traceback.format_exc(), patron)

        try:
            import xbmc
            if config.get_platform(True)['num_version'] < 14:
                log_name = "xbmc.log"
            else:
                log_name = "kodi.log"
            log_message = config.get_localized_string(50004) + xbmc.translatePath("special://logpath") + log_name
        except:
            log_message = ""

        if Channel:
            if item.url:
                if platformtools.dialog_yesno(config.get_localized_string(60087) % Channel, config.get_localized_string(60014), log_message, nolabel='ok', yeslabel=config.get_localized_string(70739)):
                    run(Item(action="open_browser", url=item.url))
            else:
                platformtools.dialog_ok(config.get_localized_string(60087) % Channel, config.get_localized_string(60014), log_message)
        else:
            platformtools.dialog_ok(
                config.get_localized_string(60038),
                config.get_localized_string(60015),
                log_message)


def new_search(item, channel=None):
    itemlist=[]
    if 'search' in dir(channel):
        itemlist = channel.search(item, item.text)
    else:
        from core import support
        itemlist = support.search(channel, item, item.text)

    writelist = item.channel
    for it in itemlist:
        writelist += ',' + it.tourl()
    filetools.write(temp_search_file, writelist)
    return itemlist

def set_search_temp(item):
    if filetools.isfile(temp_search_file) and config.get_setting('videolibrary_kodi'):
        f = '[V],' + filetools.read(temp_search_file)
        filetools.write(temp_search_file, f)

def reorder_itemlist(itemlist):
    logger.info()
    # logger.debug("Inlet itemlist size: %i" % len(itemlist))

    new_list = []
    mod_list = []
    not_mod_list = []

    modified = 0
    not_modified = 0

    to_change = [[config.get_localized_string(60335), '[V]'], [config.get_localized_string(60336), '[D]']]

    for item in itemlist:
        if not PY3:
            old_title = unicode(item.title, "utf8").lower().encode("utf8")
        else:
            old_title = item.title.lower()
        for before, after in to_change:
            if before in item.title:
                item.title = item.title.replace(before, after)
                break

        if not PY3:
            new_title = unicode(item.title, "utf8").lower().encode("utf8")
        else:
            new_title = item.title.lower()
        if old_title != new_title:
            mod_list.append(item)
            modified += 1
        else:
            not_mod_list.append(item)
            not_modified += 1

            # logger.debug("OLD: %s | NEW: %s" % (old_title, new_title))

    new_list.extend(mod_list)
    new_list.extend(not_mod_list)

    logger.info("Modified Titles:%i |Unmodified:%i" % (modified, not_modified))

    if len(new_list) == 0:
        new_list = itemlist

    # logger.debug("Outlet itemlist size: %i" % len(new_list))
    return new_list


def limit_itemlist(itemlist):
    logger.info()
    # logger.debug("Inlet itemlist size: %i" % len(itemlist))

    try:
        opt = config.get_setting("max_links", "videolibrary")
        if opt == 0:
            new_list = itemlist
        else:
            i_max = 30 * opt
            new_list = itemlist[:i_max]

        # logger.debug("Outlet itemlist size: %i" % len(new_list))
        return new_list
    except:
        return itemlist


def play_from_library(item):
    """
        The .strm files when played from kodi, this expects it to be a "playable" file so it cannot contain
        more items, at most a selection dialog can be placed.
        We solve this by "cheating kodi" and making him believe that something has been reproduced, so later by
        "Container.Update ()" we load the strm as if an item from inside the addon were treated, removing all
        the limitations and allowing to reproduce through the general function without having to create new methods to
        the video library.
        @type item: item
        @param item: item with information
    """
    import xbmcgui, xbmcplugin, xbmc
    from time import sleep

    itemlist=[]
    item.fromLibrary = True
    logger.info()
    # logger.debug("item: \n" + item.tostring('\n'))

    # Try to reproduce an image (this does nothing and also does not give an error)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=os.path.join(config.get_runtime_path(), "resources", "kod.mp4")))
    xbmc.Player().stop()

    # Modify the action (currently the video library needs "findvideos" since this is where the sources are searched
    item.action = "findvideos"

    window_type = config.get_setting("window_type", "videolibrary")
    # and launch kodi again
    if xbmc.getCondVisibility('Window.IsMedia') and not window_type == 1:
        # Conventional window
        xbmc.executebuiltin("Container.Update(" + sys.argv[0] + "?" + item.tourl() + ")")

    else:
        # Pop-up window
        from specials import videolibrary
        p_dialog = platformtools.dialog_progress_bg(config.get_localized_string(20000), config.get_localized_string(60683))
        p_dialog.update(0, '')
        item.play_from = 'window'
        itemlist = videolibrary.findvideos(item)
        p_dialog.update(100, ''); sleep(0.5); p_dialog.close()
        while platformtools.is_playing(): # Conventional window
            sleep(1)
        play_time = platformtools.resume_playback(item, True)
        if not play_time and config.get_setting('autoplay'):
            return

        # The number of links to show is limited
        if config.get_setting("max_links", "videolibrary") != 0: itemlist = limit_itemlist(itemlist)
        # The list of links is slightly "cleaned"
        if config.get_setting("replace_VD", "videolibrary") == 1: itemlist = reorder_itemlist(itemlist)

        if len(itemlist) > 0:
            while not xbmc.Monitor().abortRequested():
                # The user chooses the mirror
                options = []
                selection_implementation = 0
                for item in itemlist:
                    item.thumbnail = config.get_online_server_thumb(item.server)
                    quality = '[B][' + item.quality + '][/B]' if item.quality else ''
                    if item.server:
                        it = xbmcgui.ListItem('\n[B]%s[/B] %s - %s' % (item.server, quality, item.contentTitle))
                        it.setArt({'thumb':item.thumbnail})
                        options.append(it)
                    else:
                        selection_implementation += 1
                # The selection window opens
                if (item.contentSerieName and item.contentSeason and item.contentEpisodeNumber): head = ("%s - %sx%s | %s" % (item.contentSerieName, item.contentSeason, item.contentEpisodeNumber, config.get_localized_string(30163)))
                else: head = config.get_localized_string(30163)
                selection = platformtools.dialog_select(head, options, preselect= -1, useDetails=True)
                if selection == -1:
                    return
                else:
                    item = videolibrary.play(itemlist[selection  + selection_implementation])[0]
                    platformtools.play_video(item)
                if (platformtools.is_playing() and item.action) or item.server == 'torrent' or config.get_setting('autoplay'): break
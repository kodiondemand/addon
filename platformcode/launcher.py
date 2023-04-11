# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# XBMC Launcher (xbmc / kodi)
# ------------------------------------------------------------

import sys, xbmc
from core.item import Item
from core import filetools
from platformcode import config, logger, platformtools
from platformcode.logger import WebErrorException


def start():
    '''
    First function that is executed when entering the plugin.
    Within this function all calls should go to
    functions that we want to execute as soon as we open the plugin.
    '''
    logger.debug()

    if not config.dev_mode():
        try:
            with open(config.changelogFile, 'r') as fileC:
                changelog = fileC.read()
                if changelog.strip() and config.get_setting("addon_update_message"):
                    platformtools.dialog_ok('Kodi on Demand', 'Aggiornamenti applicati:\n' + changelog)
            filetools.remove(config.changelogFile)
        except:
            pass


def run(item=None):
    logger.debug()
    # Extract item from sys.argv
    if not item: item = makeItem()

    # Load or Repare Settings
    if not config.get_setting('show_once'): showOnce()

    # Acrions
    logger.debug(item.tostring())

    try:
        # Active tmdb
        if not config.get_setting('tmdb_active'):
            config.set_setting('tmdb_active', True)

        # If item has no action, stops here
        if item.action == '':
            logger.debug('Item without action')
            return

        # Channel Selector
        if item.channel == 'channelselector':
            itemlist = []
            import channelselector
            if item.action == 'getmainlist': # Action for main menu in channelselector
                itemlist = channelselector.getmainlist()
            elif item.action == 'getchanneltypes': # Action for channel types on channelselector: movies, series, etc.
                itemlist = channelselector.getchanneltypes()
            elif item.action == 'filterchannels': # Action for channel listing on channelselector
                itemlist = channelselector.filterchannels(item.channel_type)
            platformtools.render_items(itemlist, item)


        # Special action for playing a video from the library
        elif item.action == 'play_from_library':
            return playFromLibrary(item)

        # Special play action
        elif item.action == 'play': play(item)

        # Special findvideos Action
        elif item.action == 'findvideos': findvideos(item)

        # Special action for searching, first asks for the words then call the "search" function
        elif item.action == 'search': search(item)

        ######## Following shares must be improved ########

        # Special itemInfo Action
        elif item.action == "itemInfo":
            platformtools.dialog_textviewer('Item info', item.parent)

        # Special action for open item.url in browser
        elif item.action == "open_browser":
            import webbrowser
            if not webbrowser.open(item.url):
                if xbmc.getCondVisibility('system.platform.linux') and xbmc.getCondVisibility('system.platform.android'):  # android
                    xbmc.executebuiltin('StartAndroidActivity("", "android.intent.action.VIEW", "", "%s")' % item.url)
                else:
                    platformtools.dialog_ok(config.get_localized_string(20000), config.get_localized_string(70740) % "\n".join([item.url[j:j+57] for j in range(0, len(item.url), 57)]))

        # Special gotopage Action
        elif item.action == "gotopage":
            page = platformtools.dialog_numeric(0, config.get_localized_string(70513))
            if page:
                item.action = item.real_action
                if item.page:
                    item.page = int(page)
                else:
                    import re
                    item.url = re.sub('([=/])[0-9]+(/?)$', '\g<1>' + page + '\g<2>', item.url)
                xbmc.executebuiltin("Container.Update(%s?%s)" % (sys.argv[0], item.tourl()))

        # Special action for adding a movie to the library
        elif item.action == "add_pelicula_to_library":
            from core import videolibrarytools
            videolibrarytools.add_movie(item)

        # Special action for adding a serie to the library
        elif item.action == "add_serie_to_library":
            channel = importChannel(item)
            from core import videolibrarytools
            videolibrarytools.add_tvshow(item, channel)

        # Special action for adding a undefined to the library
        elif item.action == "add_to_library":
            channel = importChannel(item)
            from core import videolibrarytools
            videolibrarytools.add_to_videolibrary(item, channel)

        # Special action for downloading all episodes from a serie
        elif item.action == "download_all_episodes":
            from specials import downloads
            item.action = item.extra
            del item.extra
            downloads.save_download(item)

        # keymaptools special actions
        elif item.action == "keymap":
            from platformcode import keymaptools
            if item.open:
                return keymaptools.open_shortcut_menu()
            else:
                return keymaptools.set_key()
        elif item.action == "delete_key":
            from platformcode import keymaptools
            return keymaptools.delete_key()

        # delete tmdb cache
        elif item.action == "script":
            from core import tmdb
            tmdb.clean_cache()
            platformtools.dialog_notification(config.get_localized_string(20000), config.get_localized_string(60011), time=2000, sound=False)

        ################################################

        # For all other actions
        else: actions(item)



    except WebErrorException as e:
        import traceback
        from core import scrapertools

        logger.error(traceback.format_exc())

        platformtools.dialog_ok(
            config.get_localized_string(59985) % e.channel,
            config.get_localized_string(60013) % e.url)

    except Exception as e:
        import traceback
        from core import scrapertools

        logger.error(traceback.format_exc())

        patron = r'File "{}([^.]+)\.py"'.format(filetools.join(config.get_runtime_path(), 'channels', '').replace('\\', '\\\\'))
        Channel = scrapertools.find_single_match(traceback.format_exc(), patron)

        if Channel or e.__class__ == logger.ChannelScraperException:
            if item.url:
                if platformtools.dialog_yesno(config.get_localized_string(60087) % Channel, config.get_localized_string(60014), nolabel='ok', yeslabel=config.get_localized_string(70739)):
                    run(Item(action='open_browser', url=item.url))
            else:
                platformtools.dialog_ok(config.get_localized_string(60087) % Channel, config.get_localized_string(60014))
        else:
            if platformtools.dialog_yesno(config.get_localized_string(60038), config.get_localized_string(60015)):
                platformtools.itemlist_update(Item(channel='setting', action='report_menu'), True)
    finally:
        # db need to be closed when not used, it will cause freezes
        from core import db
        db.close()
        import threading
        logger.debug(threading.enumerate())


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
    # filetools.write(temp_search_file, writelist)
    return itemlist


def limitItemlist(itemlist):
    logger.debug()
    try:
        value = config.get_setting('max_links', 'videolibrary')
        if value == 0:
            new_list = itemlist
        else:
            new_list = itemlist[:value]
        return new_list
    except:
        return itemlist


def makeItem():
    logger.debug()
    if sys.argv[2]:
        sp = sys.argv[2].split('&')
        url = sp[0]
        item = Item().fromurl(url)
        if len(sp) > 1:
            for e in sp[1:]:
                key, val = e.split('=')
                if val.lower() == 'false': val = False
                elif val.lower() == 'true': val = True
                item.__setattr__(key, val)
    # If no item, this is mainlist
    else:
        item = Item(channel='channelselector', action='getmainlist', viewmode='movie')

    return item


def showOnce():
    if not config.get_all_settings_addon():
        logger.error('corrupted settings.xml!!')
        settings_xml = filetools.join(config.get_data_path(), 'settings.xml')
        settings_bak = filetools.join(config.get_data_path(), 'settings.bak')
        if filetools.exists(settings_bak):
            filetools.copy(settings_bak, settings_xml, True)
            logger.info('restored settings.xml from backup')
        else:
            filetools.write(settings_xml, '<settings version="2">\n</settings>')  # resetted settings
    else:
        from platformcode import xbmc_videolibrary
        xbmc_videolibrary.ask_set_content(silent=False)
        config.set_setting('show_once', True)


def play(item):
    channel = importChannel(item)

    # define info for trakt
    try:
        from core import trakt_tools
        trakt_tools.set_trakt_info(item)
    except:
        pass
    logger.debug('item.action=', item.action.upper())

    # First checks if channel has a "play" function
    if hasattr(channel, 'play'):
        logger.debug('Executing channel "play" method')
        itemlist = channel.play(item)
        # Play should return a list of playable URLS
        if len(itemlist) > 0 and isinstance(itemlist[0], Item):
            item = itemlist[0]
            platformtools.play_video(item)

        # Allow several qualities from Play in El Channel
        elif len(itemlist) > 0 and isinstance(itemlist[0], list):
            item.video_urls = itemlist
            platformtools.play_video(item)

        # If not, shows user an error message
        else:
            platformtools.dialog_ok(config.get_localized_string(20000), config.get_localized_string(60339))

    # If player don't have a "play" function, not uses the standard play from platformtools
    else:
        logger.debug('Executing core "play" method')
        platformtools.play_video(item)


def findvideos(item, itemlist=[]):
    if not itemlist:
        logger.debug('Executing channel', item.channel, 'method', item.action)
        channel = importChannel(item)
        from core import servertools

        p_dialog = platformtools.dialog_progress_bg(config.get_localized_string(20000), config.get_localized_string(60683))
        p_dialog.update(0)

        try:
            # First checks if channel has a "findvideos" function
            if hasattr(channel, 'findvideos'):
                itemlist = getattr(channel, item.action)(item)

            # If not, uses the generic findvideos function
            else:
                logger.debug('No channel "findvideos" method, executing core method')
                itemlist = servertools.find_video_items(item)

            itemlist = limitItemlist(itemlist)
        except Exception as ex:
            import traceback
            logger.error(traceback.format_exc())

        p_dialog.update(100)
        p_dialog.close()

    serverlist = [s for s in itemlist if s.server or s.contentChannel == 'local']

    if itemlist and not serverlist:
        platformtools.render_items(itemlist, item)
    if not serverlist:
        platformtools.dialog_notification(config.get_localized_string(20000), config.get_localized_string(60347))
    elif len(serverlist) == 1:
        # If there is only one server play it immediately
        from core import db
        db['player']['itemlist'] = []
        db.close()
        play(itemlist[0].clone(no_return=True))
    else:
        platformtools.serverWindow(item, itemlist)


def search(item):
    channel = importChannel(item)
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


def addToLibrary(item):
    channel = importChannel(item)
    from core import videolibrarytools
    videolibrarytools.add_to_videolibrary(item, channel)


def importChannel(item):
    channel = platformtools.channelImport(item.channel)
    if not channel:
        logger.debug('Channel', item.channel, 'not exist!')
        return

    logger.debug('Running channel', channel.__name__,  '|', channel.__file__)
    return channel


def actions(item):
    logger.debug('Executing channel', item.channel, 'method', item.action)
    channel = importChannel(item)
    itemlist = getattr(channel, item.action)(item)
    if type(itemlist) == list:
        if config.get_setting('trakt_sync'):
            from core import trakt_tools
            token_auth = config.get_setting('token_trakt', 'trakt')
            if not token_auth:
                trakt_tools.auth_trakt()
            else:
                if not xbmc.getCondVisibility('System.HasAddon(script.trakt)') and config.get_setting('install_trakt'):
                    trakt_tools.ask_install_script()
            itemlist = trakt_tools.trakt_check(itemlist)
        else:
            config.set_setting('install_trakt', True)

        if item.action in ['check'] and len([s for s in itemlist if s.server]) > 0:
            findvideos(item, itemlist)
        else:
            platformtools.render_items(itemlist, item)


def playFromLibrary(item):
    if not item.next_ep: platformtools.fakeVideo()
    item.action = item.next_action if item.next_action else 'findvideos'
    logger.debug('Executing channel', item.channel, 'method', item.action)
    return run(item)

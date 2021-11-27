# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# XBMC Launcher (xbmc / kodi)
# ------------------------------------------------------------

import sys
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

    if not config.devMode():
        try:
            with open(config.changelogFile, 'r') as fileC:
                changelog = fileC.read()
                if changelog.strip():
                    platformtools.dialogOk('Kodi on Demand', 'Aggiornamenti applicati:\n' + changelog)
            filetools.remove(config.changelogFile)
        except:
            pass


def run(item=None):
    logger.debug()

    # Extract item from sys.argv
    if not item: item = makeItem()

    # Load or Repare Settings
    if not config.getSetting('show_once'): showOnce()

    # Acrions
    logger.debug(item.tostring())

    try:
        # Active tmdb
        if not config.getSetting('tmdb_active'):
            config.setSetting('tmdb_active', True)

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
            platformtools.renderItems(itemlist, item)


        # Special action for playing a video from the library
        elif item.action in ['playFromLibrary', 'play_from_library']:
            return playFromLibrary(item)

        # Special play action
        elif item.action == 'play': play(item)

        # Special findvideos Action
        elif item.action == 'findvideos': findvideos(item)

        # Special action for adding a movie or serie to the library
        elif item.action == 'add_to_library': addToLibrary(item)

        # Special action for searching, first asks for the words then call the "search" function
        elif item.action == 'search': search(item)

        # For all other actions
        else: actions(item)



    except WebErrorException as e:
        import traceback
        from core import scrapertools

        logger.error(traceback.format_exc())

        platformtools.dialogOk(
            config.getLocalizedString(59985) % e.channel,
            config.getLocalizedString(60013) % e.url)

    except Exception as e:
        import traceback
        from core import scrapertools

        logger.error(traceback.format_exc())

        patron = r'File "{}([^.]+)\.py"'.format(filetools.join(config.getRuntimePath(), 'channels', '').replace('\\', '\\\\'))
        Channel = scrapertools.find_single_match(traceback.format_exc(), patron)

        if Channel or e.__class__ == logger.ChannelScraperException:
            if item.url:
                if platformtools.dialogYesNo(config.getLocalizedString(60087) % Channel, config.getLocalizedString(60014), nolabel='ok', yeslabel=config.getLocalizedString(70739)):
                    run(Item(action='open_browser', url=item.url))
            else:
                platformtools.dialogOk(config.getLocalizedString(60087) % Channel, config.getLocalizedString(60014))
        else:
            if platformtools.dialogYesNo(config.getLocalizedString(60038), config.getLocalizedString(60015)):
                platformtools.itemlistUpdate(Item(channel='setting', action='report_menu'), True)
    finally:
        # db need to be closed when not used, it will cause freezes
        from core import db, videolibrarydb
        videolibrarydb.close()
        db.close()


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

# def set_search_temp(item):
#     if filetools.isfile(temp_search_file) and config.getSetting('videolibrary_kodi'):
#         f = '[V],' + filetools.read(temp_search_file)
#         filetools.write(temp_search_file, f)


def limitItemlist(itemlist):
    logger.debug()
    try:
        value = config.getSetting('max_links', 'videolibrary')
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
    if not config.getAllSettingsAddon():
        logger.error('corrupted settings.xml!!')
        settings_xml = filetools.join(config.getDataPath(), 'settings.xml')
        settings_bak = filetools.join(config.getDataPath(), 'settings.bak')
        if filetools.exists(settings_bak):
            filetools.copy(settings_bak, settings_xml, True)
            logger.info('restored settings.xml from backup')
        else:
            filetools.write(settings_xml, '<settings version="2">\n</settings>')  # resetted settings
    else:
        from platformcode import xbmc_videolibrary
        xbmc_videolibrary.ask_set_content(silent=False)
        config.setSetting('show_once', True)


def play(item):
    channel = importChannel(item)
    # platformtools.fakeVideo()
    # define la info para trakt
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
            platformtools.playVideo(item)

        # Allow several qualities from Play in El Channel
        elif len(itemlist) > 0 and isinstance(itemlist[0], list):
            item.videoUrls = itemlist
            platformtools.playVideo(item)

        # If not, shows user an error message
        else:
            platformtools.dialogOk(config.getLocalizedString(20000), config.getLocalizedString(60339))

    # If player don't have a "play" function, not uses the standard play from platformtools
    else:
        logger.debug('Executing core "play" method')
        platformtools.playVideo(item)


def findvideos(item):
    logger.debug('Executing channel', item.channel, 'method', item.action)
    channel = importChannel(item)
    from core import servertools

    p_dialog = platformtools.dialogProgressBg(config.getLocalizedString(20000), config.getLocalizedString(60683))
    p_dialog.update(0)

    # First checks if channel has a "findvideos" function
    if hasattr(channel, 'findvideos'):
        itemlist = getattr(channel, item.action)(item)

    # If not, uses the generic findvideos function
    else:
        logger.debug('No channel "findvideos" method, executing core method')
        itemlist = servertools.find_video_items(item)

    itemlist = limitItemlist(itemlist)

    p_dialog.update(100)
    p_dialog.close()

    # If there is only one server play it immediately
    if len(itemlist) == 1 or len(itemlist) > 1 and not itemlist[1].server:
        play(itemlist[0].clone(no_return=True))
    else:
        platformtools.serverWindow(item, itemlist)


def search(item):
    channel = importChannel(item)
    from core import channeltools

    if config.getSetting('last_search'):
        last_search = channeltools.getChannelSetting('Last_searched', 'search', '')
    else:
        last_search = ''

    search_text = platformtools.dialogInput(last_search)

    if search_text is not None:
        channeltools.setChannelSetting('Last_searched', search_text, 'search')
        itemlist = new_search(item.clone(text=search_text), channel)
    else:
        return

    platformtools.renderItems(itemlist, item)


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
    if config.getSetting('trakt_sync'):
        from core import trakt_tools
        token_auth = config.getSetting('token_trakt', 'trakt')
        if not token_auth:
            trakt_tools.auth_trakt()
        else:
            import xbmc
            if not xbmc.getCondVisibility('System.HasAddon(script.trakt)') and config.getSetting('install_trakt'):
                trakt_tools.ask_install_script()
        itemlist = trakt_tools.trakt_check(itemlist)
    else:
        config.setSetting('install_trakt', True)

    platformtools.renderItems(itemlist, item)


def playFromLibrary(item):
    platformtools.fakeVideo()
    item.action = item.next_action if item.next_action else 'findvideos'
    logger.debug('Executing channel', item.channel, 'method', item.action)
    return run(item)

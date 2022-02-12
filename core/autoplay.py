# -*- coding: utf-8 -*-

from core import filetools, jsontools
from core.item import Item
from platformcode import config, logger, platformtools
from time import sleep

__channel__ = "autoplay"

PLAYED = False

quality_list = ['4k', '2160p', '2160', '4k2160p', '4k2160', '4k 2160p', '4k 2160', '2k',
                'fullhd', 'fullhd 1080', 'fullhd 1080p', 'full hd', 'full hd 1080', 'full hd 1080p', 'hd1080', 'hd1080p', 'hd 1080', 'hd 1080p', '1080', '1080p',
                'hd', 'hd720', 'hd720p', 'hd 720', 'hd 720p', '720', '720p', 'hdtv',
                'sd', '480p', '480', '360p', '360', '240p', '240',
                'default']


def start(itemlist, item):
    '''
    Main method from which the links are automatically reproduced
    - In case the option to activate it will use the options defined by the user.
    - Otherwise it will try to reproduce any link that has the preferred language.

    :param itemlist: list (list of items ready to play, ie with action = 'play')
    :param item: item (the main item of the channel)
    :return: try to auto-reproduce, in case of failure it returns the itemlist that it received in the beginning
    '''

    if item.global_search or item.from_action or item.contentAction:  # from_action means that's a special function calling this (ex: add to videolibrary)
        return itemlist
    if len([s for s in itemlist if s.server]) == 1:
        return itemlist
    logger.debug()

    global PLAYED
    PLAYED = False

    base_item = item

    if not config.is_xbmc():
        return itemlist

    import xbmc
    control_info = xbmc.getInfoLabel('Container.FolderPath')
    if control_info:
        control_item = Item().fromurl(control_info)
        if control_item.action == item.action:
            return itemlist

    if config.get_setting('autoplay') or item.autoplay:
        # Save the current value of "Action and Player Mode" in preferences
        user_config_setting_action = config.get_setting("default_action")
        # user_config_setting_player = config.get_setting("player_mode")

        # Enable the "View in high quality" action (if the server returns more than one quality, eg gdrive)
        if not user_config_setting_action: config.set_setting("default_action", 2)

        from core.servertools import sort_servers
        autoplay_list = sort_servers(itemlist)

        if autoplay_list:
            max_intents = 5
            max_intents_servers = {}

            # If something is playing it stops playing
            if platformtools.is_playing():
                platformtools.stop_video()

            for autoplay_elem in autoplay_list:
                play_item = Item
                channel_id = autoplay_elem.channel
                if autoplay_elem.channel == 'videolibrary':
                    channel_id = autoplay_elem.contentChannel

                if not platformtools.is_playing() and not PLAYED:
                    videoitem = autoplay_elem
                    if videoitem.server.lower() not in max_intents_servers:
                        max_intents_servers[videoitem.server.lower()] = max_intents

                    # If the maximum number of attempts of this server have been reached, we jump to the next
                    if max_intents_servers[videoitem.server.lower()] == 0:
                        continue

                    lang = " [{}]".format(videoitem.language) if videoitem.language else ''
                    quality = ' [{}]'.format(videoitem.quality) if videoitem.quality and videoitem.quality != 'default' else ''
                    name = servername(videoitem.server) 
                    platformtools.dialog_notification('AutoPlay', '{}{}{}'.format(name, lang, quality), sound=False)

                    # Try to play the links If the channel has its own play method, use it
                    try: channel = __import__('channels.%s' % channel_id, None, None, ["channels.%s" % channel_id])
                    except: channel = __import__('specials.%s' % channel_id, None, None, ["specials.%s" % channel_id])
                    if hasattr(channel, 'play'):
                        resolved_item = getattr(channel, 'play')(videoitem)
                        if len(resolved_item) > 0:
                            if isinstance(resolved_item[0], list): videoitem.video_urls = resolved_item
                            else: videoitem = resolved_item[0]

                    play_item.autoplay = True
                    # If not directly reproduce and mark as seen
                    # Check if the item comes from the video library
                    try:
                        if base_item.contentChannel == 'videolibrary' or base_item.nfo:
                            # Fill the video with the data of the main item and play
                            play_item = base_item.clone(**videoitem.__dict__)
                            platformtools.play_video(play_item, autoplay=True)
                        else:
                            videoitem.window = base_item.window
                            # If it doesn't come from the video library, just play
                            platformtools.play_video(videoitem, autoplay=True)
                    except:
                        pass
                    # sleep(3)
                    try:
                        if platformtools.is_playing():
                            PLAYED = True
                            break
                    except:
                        logger.debug(str(len(autoplay_list)))

                    # If we have come this far, it is because it could not be reproduced
                    max_intents_servers[videoitem.server.lower()] -= 1

                    # If the maximum number of attempts of this server has been reached, ask if we want to continue testing or ignore it.
                    if max_intents_servers[videoitem.server.lower()] == 0:
                        text = config.get_localized_string(60072) % name
                        if not platformtools.dialog_yesno("AutoPlay", text, config.get_localized_string(60073)):
                            max_intents_servers[videoitem.server.lower()] = max_intents

                    # If there are no items in the list, it is reported
                    if autoplay_elem == autoplay_list[-1] and autoplay_elem.server != 'torrent':
                        platformtools.dialog_notification('AutoPlay', config.get_localized_string(60072) % name)

        else:
            platformtools.dialog_notification(config.get_localized_string(60074), config.get_localized_string(60075))

        # Restore if necessary the previous value of "Action and Player Mode" in preferences
        if not user_config_setting_action: config.set_setting("default_action", user_config_setting_action)
        # if user_config_setting_player != 0: config.set_setting("player_mode", user_config_setting_player)

    return itemlist


def play_multi_channel(item, itemlist):
    logger.debug()
    start(itemlist, item)


def servername(server):
    from core.servertools import translate_server_name
    path = filetools.join(config.get_runtime_path(), 'servers', server.lower() + '.json')
    name = jsontools.load(open(path, "rb").read())['name']
    if name.startswith('@'): name = config.get_localized_string(int(name.replace('@','')))
    return translate_server_name(name)

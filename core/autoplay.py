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

    if item.global_search:
        return itemlist
    logger.debug()

    global PLAYED
    PLAYED = False

    base_item = item

    if not config.is_xbmc():
        return itemlist

    if config.get_setting('autoplay'):
        url_list_valid = []
        autoplay_list = []
        autoplay_b = []
        favorite_quality = []
        favorite_servers = []
        blacklisted_servers = config.get_setting("black_list", server='servers', default = [])
        favorite_servers = config.get_setting('favorites_servers_list', server='servers', default = [])

        from core import servertools

        servers_list = list(servertools.get_servers_list().items())
        for server, server_parameters in servers_list:
            if config.get_setting('favorites_servers_list', server=server) and server.lower() not in favorite_servers:
                favorite_servers.append(server.lower())

        if not favorite_servers:
            config.set_setting('favorites_servers_list', [], server='servers')
            favorite_servers = []
        else:
            s_list = []
            for s in favorite_servers:
                if s not in blacklisted_servers:
                    s_list.append(s)
            favorite_servers = s_list

        # Save the current value of "Action and Player Mode" in preferences
        user_config_setting_action = config.get_setting("default_action")
        # user_config_setting_player = config.get_setting("player_mode")

        # Enable the "View in high quality" action (if the server returns more than one quality, eg gdrive)
        if not user_config_setting_action: config.set_setting("default_action", 2)

        # if user_config_setting_player != 0: config.set_setting("player_mode", 0)

        # Priorities when ordering itemlist:
        #       0: Servers and qualities
        #       1: Qualities and servers
        #       2: Servers only
        #       3: Only qualities
        #       4: Do not order

        if config.get_setting('favorites_servers') and favorite_servers and config.get_setting('default_action'):
            priority = 0  # 0: Servers and qualities or 1: Qualities and servers
        elif config.get_setting('favorites_servers') and favorite_servers:
            priority = 2  # Servers only
        elif config.get_setting('default_action'):
            priority = 3  # Only qualities
        else:
            priority = 4  # Do not order

        if config.get_setting('default_action') == 1:
            quality_list.reverse()
        favorite_quality = quality_list
        for item in itemlist:
            autoplay_elem = dict()
            b_dict = dict()

            # We check that it is a video item
            if 'server' not in item:
                continue

            if item.server.lower() in blacklisted_servers:
                continue

            # If it does not have a defined quality, it assigns a 'default' quality.
            if item.quality.lower() not in quality_list:
                item.quality = 'default'
            # The list for custom settings is created

            if priority < 2:  # 0: Servers and qualities or 1: Qualities and servers

                # if the server and the quality are not in the favorites lists or the url is repeated, we discard the item
                if item.server.lower() not in favorite_servers or item.quality.lower() not in favorite_quality or item.url in url_list_valid:
                    item.type_b = True
                    item.window = base_item.window
                    b_dict['videoitem']= item
                    autoplay_b.append(b_dict)
                    continue
                autoplay_elem["indice_server"] = favorite_servers.index(item.server.lower())
                autoplay_elem["indice_quality"] = favorite_quality.index(item.quality.lower())

            elif priority == 2:  # Servers only

                # if the server is not in the favorites list or the url is repeated, we discard the item
                if item.server.lower() not in favorite_servers or item.url in url_list_valid:
                    item.type_b = True
                    item.window = base_item.window
                    b_dict['videoitem'] = item
                    autoplay_b.append(b_dict)
                    continue
                autoplay_elem["indice_server"] = favorite_servers.index(item.server.lower())

            elif priority == 3:  # Only qualities

                # if the quality is not in the favorites list or the url is repeated, we discard the item
                if item.quality.lower() not in favorite_quality or item.url in url_list_valid:
                    item.type_b = True
                    item.window = base_item.window
                    b_dict['videoitem'] = item
                    autoplay_b.append(b_dict)
                    continue
                autoplay_elem["indice_quality"] = favorite_quality.index(item.quality.lower())

            else:  # Do not order

                # if the url is repeated, we discard the item
                item.window = base_item.window
                if item.url in url_list_valid:
                    continue

            # If the item reaches here we add it to the list of valid urls and to autoplay_list
            url_list_valid.append(item.url)
            item.plan_b=True
            item.window = base_item.window
            autoplay_elem['videoitem'] = item
            autoplay_list.append(autoplay_elem)

        # We order according to priority
        if priority == 0: autoplay_list.sort(key=lambda orden: ((orden['indice_server'], orden['indice_quality']))) # Servers and qualities
        elif priority == 1: autoplay_list.sort(key=lambda orden: (orden['indice_quality'], orden['indice_server'])) # Qualities and servers
        elif priority == 2: autoplay_list.sort(key=lambda orden: (orden['indice_server'])) # Servers only
        elif priority == 3: autoplay_list.sort(key=lambda orden: (orden['indice_quality'])) # Only qualities

        logger.debug('PRIORITY',priority, autoplay_list)

        # if quality priority is active
        if priority == 0 and config.get_setting('quality_priority'):
            max_quality = autoplay_list[0]["indice_quality"] if autoplay_list and "indice_quality" in autoplay_list[0] else 0
            for n, item in enumerate(itemlist):
                if 'server' not in item:
                    continue

                if item.server.lower() in blacklisted_servers:
                    continue

                # If it does not have a defined quality, it assigns a 'default' quality.
                if item.quality == '':
                    item.quality = 'default'

                if favorite_quality.index(item.quality.lower()) < max_quality:
                    item.type_b = False
                    autoplay_elem["indice_server"] = n
                    autoplay_elem["indice_quality"] = favorite_quality.index(item.quality.lower())
                    autoplay_elem['videoitem'] = item
                    autoplay_list.append(autoplay_elem)
            autoplay_list.sort(key=lambda orden: (orden['indice_quality'], orden['indice_server']))

        # Plan b is prepared, in case it is active the non-favorite elements are added at the end
        # try: plan_b = settings_node['plan_b']
        # except: 
        plan_b = True
        text_b = ''
        if plan_b: autoplay_list.extend(autoplay_b)
        # If there are elements in the autoplay list, an attempt is made to reproduce each element, until one is found or all fail.

        if autoplay_list or (plan_b and autoplay_b):

            max_intentos = 5
            max_intentos_servers = {}

            # If something is playing it stops playing
            if platformtools.is_playing():
                platformtools.stop_video()

            for autoplay_elem in autoplay_list:
                play_item = Item
                channel_id = autoplay_elem['videoitem'].channel
                if autoplay_elem['videoitem'].channel == 'videolibrary':
                    channel_id = autoplay_elem['videoitem'].contentChannel

                # If it is not a favorite element if you add the text plan b
                if autoplay_elem['videoitem'].type_b:
                    text_b = '(Plan B)'
                if not platformtools.is_playing() and not PLAYED:
                    videoitem = autoplay_elem['videoitem']
                    if videoitem.server.lower() not in max_intentos_servers:
                        max_intentos_servers[videoitem.server.lower()] = max_intentos

                    # If the maximum number of attempts of this server have been reached, we jump to the next
                    if max_intentos_servers[videoitem.server.lower()] == 0:
                        continue

                    lang = " "
                    if hasattr(videoitem, 'language') and videoitem.language != "":
                        lang = " '%s' " % videoitem.language
                    name = servername(videoitem.server) 
                    platformtools.dialog_notification("AutoPlay %s" %text_b, "%s%s%s" % (name, lang, videoitem.quality.upper()), sound=False)

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
                    sleep(3)
                    try:
                        if platformtools.is_playing():
                            PLAYED = True
                            break
                    except:
                        logger.debug(str(len(autoplay_list)))

                    # If we have come this far, it is because it could not be reproduced
                    max_intentos_servers[videoitem.server.lower()] -= 1

                    # If the maximum number of attempts of this server has been reached, ask if we want to continue testing or ignore it.
                    if max_intentos_servers[videoitem.server.lower()] == 0:
                        text = config.get_localized_string(60072) % name
                        if not platformtools.dialog_yesno("AutoPlay", text, config.get_localized_string(60073)):
                            max_intentos_servers[videoitem.server.lower()] = max_intentos

                    # If there are no items in the list, it is reported
                    if autoplay_elem == autoplay_list[-1]:
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
# -*- coding: utf-8 -*-

#from builtins import str
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int
from builtins import range

import os

from core import channeltools, jsontools
from core.item import Item
from platformcode import config, logger, platformtools, launcher
from time import sleep
from platformcode.config import get_setting

__channel__ = "autoplay"

PLAYED = False

autoplay_node = {}

colorKOD = '0xFF65B3DA'


def context():
    '''
    Add the Configure AutoPlay option to the context menu

    :return:
    '''

    _context = ""

    if config.is_xbmc():
        _context = [{"title": config.get_localized_string(60071),
                     "action": "autoplay_config",
                     "channel": "autoplay"}]
    return _context


context = context()


def show_option(channel, itemlist, text_color=colorKOD, thumbnail=None, fanart=None):
    '''
    Add the option Configure AutoPlay in the received list

    :param channel: str
    :param itemlist: list (lista donde se desea integrar la opcion de configurar AutoPlay)
    :param text_color: str (color for the text of the option Configure Autoplay)
    :param thumbnail: str (address where the thumbnail is for the Configure Autoplay option)
    :return:
    '''
    from channelselector import get_thumb
    from core.support import typo
    logger.info()

    if not config.is_xbmc():
        return itemlist

    if thumbnail == None:
        thumbnail = get_thumb('autoplay.png')
    # if fanart == None:
    #     fanart = get_thumb('autoplay.png')

    plot_autoplay = config.get_localized_string(60399)
    itemlist.append(
        Item(channel=__channel__,
             title=typo(config.get_localized_string(60071), 'bold color kod'),
             action="autoplay_config",
             text_color=text_color,
             text_bold=True,
             thumbnail=thumbnail,
            #  fanart=fanart,
             plot=plot_autoplay,
             from_channel=channel,
             folder=False
             ))
    return itemlist


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
    logger.info()

    global PLAYED
    global autoplay_node
    PLAYED = False

    base_item = item

    
    if not config.is_xbmc():
        # platformtools.dialog_notification('AutoPlay ERROR', 'Sólo disponible para XBMC/Kodi')
        return itemlist

    if not autoplay_node:
        # Get AUTOPLAY node from json
        autoplay_node = jsontools.get_node_from_file('autoplay', 'AUTOPLAY')

    channel_id = item.channel
    if item.channel == 'videolibrary':
        autoplay_node = jsontools.get_node_from_file('autoplay', 'AUTOPLAY')
        channel_id = item.contentChannel
    # try:
    #     active = autoplay_node['status']
    # except:
    #     active = is_active(item.channel)

    if not channel_id in autoplay_node: # or not active:
        return itemlist

    # Add servers and qualities not listed to autoplay_node
    new_options = check_value(channel_id, itemlist)

    # Get the channel node from autoplay_node
    channel_node = autoplay_node.get(channel_id, {})
    # Get the autoplay settings for this channel
    settings_node = channel_node.get('settings', {})

    if get_setting('autoplay') or settings_node['active']:
        url_list_valid = []
        autoplay_list = []
        autoplay_b = []
        favorite_langs = []
        favorite_servers = []
        favorite_quality = []

        # 2nd lang, see if you want to filter or not
        status_language = config.get_setting("filter_languages", channel_id)


        # Save the current value of "Action and Player Mode" in preferences
        user_config_setting_action = config.get_setting("default_action")
        user_config_setting_player = config.get_setting("player_mode")
        # Enable the "View in high quality" action (if the server returns more than one quality, eg gdrive)
        if user_config_setting_action != 2:
            config.set_setting("default_action", 2)
        if user_config_setting_player != 0:
            config.set_setting("player_mode", 0)

        # Report that AutoPlay is active
        # platformtools.dialog_notification('AutoPlay Activo', '', sound=False)

        # Priorities when ordering itemlist:
        #       0: Servers and qualities
        #       1: Qualities and servers
        #       2: Servers only
        #       3: Only qualities
        #       4: Do not order
        if (settings_node['custom_servers'] and settings_node['custom_quality']) or get_setting('autoplay'):
            priority = settings_node['priority']  # 0: Servers and qualities or 1: Qualities and servers
        elif settings_node['custom_servers']:
            priority = 2  # Servers only
        elif settings_node['custom_quality']:
            priority = 3  # Only qualities
        else:
            priority = 4  # Do not order

        # Get server lists, qualities available from AutoPlay json node
        server_list = channel_node.get('servers', [])
        for server in server_list:
            server = server.lower()
        quality_list = channel_node.get('quality', [])

        # If no qualities are defined, default is assigned as unique quality.
        if len(quality_list) == 0:
            quality_list =['default']

        # The texts of each server and quality are stored in lists, e.g. favorite_servers = ['verystream', 'openload', 'streamcloud']
        for num in range(1, 4):
            favorite_servers.append(channel_node['servers'][settings_node['server_%s' % num]].lower())
            favorite_quality.append(channel_node['quality'][settings_node['quality_%s' % num]])

        # Itemlist links are filtered and correspond to autoplay values
        for n, item in enumerate(itemlist):
            autoplay_elem = dict()
            b_dict = dict()

            # We check that it is a video item
            if 'server' not in item:
                continue
            # 2nd lang language list
            if item.language not in favorite_langs:
                favorite_langs.append(item.language)

            # Add the option to configure AutoPlay to the context menu
            if 'context' not in item:
                item.context = list()
            if not [x for x in context if x['action'] == 'autoplay_config']:
                item.context.append({"title": config.get_localized_string(60071),
                                     "action": "autoplay_config",
                                     "channel": "autoplay",
                                     "from_channel": channel_id})

            # If it does not have a defined quality, it assigns a 'default' quality.
            if item.quality == '':
                item.quality = 'default'

            # The list for custom settings is created
            if priority < 2:  # 0: Servers and qualities or 1: Qualities and servers

                # if the server and the quality are not in the favorites lists or the url is repeated, we discard the item
                if item.server.lower() not in favorite_servers or item.quality not in favorite_quality \
                        or item.url in url_list_valid:
                    item.type_b = True
                    b_dict['videoitem']= item
                    autoplay_b.append(b_dict)
                    continue
                autoplay_elem["indice_lang"] = favorite_langs.index(item.language)
                autoplay_elem["indice_server"] = favorite_servers.index(item.server.lower())
                autoplay_elem["indice_quality"] = favorite_quality.index(item.quality)

            elif priority == 2:  # Servers only

                # if the server is not in the favorites list or the url is repeated, we discard the item
                if item.server.lower() not in favorite_servers or item.url in url_list_valid:
                    item.type_b = True
                    b_dict['videoitem'] = item
                    autoplay_b.append(b_dict)
                    continue
                autoplay_elem["indice_lang"] = favorite_langs.index(item.language)
                autoplay_elem["indice_server"] = favorite_servers.index(item.server.lower())

            elif priority == 3:  # Solo calidades

                # if the quality is not in the favorites list or the url is repeated, we discard the item
                if item.quality not in favorite_quality or item.url in url_list_valid:
                    item.type_b = True
                    b_dict['videoitem'] = item
                    autoplay_b.append(b_dict)
                    continue
                autoplay_elem["indice_lang"] = favorite_langs.index(item.language)
                autoplay_elem["indice_quality"] = favorite_quality.index(item.quality)

            else:  # Do not order

                # if the url is repeated, we discard the item
                if item.url in url_list_valid:
                    continue

            # If the item reaches here we add it to the list of valid urls and to autoplay_list
            url_list_valid.append(item.url)
            item.plan_b=True
            autoplay_elem['videoitem'] = item
            # autoplay_elem['server'] = item.server
            # autoplay_elem['quality'] = item.quality
            autoplay_list.append(autoplay_elem)

        # We order according to priority
        if priority == 0:  # Servers and qualities
            autoplay_list.sort(key=lambda orden: (orden['indice_lang'], orden['indice_server'], orden['indice_quality']))

        elif priority == 1:  # Qualities and servers
            autoplay_list.sort(key=lambda orden: (orden['indice_lang'], orden['indice_quality'], orden['indice_server']))

        elif priority == 2:  # Servers only
            autoplay_list.sort(key=lambda orden: (orden['indice_lang'], orden['indice_server']))

        elif priority == 3:  # Only qualities
            autoplay_list.sort(key=lambda orden: (orden['indice_lang'], orden['indice_quality']))

        # Plan b is prepared, in case it is active the non-favorite elements are added at the end
        try:
            plan_b = settings_node['plan_b']
        except:
            plan_b = True
        text_b = ''
        if plan_b:
            autoplay_list.extend(autoplay_b)
        # If there are elements in the autoplay list, an attempt is made to reproduce each element, until one is found or all fail.

        if autoplay_list or (plan_b and autoplay_b):

            # played = False
            max_intentos = 5
            max_intentos_servers = {}

            # If something is playing it stops playing
            if platformtools.is_playing():
                platformtools.stop_video()

            for autoplay_elem in autoplay_list:
                play_item = Item

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

                    platformtools.dialog_notification("AutoPlay %s" %text_b, "%s%s%s" % (
                        videoitem.server.upper(), lang, videoitem.quality.upper()), sound=False)
                    # TODO videoitem.server is the id of the server, but it might not be the name !!!

                    # Try to play the links If the channel has its own play method, use it
                    try:
                        channel = __import__('channels.%s' % channel_id, None, None, ["channels.%s" % channel_id])
                    except:
                        channel = __import__('specials.%s' % channel_id, None, None, ["specials.%s" % channel_id])
                    if hasattr(channel, 'play'):
                        resolved_item = getattr(channel, 'play')(videoitem)
                        if len(resolved_item) > 0:
                            if isinstance(resolved_item[0], list):
                                videoitem.video_urls = resolved_item
                            else:
                                videoitem = resolved_item[0]

                    # If not directly reproduce and mark as seen

                    #Check if the item comes from the video library
                    try:
                        if base_item.contentChannel =='videolibrary':
                            # Mark as seen
                            from platformcode import xbmc_videolibrary
                            xbmc_videolibrary.mark_auto_as_watched(base_item)
                            # Fill the video with the data of the main item and play
                            play_item = base_item.clone(url=videoitem)
                            platformtools.play_video(play_item.url, autoplay=True)
                        else:
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
                        text = config.get_localized_string(60072) % videoitem.server.upper()
                        if not platformtools.dialog_yesno("AutoPlay", text, config.get_localized_string(60073)):
                            max_intentos_servers[videoitem.server.lower()] = max_intentos

                    # If there are no items in the list, it is reported
                    if autoplay_elem == autoplay_list[-1]:
                         platformtools.dialog_notification('AutoPlay', config.get_localized_string(60072) % videoitem.server.upper())

        else:
            platformtools.dialog_notification(config.get_localized_string(60074), config.get_localized_string(60075))
        if new_options:
            platformtools.dialog_notification("AutoPlay", config.get_localized_string(60076), sound=False)

        # Restore if necessary the previous value of "Action and Player Mode" in preferences
        if user_config_setting_action != 2:
            config.set_setting("default_action", user_config_setting_action)
        if user_config_setting_player != 0:
            config.set_setting("player_mode", user_config_setting_player)

    return itemlist


def init(channel, list_servers, list_quality, reset=False):
    '''
    Check the existence of a channel in the Autoplay configuration file and if it does not exist, add it.
    It is necessary to call this function when entering any channel that includes the Autoplay function.

    :param channel: (str) channel id
    :param list_servers: (list) initial list of valid servers for the channel. It is not necessary to include them all,
        since the list of valid servers will be updated dynamically.
    :param list_quality: (list) initial list of valid qualities for the channel. It is not necessary to include them all,
        since the list of valid qualities will be updated dynamically.
    :return: (bool) True if the initialization was successful.
    '''
    logger.info()
    change = False
    result = True


    if not config.is_xbmc():
        # platformtools.dialog_notification('AutoPlay ERROR', 'Sólo disponible para XBMC/Kodi')
        result = False
    else:
        autoplay_path = os.path.join(config.get_data_path(), "settings_channels", 'autoplay_data.json')
        if os.path.exists(autoplay_path):
            autoplay_node = jsontools.get_node_from_file('autoplay', "AUTOPLAY")
        else:
            change = True
            autoplay_node = {"AUTOPLAY": {}}

        if channel not in autoplay_node or reset:
            change = True

            # It is verified that there are no duplicate qualities or servers
            if 'default' not in list_quality:
                list_quality.append('default')
            # list_servers = list(set(list_servers))
            # list_quality = list(set(list_quality))

            # We create the channel node and add it
            channel_node = {"servers": list_servers,
                            "quality": list_quality,
                            "settings": {
                                "active": False,
                                "hide_servers": False,
                                "plan_b": True,
                                "custom_servers": False,
                                "custom_quality": False,
                                "priority": 0}}
            for n in range(1, 4):
                s = c = 0
                if len(list_servers) >= n:
                    s = n - 1
                if len(list_quality) >= n:
                    c = n - 1

                channel_node["settings"]["server_%s" % n] = s
                channel_node["settings"]["quality_%s" % n] = c
            autoplay_node[channel] = channel_node

        if change:
            result, json_data = jsontools.update_node(autoplay_node, 'autoplay', 'AUTOPLAY')

            if not result:
                heading = config.get_localized_string(60077)
                msj = config.get_localized_string(60078)

                platformtools.dialog_notification(heading, msj, sound=False)

    return result


def check_value(channel, itemlist):
    ''' 
    checks the existence of a value in the list of servers or qualities if it does not exist adds them to the list in the json

    :param channel: str
    :param values: list (one of servers or qualities)
    :param value_type: str (server o quality)
    :return: list
    '''
    logger.info()
    global autoplay_node
    change = False

    if not autoplay_node:
        # Get AUTOPLAY node from json
        autoplay_node = jsontools.get_node_from_file('autoplay', 'AUTOPLAY')

    channel_node = autoplay_node.get(channel)

    server_list = channel_node.get('servers')
    if not server_list:
        server_list = channel_node['servers'] = list()

    quality_list = channel_node.get('quality')
    if not quality_list:
        quality_list = channel_node['quality'] = list()

    for item in itemlist:
        if item.server.lower() not in server_list and item.server !='':
            server_list.append(item.server.lower())
            change = True
        if item.quality not in quality_list and item.quality !='':
            quality_list.append(item.quality)
            change = True

    if change:
        change, json_data = jsontools.update_node(autoplay_node, 'autoplay', 'AUTOPLAY')

    return change


def autoplay_config(item):
    logger.info()
    global autoplay_node
    dict_values = {}
    list_controls = []
    channel_parameters = channeltools.get_channel_parameters(item.from_channel)
    channel_name = channel_parameters['title']

    if not autoplay_node:
        # Get AUTOPLAY node from json
        autoplay_node = jsontools.get_node_from_file('autoplay', 'AUTOPLAY')

    channel_node = autoplay_node.get(item.from_channel, {})
    settings_node = channel_node.get('settings', {})

    allow_option = True

    active_settings = {"id": "active", "label": config.get_localized_string(60079), "type": "bool",
                       "default": False, "enabled": allow_option, "visible": allow_option}

    list_controls.append(active_settings)
    dict_values['active'] = settings_node.get('active', False)

    hide_servers = {"id": "hide_servers", "label": config.get_localized_string(70747), "type": "bool",
                    "default": False, "enabled": "eq(-" + str(len(list_controls)) + ",true)", "visible": allow_option}

    list_controls.append(hide_servers)
    dict_values['hide_servers'] = settings_node.get('hide_servers', False)

    # Language
    status_language = config.get_setting("filter_languages", item.from_channel)
    if not status_language:
        status_language = 0

    set_language = {"id": "language", "label": config.get_localized_string(60080),
                    "type": "list", "default": 0, "enabled": "eq(-" + str(len(list_controls)) + ",true)", "visible": True,
                    "lvalues": get_languages(item.from_channel)}

    list_controls.append(set_language)
    dict_values['language'] = status_language

    separador = {"id": "label", "label": "         "
                                         "_________________________________________________________________________________________",
                 "type": "label", "enabled": True, "visible": True}
    list_controls.append(separador)

    # Favorite servers section
    server_list = channel_node.get("servers", [])
    if not server_list:
        enabled = False
        server_list = ["No disponible"]
    else:
        enabled = "eq(-" + str(len(list_controls)) + ",true)"

    custom_servers_settings = {"id": "custom_servers", "label": config.get_localized_string(60081),
                               "type": "bool", "default": False, "enabled": enabled, "visible": True}
    custom_servers_pos = len(list_controls)
    list_controls.append(custom_servers_settings)
    if dict_values['active'] and enabled:
        dict_values['custom_servers'] = settings_node.get('custom_servers', False)
    else:
        dict_values['custom_servers'] = False

    for num in range(1, 4):
        pos1 = num + custom_servers_pos
        default = num - 1
        if default > len(server_list) - 1:
            default = 0
        set_servers = {"id": "server_%s" % num, "label": u"          \u2665" + config.get_localized_string(60082) % num,
                       "type": "list", "default": default,
                       "enabled": "eq(-%s,true)+eq(-%s,true)" % (pos1, num), "visible": True,
                       "lvalues": server_list}
        list_controls.append(set_servers)

        dict_values["server_%s" % num] = settings_node.get("server_%s" % num, 0)
        if settings_node.get("server_%s" % num, 0) > len(server_list) - 1:
            dict_values["server_%s" % num] = 0

    # Favorite Qualities Section
    quality_list = channel_node.get("quality", [])
    if not quality_list:
        enabled = False
        quality_list = ["No disponible"]
    else:
        enabled = "eq(-" + str(len(list_controls)) + ",true)"

    custom_quality_settings = {"id": "custom_quality", "label": config.get_localized_string(60083), "type": "bool", "default": False, "enabled": enabled, "visible": True}
    custom_quality_pos = len(list_controls)
    list_controls.append(custom_quality_settings)
    if dict_values['active'] and enabled:
        dict_values['custom_quality'] = settings_node.get('custom_quality', False)
    else:
        dict_values['custom_quality'] = False

    for num in range(1, 4):
        pos1 = num + custom_quality_pos
        default = num - 1
        if default > len(quality_list) - 1:
            default = 0

        set_quality = {"id": "quality_%s" % num, "label": u"          \u2665 " + config.get_localized_string(707417) + " %s" % num,
                       "type": "list", "default": default,
                       "enabled": "eq(-%s,true)+eq(-%s,true)" % (pos1, num), "visible": True,
                       "lvalues": quality_list}
        list_controls.append(set_quality)
        dict_values["quality_%s" % num] = settings_node.get("quality_%s" % num, 0)
        if settings_node.get("quality_%s" % num, 0) > len(quality_list) - 1:
            dict_values["quality_%s" % num] = 0

    # Plan B
    dict_values['plan_b'] = settings_node.get('plan_b', False)
    enabled = "eq(-" + str(custom_servers_pos) + ",true)|eq(-" + str(custom_quality_pos) + ",true)"
    plan_b = {"id": "plan_b", "label": config.get_localized_string(70172),"type": "bool", "default": False, "enabled": enabled, "visible": True}
    list_controls.append(plan_b)


    # Priorities Section
    priority_list = [config.get_localized_string(70174), config.get_localized_string(70175)]
    set_priority = {"id": "priority", "label": config.get_localized_string(60085), "type": "list", "default": 0,
                    "enabled": True, "visible": "eq(-5,true)+eq(-9,true)+eq(-12,true)", "lvalues": priority_list}
    list_controls.append(set_priority)
    dict_values["priority"] = settings_node.get("priority", 0)



    # Open dialog box
    platformtools.show_channel_settings(list_controls=list_controls, dict_values=dict_values, callback='save',
                                        item=item, caption='%s - AutoPlay' % channel_name,
                                        custom_button={'visible': True,
                                                       'function': "reset",
                                                        'close': True,
                                                        'label': 'Reset'})


def save(item, dict_data_saved):
    '''
    Save the data from the configuration window

    :param item: item
    :param dict_data_saved: dict
    :return:
    '''
    logger.info()
    global autoplay_node

    if not autoplay_node:
        # Get AUTOPLAY node from json
        autoplay_node = jsontools.get_node_from_file('autoplay', 'AUTOPLAY')

    new_config = dict_data_saved
    if not new_config['active']:
        new_config['language']=0
    channel_node = autoplay_node.get(item.from_channel)
    config.set_setting("filter_languages", dict_data_saved.pop("language"), item.from_channel)
    channel_node['settings'] = dict_data_saved

    result, json_data = jsontools.update_node(autoplay_node, 'autoplay', 'AUTOPLAY')


    return result


def get_languages(channel):
    '''
    Get the languages ​​from the channel's json

    :param channel: str
    :return: list
    '''
    logger.info()
    list_language = ['Non filtrare']
    list_controls, dict_settings = channeltools.get_channel_controls_settings(channel)
    for control in list_controls:
        try:
            if control["id"] == 'filter_languages':
                list_language = control["lvalues"]
        except:
            pass

    return list_language


def is_active(channel):
    '''
    Returns a boolean that indicates whether or not autoplay is active on the channel from which it is called

    :return:True if autoplay is active for the channel from which it is called, False otherwise.
    '''
    logger.info()
    global autoplay_node

    if not config.is_xbmc():
        return False

    if not autoplay_node:
        # Get AUTOPLAY node from json
        autoplay_node = jsontools.get_node_from_file('autoplay', 'AUTOPLAY')

        # Get the channel from which the call is made
        #import inspect
        #module = inspect.getmodule(inspect.currentframe().f_back)
        #canal = module.__name__.split('.')[1]
    canal = channel

    # Get the channel node from autoplay_node
    channel_node = autoplay_node.get(canal, {})
    # Get the autoplay settings for this channel
    settings_node = channel_node.get('settings', {})

    return settings_node.get('active', False) or get_setting('autoplay')


def reset(item, dict):

    channel_name = item.from_channel
    channel = __import__('channels.%s' % channel_name, fromlist=["channels.%s" % channel_name])
    list_servers = channel.list_servers
    list_quality = channel.list_quality

    init(channel_name, list_servers, list_quality, reset=True)
    platformtools.dialog_notification('AutoPlay', config.get_localized_string(70523) % item.category)

    return

# def set_status(status):
#     logger.info()
#     # Get AUTOPLAY node from json
#     autoplay_node = jsontools.get_node_from_file('autoplay', 'AUTOPLAY')
#     autoplay_node['status'] = status
#
#     result, json_data = jsontools.update_node(autoplay_node, 'autoplay', 'AUTOPLAY')

# return if item channel has autoplay and hideserver enabled
def get_channel_AP_HS(item):
    autoplay_node = jsontools.get_node_from_file('autoplay', 'AUTOPLAY')
    channel_node = autoplay_node.get(item.channel, {})
    if not channel_node:  # never opened the channel menu so in autoplay_data.json there is no key
        try:
            channelFile = __import__('channels.' + item.channel, fromlist=["channels.%s" % item.channel])
        except:
            channelFile = __import__('specials.' + item.channel, fromlist=["specials.%s" % item.channel])
        if hasattr(channelFile, 'list_servers') and hasattr(channelFile, 'list_quality'):
            init(item.channel, channelFile.list_servers, channelFile.list_quality)

    autoplay_node = jsontools.get_node_from_file('autoplay', 'AUTOPLAY')
    channel_node = autoplay_node.get(item.channel, {})
    settings_node = channel_node.get('settings', {})
    AP = get_setting('autoplay') or (settings_node['active'] if 'active' in settings_node else False)
    HS = config.get_setting('hide_servers') or (
        settings_node['hide_servers'] if 'hide_server' in settings_node else False)

    return AP, HS

def play_multi_channel(item, itemlist):
    logger.info()
    global PLAYED
    video_dict = dict()
    # set_status(True)

    for video_item in itemlist:
        if is_active(video_item.contentChannel):
            if video_item.contentChannel not in video_dict.keys():
                video_dict[video_item.contentChannel] = [video_item]
            else:
                video_dict[video_item.contentChannel].append(video_item)

    for channel, videos in video_dict.items():
        item.contentChannel = channel
        if not PLAYED:
            start(videos, item)
        else:
            break

    AP, HS = get_channel_AP_HS(item)
    return HS
# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# channeltools - Tools for working with channels
# ------------------------------------------------------------

from __future__ import absolute_import

from core import jsontools
from platformcode import config, logger

DEFAULT_UPDATE_URL = "/channels/"
dict_channels_parameters = dict()
default_file = dict()

remote_path = 'https://raw.githubusercontent.com/kodiondemand/media/master/'

def is_enabled(channel_name):
    logger.debug("channel_name=" + channel_name)
    return get_channel_parameters(channel_name)["active"] and get_channel_setting("enabled", channel=channel_name,
                                                                                  default=True)


def get_channel_parameters(channel_name):
    from core import filetools
    global dict_channels_parameters

    if channel_name not in dict_channels_parameters:
        try:
            channel_parameters = get_channel_json(channel_name)
            logger.debug(channel_parameters)
            if channel_parameters:
                # name and default changes
                channel_parameters["title"] = channel_parameters.pop("name") + (' [DEPRECATED]' if 'deprecated' in channel_parameters and channel_parameters['deprecated'] else '')
                channel_parameters["channel"] = channel_parameters.pop("id")

                # if the key does not exist, they are declared a default value so that there are no failures in the functions that call it
                channel_parameters["update_url"] = channel_parameters.get("update_url", DEFAULT_UPDATE_URL)
                channel_parameters["language"] = channel_parameters.get("language", ["all"])
                channel_parameters["active"] = channel_parameters.get("active", False)
                channel_parameters["include_in_global_search"] = channel_parameters.get("include_in_global_search",
                                                                                        False)
                channel_parameters["categories"] = channel_parameters.get("categories", list())

                channel_parameters["thumbnail"] = channel_parameters.get("thumbnail", "")
                channel_parameters["banner"] = channel_parameters.get("banner", "")
                channel_parameters["fanart"] = channel_parameters.get("fanart", "")

                # Images: url and local files are allowed inside "resources / images"
                if channel_parameters.get("thumbnail") and "://" not in channel_parameters["thumbnail"]:
                    channel_parameters["thumbnail"] = filetools.join(remote_path, "resources", "thumb", channel_parameters["thumbnail"])
                if channel_parameters.get("banner") and "://" not in channel_parameters["banner"]:
                    channel_parameters["banner"] = filetools.join(remote_path, "resources", "banner", channel_parameters["banner"])
                if channel_parameters.get("fanart") and "://" not in channel_parameters["fanart"]:
                    channel_parameters["fanart"] = filetools.join(remote_path, "resources", channel_parameters["fanart"])

                # We obtain if the channel has configuration options
                channel_parameters["has_settings"] = False
                if 'settings' in channel_parameters:
                    channel_parameters['settings'] = get_default_settings(channel_name)
                    for s in channel_parameters['settings']:
                        if 'id' in s:
                            if s['id'] == "include_in_global_search":
                                channel_parameters["include_in_global_search"] = True
                            elif s['id'] == "filter_languages":
                                channel_parameters["filter_languages"] = s.get('lvalues', [])
                            elif s['id'].startswith("include_in_"):
                                channel_parameters["has_settings"] = True

                    del channel_parameters['settings']

                dict_channels_parameters[channel_name] = channel_parameters

            else:
                # To avoid cases where channels are not defined as configuration, we throw the exception and thus we have the basic values
                raise Exception

        except Exception as ex:
            logger.error(channel_name + ".json error \n%s" % ex)
            channel_parameters = dict()
            channel_parameters["channel"] = ""
            channel_parameters['active'] = False
            channel_parameters["language"] = ""
            channel_parameters["update_url"] = DEFAULT_UPDATE_URL
            return channel_parameters

    return dict_channels_parameters[channel_name]


def get_channel_json(channel_name):
    logger.debug("channel_name=" + channel_name)
    from core import filetools
    channel_json = None
    try:
        channel_path = filetools.join(config.get_runtime_path(), "channels", channel_name + ".json")
        if not filetools.isfile(channel_path):
            channel_path = filetools.join(config.get_runtime_path(), "specials", channel_name + ".json")
            if not filetools.isfile(channel_path):
                channel_path = filetools.join(config.get_runtime_path(), "servers", channel_name + ".json")
                if not filetools.isfile(channel_path):
                    channel_path = filetools.join(config.get_runtime_path(), "servers", "debriders",
                                                  channel_name + ".json")

        if filetools.isfile(channel_path):
            logger.debug("channel_data=" + channel_path)
            channel_json = jsontools.load(filetools.read(channel_path))
            logger.debug("channel_json= %s" % channel_json)

    except Exception as ex:
        template = "An exception of type %s occured. Arguments:\n%r"
        message = template % (type(ex).__name__, ex.args)
        logger.error(" %s" % message)

    return channel_json


def get_channel_controls_settings(channel_name):
    logger.debug("channel_name=" + channel_name)
    dict_settings = {}
    # import web_pdb; web_pdb.set_trace()
    # list_controls = get_channel_json(channel_name).get('settings', list())
    list_controls = get_default_settings(channel_name)

    for c in list_controls:
        if 'id' not in c or 'type' not in c or 'default' not in c:
            # If any control in the list does not have id, type or default, we ignore it
            continue

        # new dict with key(id) and value(default) from settings
        dict_settings[c['id']] = c['default']

    return list_controls, dict_settings


def get_lang(channel_name):
    channel = __import__('channels.%s' % channel_name, fromlist=["channels.%s" % channel_name])
    list_language = [config.get_localized_string(70522)]
    if hasattr(channel, 'list_language'):
        for language in channel.list_language:
            list_language.append(language)
        logger.debug(list_language)
    else:
        sub = False
        langs = []
        language = get_channel_json(channel_name).get('language', list())
        for lang in language:
            if 'vos' not in lang:
                langs.append(lang.upper())
            else:
                sub = True
        if sub == True:
            for lang in langs:
                list_language.append(lang)
                list_language.append('Sub-' + lang)
        else:
            for lang in langs:
                list_language.append(lang)
    return list_language


def get_default_settings(channel_name):
    from core import filetools
    import copy

    default_path = filetools.join(config.get_runtime_path(), 'default_channel_settings' + '.json')
    if channel_name not in ['trakt', 'autoplay']:
        global default_file
    else:
        default_file = {}
    if not default_file:
        default_file = jsontools.load(filetools.read(default_path))

    channel_path = filetools.join(config.get_runtime_path(), 'channels', channel_name + '.json')

    # from core.support import dbg; dbg()
    if filetools.exists(channel_path):
        default_controls = default_file['settings']
        default_controls_renumber = default_file['renumber']
        channel_json = get_channel_json(channel_name)

        # Collects configurations
        channel_language = channel_json['language']
        channel_controls = channel_json['settings']
        categories = channel_json['categories']
        not_active = channel_json['not_active'] if 'not_active' in channel_json else []
        default_off = channel_json['default_off'] if 'default_off' in channel_json else []

        # Apply default configurations if they do not exist
        for control in copy.deepcopy(default_controls):
            if control['id'] not in str(channel_controls):
                if 'include_in_newest' in control['id'] and 'include_in_newest' not in not_active and control[
                    'id'] not in not_active:
                    label = control['id'].split('_')
                    label = label[-1]
                    if label == 'peliculas':
                        if 'movie' in categories:
                            control['label'] = config.get_localized_string(70727) + ' - ' + config.get_localized_string( 30122)
                            control['default'] = False if ('include_in_newest' in default_off) or ( ' include_in_newest_peliculas' in default_off) else True
                            channel_controls.append(control)
                        else:
                            pass
                    elif label == 'series':
                        if 'tvshow' in categories:
                            control['label'] = config.get_localized_string(70727) + ' - ' + config.get_localized_string( 30123)
                            control['default'] = False if ('include_in_newest' in default_off) or ( 'include_in_newest_series' in default_off) else True
                            channel_controls.append(control)
                        else:
                            pass
                    elif label == 'anime':
                        if 'anime' in categories:
                            control['label'] = config.get_localized_string(70727) + ' - ' + config.get_localized_string( 30124)
                            control['default'] = False if ('include_in_newest' in default_off) or ( 'include_in_newest_anime' in default_off) else True
                            channel_controls.append(control)
                        else:
                            pass

                    else:
                        control['label'] = config.get_localized_string(70727) + ' - ' + label.capitalize()
                        control['default'] = control['default'] if control['id'] not in default_off else False
                        channel_controls.append(control)

                elif control['id'] not in not_active and 'include_in_newest' not in control['id']:
                    if type(control['default']) == bool:
                        control['default'] = control['default'] if control['id'] not in default_off else False
                    channel_controls.append(control)

        if 'anime' in categories:
            for control in default_controls_renumber:
                if control['id'] not in str(channel_controls):
                    channel_controls.append(control)
                else:
                    pass
    else:
        return get_channel_json(channel_name).get('settings', list())
    return channel_controls


def get_channel_setting(name, channel, default=None):
    from core import filetools
    """
    Returns the configuration value of the requested parameter.

    Returns the value of the parameter 'name' in the own configuration of the channel 'channel'.

    Look in the path \addon_data\plugin.video.kod\settings_channels for the file channel_data.json and read
    the value of the parameter 'name'. If the file channel_data.json does not exist look in the channels folder for the file
    channel.json and create a channel_data.json file before returning the requested value. If the parameter 'name'
    also does not exist in the channel.json file the default parameter is returned.


    @param name: parameter name
    @type name: str
    @param channel: channel name
    @type channel: str
    @param default: return value in case the name parameter does not exist
    @type default: any

    @return: The value of the parameter 'name'
    @rtype: any

    """
    file_settings = filetools.join(config.get_data_path(), "settings_channels", channel + "_data.json")
    dict_settings = {}
    dict_file = {}

    if filetools.exists(file_settings):
        # We get saved configuration from ../settings/channel_data.json
        try:
            dict_file = jsontools.load(filetools.read(file_settings))
            if isinstance(dict_file, dict) and 'settings' in dict_file:
                dict_settings = dict_file['settings']
        except EnvironmentError:
            logger.error("ERROR when reading the file: %s" % file_settings)

    if not dict_settings or name not in dict_settings:
        # We get controls from the file ../channels/channel.json
        try:
            list_controls, default_settings = get_channel_controls_settings(channel)
        except:
            default_settings = {}

        if name in default_settings:  #If the parameter exists in the channel.json we create the channel_data.json
            default_settings.update(dict_settings)
            dict_settings = default_settings
            dict_file['settings'] = dict_settings
            # We create the file ../settings/channel_data.json
            json_data = jsontools.dump(dict_file)
            if not filetools.write(file_settings, json_data, silent=True):
                logger.error("ERROR saving file: %s" % file_settings)

    # We return the value of the local parameter 'name' if it exists, if default is not returned
    return dict_settings.get(name, default)


def set_channel_setting(name, value, channel):
    from core import filetools
    """
    Sets the configuration value of the indicated parameter.

    Set 'value' as the value of the parameter 'name' in the own configuration of the channel 'channel'.
    Returns the changed value or None if the assignment could not be completed.

    If the name of the channel is specified, search in the path \addon_data\plugin.video.kod\settings_channels the
    channel_data.json file and set the parameter 'name' to the value indicated by 'value'.
    If the parameter 'name' does not exist, it adds it, with its value, to the corresponding file.

    @param name: parameter name
    @type name: str
    @param value: parameter value
    @type value: str
    @param channel: channel name
    @type channel: str

    @return: 'value' if the value could be set and None otherwise
    @rtype: str, None

    """
    # We create the folder if it does not exist
    if not filetools.exists(filetools.join(config.get_data_path(), "settings_channels")):
        filetools.mkdir(filetools.join(config.get_data_path(), "settings_channels"))

    file_settings = filetools.join(config.get_data_path(), "settings_channels", channel + "_data.json")
    dict_settings = {}

    dict_file = None

    if filetools.exists(file_settings):
        # We get saved settings from ../settings/channel_data.json
        try:
            dict_file = jsontools.load(filetools.read(file_settings))
            dict_settings = dict_file.get('settings', {})
        except EnvironmentError:
            logger.error("ERROR when reading the file: %s" % file_settings)

    dict_settings[name] = value

    # we check if dict_file exists and it is a dictionary, if not we create it
    if dict_file is None or not dict_file:
        dict_file = {}

    dict_file['settings'] = dict_settings

    # Creamos el archivo ../settings/channel_data.json
    json_data = jsontools.dump(dict_file)
    if not filetools.write(file_settings, json_data, silent=True):
        logger.error("ERROR saving file: %s" % file_settings)
        return None

    return value

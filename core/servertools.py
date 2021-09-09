# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# Server management
# --------------------------------------------------------------------------------

from __future__ import division
from __future__ import absolute_import
import sys
import os
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3: import urllib.parse as urlparse
else: import urlparse

from lib.future.builtins import range
from lib.past.utils import old_div

import re

from core import filetools, httptools, jsontools
from core.item import Item
from platformcode import config, logger, platformtools
from lib import unshortenit
import requests

dict_servers_parameters = {}
server_list = {}


def find_video_items(item=None, data=None):
    """
    Generic function to search for videos on a page, returning an itemlist with the ready-to-use items.
     - If an Item is passed as an argument, the resulting items keep the parameters of the last item
     - If an Item is not passed, a new one is created, but it will not contain any parameters other than those of the server.

    @param item: Item to which you want to search for videos, this must contain the valid url
    @type item: Item
    @param data: String with the page content already downloaded (if item is not passed)
    @type data: str

    @return: returns the itemlist with the results
    @rtype: list
    """
    logger.debug()
    itemlist = []

    # Download the page
    if data is None:
        data = httptools.downloadpage(item.url).data

    data = unshortenit.findlinks(data)

    # Create an item if there is no item
    if item is None:
        item = Item()
    # Pass the thumbnail and title fields to contentThumbnail and contentTitle
    else:
        if not item.contentThumbnail:
            item.contentThumbnail = item.thumbnail
        if not item.contentTitle:
            item.contentTitle = item.title

    # Find the links to the videos
    for label, url, server, thumbnail in findvideos(data):
        title = label
        itemlist.append(
            item.clone(title=title, action="play", url=url, thumbnail=thumbnail, server=server, folder=False))

    return itemlist


def get_servers_itemlist(itemlist, fnc=None, sort=False):
    """
    Get the server for each of the items, based on their url.
     - Assign the server, the modified url, the thumbnail (if the item does not contain contentThumbnail the thumbnail is assigned)
     - If a function is passed through the fnc argument, it is executed by passing the item as an argument, the result of that function is assigned to the title of the item
     - In this function we can modify anything of the item
     - This function always has to return the item.title as a result
     - If no server is found for a url, it is assigned "direct"

    @param itemlist: item list
    @type itemlist: list
    @param fnc: function to execute with each item (to assign the title)
    @type fnc: function
    @param sort: indicates whether the resulting list should be ordered based on the list of favorite servers
    @type sort: bool
    """
    # Roam the servers
    for serverid in list(get_servers_list().keys()):
        server_parameters = get_server_parameters(serverid)

        # Walk the patterns
        for pattern in server_parameters.get("find_videos", {}).get("patterns", []):
            logger.debug(pattern["pattern"])
            # Scroll through the results
            for match in re.compile(pattern["pattern"], re.DOTALL).finditer(
                    "\n".join([item.url.split('|')[0] for item in itemlist if not item.server])):
                url = pattern["url"]
                for x in range(len(match.groups())):
                    url = url.replace("\\%s" % (x + 1), match.groups()[x])

                for item in itemlist:
                    if match.group() in item.url:
                        if not item.contentThumbnail:
                            item.contentThumbnail = item.thumbnail
                        item.thumbnail = server_parameters.get("thumbnail", "")
                        item.server = serverid
                        if '|' in item.url:
                            item.url = url + '|' + item.url.split('|')[1]
                        else:
                            item.url = url

    # We remove the deactivated servers
    # itemlist = filter(lambda i: not i.server or is_server_enabled(i.server), itemlist)

    for item in itemlist:
        # We assign "direct" in case the server is not in KoD
        if not item.server and item.url:
            item.server = "directo"

        if fnc:
            item.title = fnc(item)


    # Sort according to favoriteslist if necessary
    if sort:
        itemlist = sort_servers(itemlist)

    return itemlist


def findvideos(data, skip=False):
    """
    Scroll through the list of available servers and run the findvideosbyserver function for each of them
    :param data: Text where to look for the links
    :param skip: Indicates a limit to stop scrolling through the list of servers. It can be a boolean in which case
    It would be False to go through the whole list (default value) or True to stop after the first server that
    return some link. It can also be an integer greater than 1, which would represent the maximum number of links to search.
    :return:
    """
    logger.debug()
    devuelve = []
    skip = int(skip)
    servers_list = list(get_servers_list().keys())
    # Run findvideos on each active server
    for serverid in servers_list:
        if is_server_enabled(serverid) :
            devuelve.extend(findvideosbyserver(data, serverid))
            if skip and len(devuelve) >= skip:
                devuelve = devuelve[:skip]
                break
    return devuelve


def findvideosbyserver(data, serverid):
    serverid = get_server_name(serverid)
    if not serverid:
        return []

    server_parameters = get_server_parameters(serverid)
    if not server_parameters["active"]:
        return []
    devuelve = []
    if "find_videos" in server_parameters:
        # Walk the patterns
        for pattern in server_parameters["find_videos"].get("patterns", []):
            msg = "%s\npattern: %s" % (serverid, pattern["pattern"])
            # Scroll through the results
            for match in re.compile(pattern["pattern"], re.DOTALL).finditer(data):
                url = pattern["url"]
                # Create the url with the data
                for x in range(len(match.groups())):
                    url = url.replace("\\%s" % (x + 1), match.groups()[x])
                msg += "\nfound url: %s" % url
                value = translate_server_name(server_parameters["name"]) , url, serverid, server_parameters.get("thumbnail", "")
                if value not in devuelve and url not in server_parameters["find_videos"].get("ignore_urls", []):
                    devuelve.append(value)
                logger.debug(msg)

    return devuelve


def guess_server_thumbnail(serverid):
    server = get_server_name(serverid)
    server_parameters = get_server_parameters(server)
    return server_parameters.get('thumbnail', "")


def get_server_from_url(url):
    logger.debug()
    servers_list = list(get_servers_list().keys())

    # Run findvideos on each active server
    for serverid in servers_list:
        '''if not is_server_enabled(serverid):
            continue'''
        serverid = get_server_name(serverid)
        if not serverid:
            continue
        server_parameters = get_server_parameters(serverid)
        if not server_parameters["active"]:
            continue
        if "find_videos" in server_parameters:
            # Walk the patterns
            for n, pattern in enumerate(server_parameters["find_videos"].get("patterns", [])):
                msg = "%s\npattern: %s" % (serverid, pattern["pattern"])
                if not "pattern_compiled" in pattern:
                    # logger.debug('compiled ' + serverid)
                    pattern["pattern_compiled"] = re.compile(pattern["pattern"])
                    dict_servers_parameters[serverid]["find_videos"]["patterns"][n]["pattern_compiled"] = pattern["pattern_compiled"]
                # Scroll through the results
                match = re.search(pattern["pattern_compiled"], url)
                if match:
                    url = pattern["url"]
                    # Create the url with the data
                    for x in range(len(match.groups())):
                        url = url.replace("\\%s" % (x + 1), match.groups()[x])
                    msg += "\nurl encontrada: %s" % url
                    value = translate_server_name(server_parameters["name"]), url, serverid, server_parameters.get("thumbnail", "")
                    if url not in server_parameters["find_videos"].get("ignore_urls", []):
                        logger.debug(msg)
                        return value

    return None


def resolve_video_urls_for_playing(server, url, video_password="", muestra_dialogo=False, background_dialog=False):
    """
    Function to get the real url of the video
    @param server: Server where the video is hosted
    @type server: str
    @param url: video url
    @type url: str
    @param video_password: Password for the video
    @type video_password: str
    @param muestra_dialogo: Show progress dialog
    @type muestra_dialogo: bool
    @type background_dialog: bool
    @param background_dialog: if progress dialog should be in background

    @return: returns the url of the video
    @rtype: list
    """
    logger.info("Server: %s, Url: %s" % (server, url))

    server = server.lower()

    video_urls = []
    video_exists = True
    error_messages = []
    opciones = []

    # If the video is "direct" or "local", look no further
    if server == "directo" or server == "local":
        if isinstance(video_password, list):
            return video_password, len(video_password) > 0, "<br/>".join(error_messages)
        logger.info("Server: %s, url is good" % server)
        video_urls.append(["%s [%s]" % (urlparse.urlparse(url)[2][-4:], config.get_localized_string(30137)), url])

    # Find out the video URL
    else:
        if server:
            server_parameters = get_server_parameters(server)
        else:
            server_parameters = {}

        if server_parameters:
            # Show a progress dialog
            if muestra_dialogo:
                progreso = (platformtools.dialog_progress_bg if background_dialog else platformtools.dialog_progress)(config.get_localized_string(20000), config.get_localized_string(70180) % translate_server_name(server_parameters["name"]))

            # Count the available options, to calculate the percentage

            orden = [
                ["free"] + [server] + [premium for premium in server_parameters["premium"] if not premium == server],
                [server] + [premium for premium in server_parameters["premium"] if not premium == server] + ["free"],
                [premium for premium in server_parameters["premium"] if not premium == server] + [server] + ["free"]
            ]

            if server_parameters["free"] == True:
                opciones.append("free")
            opciones.extend(
                [premium for premium in server_parameters["premium"] if config.get_setting("premium", server=premium)])

            priority = int(config.get_setting("resolve_priority"))
            opciones = sorted(opciones, key=lambda x: orden[priority].index(x))

            logger.info("Available options: %s | %s" % (len(opciones), opciones))
        else:
            logger.error("There is no connector for the server %s" % server)
            error_messages.append(config.get_localized_string(60004) % server)
            muestra_dialogo = False

        # Import the server
        try:
            server_module = __import__('servers.%s' % server, None, None, ["servers.%s" % server])
            logger.info("Imported server: %s" % server_module)
        except:
            server_module = None
            if muestra_dialogo:
                progreso.close()
            logger.error("Could not import server: %s" % server)
            import traceback
            logger.error(traceback.format_exc())

        # If it has a function to see if the video exists, check it now
        if hasattr(server_module, 'test_video_exists'):
            logger.info("Invoking a %s.test_video_exists" % server)
            try:
                video_exists, message = server_module.test_video_exists(page_url=url)

                if not video_exists:
                    error_messages.append(message)
                    logger.info("test_video_exists says video doesn't exist")
                    if muestra_dialogo:
                        progreso.close()
                else:
                    logger.info("test_video_exists says the video DOES exist")
            except:
                logger.error("Could not verify if the video exists")
                import traceback
                logger.error(traceback.format_exc())

        # If the video exists and the free mode is available, we get the url
        if video_exists:
            for opcion in opciones:
                # Own free and premium option uses the same server
                if opcion == "free" or opcion == server:
                    serverid = server_module
                    server_name = translate_server_name(server_parameters["name"])

                # Rest of premium options use a debrider
                else:
                    serverid = __import__('servers.debriders.%s' % opcion, None, None,
                                          ["servers.debriders.%s" % opcion])
                    server_name = get_server_parameters(opcion)["name"]

                # Show progress
                if muestra_dialogo:
                    progreso.update((old_div(100, len(opciones))) * opciones.index(opcion), config.get_localized_string(70180) % server_name)

                # Free mode
                if opcion == "free":
                    try:
                        logger.info("Invoking a %s.get_video_url" % server)
                        response = serverid.get_video_url(page_url=url, video_password=video_password)
                        video_urls.extend(response)
                    except:
                        logger.error("Error getting url in free mode")
                        error_messages.append(config.get_localized_string(60014))
                        import traceback
                        logger.error(traceback.format_exc())

                # Premium mode
                else:
                    try:
                        logger.info("Invoking a %s.get_video_url" % opcion)
                        response = serverid.get_video_url(page_url=url, premium=True,
                                                          user=config.get_setting("user", server=opcion),
                                                          password=config.get_setting("password", server=opcion),
                                                          video_password=video_password)
                        if response and response[0][1]:
                            video_urls.extend(response)
                        elif response and response[0][0]:
                            error_messages.append(response[0][0])
                        else:
                            error_messages.append(config.get_localized_string(60014))
                    except:
                        logger.error("Server errorr: %s" % opcion)
                        error_messages.append(config.get_localized_string(60014))
                        import traceback
                        logger.error(traceback.format_exc())

                # If we already have URLS, we stop searching
                if video_urls and config.get_setting("resolve_stop") == True:
                    break

            # We close progress
            if muestra_dialogo:
                progreso.update(100, config.get_localized_string(60008))
                progreso.close()

            # If there are no options available, we show the notice of premium accounts
            if video_exists and not opciones and server_parameters.get("premium"):
                listapremium = [get_server_parameters(premium)["name"] for premium in server_parameters["premium"]]
                error_messages.append(
                    config.get_localized_string(60009) % (server, " o ".join(listapremium)))

            # If we do not have urls or error messages, we put a generic one
            elif not video_urls and not error_messages:
                error_messages.append(config.get_localized_string(60014))

    return video_urls, len(video_urls) > 0, "<br/>".join(error_messages)


def get_server_name(serverid):
    """
    Function get real server name from string.
    @param serverid: Chain where to look
    @type serverid: str

    @return: Server name
    @rtype: str
    """
    serverid = serverid.lower().split(".")[0]

    # We get the list of servers
    server_list = list(get_servers_list().keys())

    # If the name is in the list
    if serverid in server_list:
        return serverid

    # Browse all servers looking for the name
    for server in server_list:
        params = get_server_parameters(server)
        # If the name is in the list of ids
        if serverid in params["id"]:
            return server
        # If the name is more than one word, check if any id is inside the name:
        elif len(serverid.split()) > 1:
            for id in params["id"]:
                if id in serverid:
                    return server

    # If nothing is found an empty string is returned
    return ""


def is_server_enabled(server):
    """
    Function check if a server is according to the established configuration
    @param server: Server name
    @type server: str

    @return: check result
    @rtype: bool
    """

    server = get_server_name(server)

    # The server does not exist
    if not server:
        return False

    server_parameters = get_server_parameters(server)
    if server_parameters["active"] == True:
        if not config.get_setting("hidepremium"):
            return True
        elif server_parameters["free"] == True:
            return True
        elif [premium for premium in server_parameters["premium"] if config.get_setting("premium", server=premium)]:
            return True

    return False


def get_server_parameters(server):
    """
    Get data from server
    @param server: Server name
    @type server: str

    @return: server data
    @rtype: dict
    """
    # logger.info("server %s" % server)
    global dict_servers_parameters
    server = server.split('.')[0]
    if not server:
        return {}

    if server not in dict_servers_parameters and server not in ['servers']:
        try:
            path = ''
            # Servers
            if filetools.isfile(filetools.join(config.get_runtime_path(), "servers", server + ".json")):
                path = filetools.join(config.get_runtime_path(), "servers", server + ".json")

            # Debriders
            elif filetools.isfile(filetools.join(config.get_runtime_path(), "servers", "debriders", server + ".json")):
                path = filetools.join(config.get_runtime_path(), "servers", "debriders", server + ".json")

            # When the server is not well defined in the channel (there is no connector), it shows an error because there is no "path" and the channel has to be checked
            dict_server = jsontools.load(filetools.read(path))

            dict_server["name"] = translate_server_name(dict_server["name"])

            # Images: url and local files are allowed inside "resources / images"
            if dict_server.get("thumbnail") and "://" not in dict_server["thumbnail"]:
                dict_server["thumbnail"] = filetools.join(config.get_runtime_path(), "resources", "media",
                                                        "servers", dict_server["thumbnail"])
            for k in ['premium', 'id']:
                dict_server[k] = dict_server.get(k, list())

                if isinstance(dict_server[k], str):
                    dict_server[k] = [dict_server[k]]

            if "find_videos" in dict_server:
                dict_server['find_videos']["patterns"] = dict_server['find_videos'].get("patterns", list())
                dict_server['find_videos']["ignore_urls"] = dict_server['find_videos'].get("ignore_urls", list())

            if "settings" in dict_server:
                dict_server['has_settings'] = True
            else:
                dict_server['has_settings'] = False

            dict_servers_parameters[server] = dict_server

        except:
            mensaje = config.get_localized_string(59986) % server
            import traceback
            logger.error(mensaje + traceback.format_exc())
            return {}

    return dict_servers_parameters[server]


def get_server_host(server_name):
    from core import scrapertools
    return [scrapertools.get_domain_from_url(pattern['url']) for pattern in get_server_parameters(server_name)['find_videos']['patterns']]


def get_server_controls_settings(server_name):
    dict_settings = {}

    list_controls = get_server_parameters(server_name).get('settings', [])
    import copy
    list_controls = copy.deepcopy(list_controls)

    # Conversion de str a bool, etc...
    for c in list_controls:
        if 'id' not in c or 'type' not in c or 'default' not in c:
            # If any control in the list does not have id, type or default, we ignore it
            continue

        # new dict with key(id) and value(default) from settings
        dict_settings[c['id']] = c['default']

    return list_controls, dict_settings


def get_server_setting(name, server, default=None):
    """
        Returns the configuration value of the requested parameter.

        Returns the value of the parameter 'name' in the own configuration of the server 'server'.

        Look in the path \addon_data\plugin.video.addon\settings_servers for the file server_data.json and read
        the value of the parameter 'name'. If the server_data.json file does not exist look in the servers folder for the file
        server.json and create a server_data.json file before returning the requested value. If the parameter 'name'
        also does not exist in the server.json file the default parameter is returned.


        @param name: parameter name
        @type name: str
        @param server: server name
        @type server: str
        @param default: return value in case the name parameter does not exist
        @type default: any

        @return: The parameter value 'name'
        @rtype: any

        """
    # We create the folder if it does not exist
    if not filetools.exists(filetools.join(config.get_data_path(), "settings_servers")):
        filetools.mkdir(filetools.join(config.get_data_path(), "settings_servers"))

    file_settings = filetools.join(config.get_data_path(), "settings_servers", server + "_data.json")
    dict_settings = {}
    dict_file = {}
    if filetools.exists(file_settings):
        # We get saved configuration from ../settings/channel_data.json
        try:
            dict_file = jsontools.load(filetools.read(file_settings))
            if isinstance(dict_file, dict) and 'settings' in dict_file:
                dict_settings = dict_file['settings']
        except EnvironmentError:
            logger.info("ERROR when reading the file: %s" % file_settings)

    if not dict_settings or name not in dict_settings:
        # We get controls from the file ../servers/server.json
        try:
            list_controls, default_settings = get_server_controls_settings(server)
        except:
            default_settings = {}
        if name in default_settings:  # If the parameter exists in the server.json we create the server_data.json
            default_settings.update(dict_settings)
            dict_settings = default_settings
            dict_file['settings'] = dict_settings
            # We create the file ../settings/channel_data.json
            if not filetools.write(file_settings, jsontools.dump(dict_file)):
                logger.error("ERROR saving file: %s" % file_settings)

    # We return the value of the local parameter 'name' if it exists, if default is not returned
    return dict_settings.get(name, default)


def set_server_setting(name, value, server):
    # We create the folder if it does not exist
    if not filetools.exists(filetools.join(config.get_data_path(), "settings_servers")):
        filetools.mkdir(filetools.join(config.get_data_path(), "settings_servers"))

    file_settings = filetools.join(config.get_data_path(), "settings_servers", server + "_data.json")
    dict_settings = {}

    dict_file = None

    if filetools.exists(file_settings):
        # We get saved configuration from ../settings/channel_data.json
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

    # We create the file ../settings/channel_data.json
    if not filetools.write(file_settings, jsontools.dump(dict_file)):
        logger.error("ERROR saving file: %s" % file_settings)
        return None

    return value


def get_servers_list():
    """
    Get a dictionary with all available servers

    @return: Diccionario cuyas claves son los nombre de los servidores (nombre del json) and as a value a dictionary with the server parameters.
    @rtype: dict
    """
    global server_list
    if not server_list:
        for server in filetools.listdir(filetools.join(config.get_runtime_path(), "servers")):
            if server.endswith(".json") and not server == "version.json":
                server_parameters = get_server_parameters(server)
                if server_parameters['active']:
                    server_list[server.split(".")[0]] = server_parameters

        if type(server_list) != dict: server_list = sort_servers(server_list)
    return server_list


def get_debriders_list():
    """
    Get a dictionary with all available debriders

    @return: Dictionary whose keys are the names of the debriders (name of the json) and as a value a dictionary with the server parameters.
    @rtype: dict
    """
    server_list = {}
    for server in filetools.listdir(filetools.join(config.get_runtime_path(), "servers", "debriders")):
        if server.endswith(".json"):
            server_parameters = get_server_parameters(server)
            if server_parameters["active"] == True:
                logger.info(server_parameters)
                server_list[server.split(".")[0]] = server_parameters
    return server_list


def sort_servers(servers_list):
    """
    If the option "Order servers" is activated in the server configuration and there is a list of servers
    favorites in settings use it to sort the servers_list list
    :param servers_list: List of servers to order. The items in the servers_list can be strings or Item objects. In both cases it is necessary to have an item.server attribute of type str.
    :return: List of the same type of objects as servers_list ordered according to the favorite servers.
    """
    def index(lst, value):
        if value in lst:
            return lst.index(value)
        else:
            logger.debug('Index not found: ' + value)
            return 999
    if not servers_list:
        return []

    blacklisted_servers = config.get_setting("black_list", server='servers', default=[])
    favorite_servers = config.get_setting('favorites_servers_list', server='servers', default=[])
    favorite_servers = [s for s in favorite_servers if s not in blacklisted_servers]
    if isinstance(servers_list[0], str):
        servers_list = sorted(servers_list, key=lambda x: favorite_servers.index(x) if x in favorite_servers else 999)
        return servers_list

    favorite_quality = ['4k', '2160p', '2160', '4k2160p', '4k2160', '4k 2160p', '4k 2160', '2k',
                    'fullhd', 'fullhd 1080', 'fullhd 1080p', 'full hd', 'full hd 1080', 'full hd 1080p', 'hd1080', 'hd1080p', 'hd 1080', 'hd 1080p', '1080', '1080p',
                    'hd', 'hd720', 'hd720p', 'hd 720', 'hd 720p', '720', '720p', 'hdtv',
                    'sd', '480p', '480', '360p', '360', '240p', '240']

    sorted_list = []
    inverted = False

    if config.get_setting('default_action') == 2:
        inverted = True

    # Priorities when ordering itemlist:
    #       0: Only Qualities
    #       1: Servers and Qualities
    #       2: Qualities and Servers

    priority = 0
    if config.get_setting('favorites_servers') and favorite_servers: priority = 1
    if config.get_setting('quality_priority'): priority = 2

    for item in servers_list:
        element = dict()

        # We check that it is a video item
        if 'server' not in item:
            continue

        if item.server.lower() in blacklisted_servers:
            continue

        element["index_server"] = index(favorite_servers, item.server.lower())
        element["index_quality"] = platformtools.calcResolution(item.quality)
        element['index_language'] = 0 if item.contentLanguage == 'ITA' else 1
        element["bit_rate"] = item.bitrate
        element['videoitem'] = item
        sorted_list.append(element)

    # We order according to priority
    if priority == 0: sorted_list.sort(key=lambda element: (element['index_language'], -element['index_quality'] if inverted else element['index_quality'], element['videoitem'].server))
    elif priority == 1: sorted_list.sort(key=lambda element: (element['index_language'], element['index_server'], -element['index_quality'] if inverted else element['index_quality'])) # Servers and Qualities
    elif priority == 2: sorted_list.sort(key=lambda element: (element['index_language'], -element['index_quality'] if inverted else element['index_quality'], element['index_server'])) # Qualities and Servers

    return [v['videoitem'] for v in sorted_list if v]


# Checking links
def check_list_links(itemlist, numero='', timeout=3):
    """
    Check a list of video links and return it by modifying the title with verification.
    The number parameter indicates how many links to check (0:5, 1:10, 2:15, 3:20)
    The timeout parameter indicates a waiting limit to download the page.
    """
    numero = numero if numero > 4 else ((int(numero) + 1) * 5) if numero != '' else 5
    import sys
    if sys.version_info[0] >= 3:
        from concurrent import futures
    else:
        from concurrent_py2 import futures
    with futures.ThreadPoolExecutor() as executor:
        checked = []
        for it in itemlist:
            if numero > 0 and it.server != '' and it.url != '':
                checked.append(executor.submit(check_video_link, it, timeout))
                numero -= 1
        for link in futures.as_completed(checked):
            res = link.result()
            if res:
                it = res[0]
                verificacion = res[1]
                it.title = verificacion + ' ' + it.title.strip()
                logger.debug('VERIFICATION= ' + verificacion)
                it.alive = verificacion
    return itemlist


def check_video_link(item, timeout=3):
    """
        Check if the link to a video is valid and return a 2-position string with verification.
        :param url, server: Link and server
        :return: str(2) '??':Could not be verified. 'Ok': The link seems to work. 'NO': It doesn't seem to work.
    """
    url = item.url
    server = item.server

    NK = u"[COLOR 0xFFF9B613][B]\u2022[/B][/COLOR]"
    OK = u"[COLOR 0xFF00C289][B]\u2022[/B][/COLOR]"
    KO = u"[COLOR 0xFFC20000][B]\u2022[/B][/COLOR]"

    try:
        server_module = __import__('servers.%s' % server, None, None, ["servers.%s" % server])
    except:
        server_module = None
        logger.error("[check_video_link] Cannot import server! %s" % server)
        return item, NK

    if hasattr(server_module, 'test_video_exists'):
        ant_timeout = httptools.HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT
        httptools.HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT = timeout  # Limit download time

        try:
            video_exists, message = server_module.test_video_exists(page_url=url)
            if not video_exists:
                logger.error("[check_video_link] Does not exist! %s %s %s" % (message, server, url))
                resultado = KO
            else:
                logger.debug("[check_video_link] check ok %s %s" % (server, url))
                resultado = OK
        except:
            logger.error("[check_video_link] Can't check now! %s %s" % (server, url))
            resultado = NK

        finally:
            httptools.HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT = ant_timeout  # Restore download time
            return item, resultado

    logger.debug("[check_video_link] There is no test_video_exists for server:", server)
    return item, NK


def translate_server_name(name):
    if '@' in name: return config.get_localized_string(int(name.replace('@','')))
    else: return name


# def get_server_json(server_name):
#     # logger.info("server_name=" + server_name)
#     try:
#         server_path = filetools.join(config.get_runtime_path(), "servers", server_name + ".json")
#         if not filetools.exists(server_path):
#             server_path = filetools.join(config.get_runtime_path(), "servers", "debriders", server_name + ".json")
#
#         # logger.info("server_path=" + server_path)
#         server_json = jsontools.load(filetools.read(server_path))
#         # logger.info("server_json= %s" % server_json)
#
#     except Exception as ex:
#         template = "An exception of type %s occured. Arguments:\n%r"
#         message = template % (type(ex).__name__, ex.args)
#         logger.error(" %s" % message)
#         server_json = None
#
#     return server_json

if PY3:
    from lib.pymediainfo import MediaInfo
    import pathlib

    def correct_onlinemedia_info(video_itemlist: list) -> list:
        """This function aims at correctly identifying video information
        of an online mediafile and writes them back selectively in the corresponding 
        properties of each Item;
        Examples can be the 'quality_label', 'resolution' and 'bit_rate'

        IN ADDITION it sets also the final media url!
        -------------------
        Parameters
        -------------------
        - video_itemlist: a list of Items (custom type)
        -------------------

        @return: it returns the modified parameter passed to the function "video_itemlist"
        @rtype: list.
        """

        def get_onlinevideo_chunck(url: str) -> str:
            """This function downloads a chunck of the mediafile which resides at the link
            provided as parameter to the function and returns the path to it;
            -------------------
            Parameters
            -------------------
            - url: a string containig the url/link to the video/mediafile you want to gather info from
            -------------------

            @return: the path to the "video_chunk"
            @rtype: string.
            """

            video_chunk =  str(pathlib.Path(__file__).parent.parent.resolve()) + "/header_mediafile"
            headers = {}

            urlList = url.split("|")
            if len(urlList) == 1:
                directUrl, headersUrl = urlList[0], ''
            elif len(urlList) == 2:
                directUrl, headersUrl = urlList

            if headersUrl:
                for name in headersUrl.split('&'):
                    h, v = name.split('=')
                    h = str(h)
                    headers[h] = str(v)

            with requests.Session() as session:
                r = session.get(directUrl, headers=headers, stream=True)

            with open(video_chunk, 'wb') as f:
                logger.info(f'Saving the chunk to the location: {video_chunk}')
                for chunk in r.iter_content(chunk_size=100000):
                    if chunk:
                        f.write(chunk)
                        break

            return video_chunk

        def extract_video_info(path_to_videochunk: str) -> dict:
            """This function determines and generates a dictionary containing
            the correct "resolution", "resolution_label" and "bit_rate" of a video file;
            -------------------
            Parameters
            -------------------
            - path_to_videochunk: path to the video chunk downloaded previously
            -------------------

            @return: it returns a dictionary containing only the selected video information ("resolution", "resolution_label" and "bit_rate")
            @rtype: dictionary
            """
            info_dict = dict()  # dictionary to store resolution, resolution_label and bitrate information that will be returned
            resolutions = {"sd_width" : 1024, "hd_width" : 1366, "fullhd_width" : 1920, "2k_width" : 2560, "4k_width" : 3840}

            logger.info(f'"Mediainfo" will parse the file located at: {path_to_videochunk}')
            media_info = MediaInfo.parse(path_to_videochunk)  # analyses the file in the "path_to_videochunk" location
            for track in media_info.tracks:
                if track.track_type == "Video":               # there can be video tracks and audio tracks, we ensure it is the video one
                    videoinfo = track.to_data()               # save all the data as a dictionary in the variable "videoinfo"

            for k,v in videoinfo.items():
                logger.debug(f'{k}:{v}')

            # if the width information available in the dictionary passed as parameter 
            # to the function is comparable to the dictionary of "resolutions" defined above:
                # set the "resolution_label" accordingly
            if videoinfo["width"] <= resolutions["sd_width"]:
                info_dict["resolution_label"] = "SD"
            elif videoinfo["width"] <= resolutions["hd_width"]:
                info_dict["resolution_label"] = "HD"
            elif videoinfo["width"] <= resolutions["fullhd_width"]:
                info_dict["resolution_label"] = "Full HD"
            elif videoinfo["width"] <= resolutions["2k_width"]:
                info_dict["resolution_label"] = "2K"
            elif videoinfo["width"] <= resolutions["4k_width"]:
                info_dict["resolution_label"] = "4K"
            
            info_dict["resolution"] = (f'{videoinfo["width"]} x {videoinfo["height"]}')
            info_dict["bit_rate"] = float(videoinfo.get("other_bit_rate", 0)[0].split(" ")[0]) if videoinfo.get("other_bit_rate", 0) != 0 else videoinfo.get("other_bit_rate", 0)

            os.remove(path_to_videochunk)                     # remove the video chunck downloaded at the beginning used to retrieve the necessary information

            return info_dict

        def set_blank_videoinfo(item: Item, media_url: str) -> Item:
            """This function sets BLANK attributes of the 'item' object and returns
            its modified version;
            -------------------
            Parameters
            -------------------
            - item: the Item whose parameters need to be modified
            - media_url: the url of the real mediafile
            -------------------

            @return: it returns the abovementioned 'item' with 'blank' set attributes
            @rtype: Item
            """

            logger.info("Updating the Item's information with BLANK ones")
            if "m3u8" in media_url:
                logger.debug("'resolve_video_urls_for_playing' found only an '.m3u8' url which cannot be parsed")
            else:
                logger.debug("'resolve_video_urls_for_playing' was not able to find a valid url to be passed to 'get_onlinevideo_chunk'")

            item.media_url = media_url
            item.title += f"{' [m3u8]' if 'm3u8' in media_url else ''} ... x ..., Bit Rate: unknown"
            # i won't set alternative values for the "item.quality" parameter
            # i won't set alternative values for the "item.resolution" parameter
            item.bitrate = 0
            return item
        
        def set_gathered_videoinfo(item: Item, videoquality_info: dict, media_url: str) -> Item:
            """This function sets the 'media_url', 'title', 'quality', 'resolution' and
            'bitrate' attributes of the 'item' object and returns its modified version;
            -------------------
            Parameters
            -------------------
            - item: the Item whose parameters need to be modified
            - videoquality_info: a dictionary containing all the media quality info
            - media_url: the url of the real mediafile
            -------------------

            @return: it returns the abovementioned 'item' with the modified attributes
            @rtype: Item
            """

            logger.info("Updating the Item's information with the gathered ones")
            item.media_url = media_url
            item.title += (f' {videoquality_info["resolution_label"]}, {videoquality_info["resolution"]}, Bit Rate: {videoquality_info["bit_rate"] + " kb/s" if videoquality_info["bit_rate"] != 0 else "unknown"}')
            item.quality = videoquality_info["resolution_label"]
            item.resolution = videoquality_info["resolution"]
            item.bitrate = videoquality_info["bit_rate"]
            return item

        def find_obfuscated_url(item: Item):
            # Checks if channel exists
            CHANNELS = 'channels' if os.path.isfile(os.path.join(config.get_runtime_path(), 'channels', item.channel + ".py")) else 'specials'

            channel_file = os.path.join(config.get_runtime_path(), CHANNELS, item.channel + ".py")
            logger.debug("channel_file= " + channel_file + ' - ' + CHANNELS + ' - ' + item.channel)

            channel = None

            if os.path.exists(channel_file):
                try:
                    channel = __import__('%s.%s' % (CHANNELS, item.channel), None, None, ['%s.%s' % (CHANNELS, item.channel)])
                except ImportError:
                    exec("import " + CHANNELS + "." + item.channel + " as channel")
            logger.info("Running channel %s | %s" % (channel.__name__, channel.__file__))

            if hasattr(channel, 'play'):
                logger.debug("Executing channel 'play' method")
                itemlist = channel.play(item)
                if len(itemlist) > 0 and isinstance(itemlist[0], Item):
                    item = itemlist[0]

            return item

        if isinstance(video_itemlist, list):
            logger.info("Parsing the provided 'video_itemlist'")
            for number, item in enumerate(video_itemlist):
                logger.debug(f'Parsing the item n°: {number}')
                if item.action == "play":
                    url_list, url_exists, url_error = resolve_video_urls_for_playing(item.server, item.url, item.password)
                    if not url_exists:
                        logger.debug(url_error)
                        item.url = find_obfuscated_url(item).url  # Let's try another way before giving up
                        url_list, url_exists, url_error = resolve_video_urls_for_playing(item.server, item.url, item.password)

                    if url_exists:
                        logger.debug(f'The URL list is: ----> {url_list}\n')
                        if len(url_list) == 1 and (url_list[-1][-1] == "" or "m3u8" in url_list[-1][-1]):
                            item = set_blank_videoinfo(item, url_list[-1][-1])
                            continue
                        elif not "m3u8" in url_list[-1][-1]:
                            highest_quality_url = url_list[-1][-1]
                        else:
                            highest_quality_url = url_list[-2][-1]

                        try:
                            logger.info(f'For the Server: "{item.server}"  we will pass to "correct_onlinemedia_info" the url: "{highest_quality_url}"')
                            path_to_chunck = get_onlinevideo_chunck(highest_quality_url)
                            video_quality_info = extract_video_info(path_to_chunck)
                            item = set_gathered_videoinfo(item, video_quality_info, highest_quality_url)
                            logger.info(f'\n --------\n THE INFORMATION THAT WERE SET ARE:\n {item.url}\n {item.media_url}\n {item.title}\n {item.quality}\n {item.resolution}\n {item.bitrate + " kb/s"}\n --------')
                        except Exception:
                            import traceback
                            logger.error(traceback.format_exc())
                            item = set_blank_videoinfo(item, media_url=highest_quality_url)
                            try:
                                os.remove(path_to_chunck)
                            except (FileNotFoundError, UnboundLocalError):
                                continue
                    else:
                        logger.debug(url_error)
                        item = set_blank_videoinfo(item, media_url="")
                else:
                    logger.debug(f'The intem n°: {number} is not a valid item to parse')
        else:
            return []

        return video_itemlist

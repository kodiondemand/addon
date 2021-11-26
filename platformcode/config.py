# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Configuration parameters (kodi)
# ------------------------------------------------------------

import sys, os, xbmc, xbmcaddon
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

PLUGIN_NAME = "kod"

__settings__ = xbmcaddon.Addon(id="plugin.video." + PLUGIN_NAME)
__language__ = __settings__.getLocalizedString
__version_fix = None
__devMode = None

channelsData = dict()
changelogFile = xbmc.translatePath("special://profile/addon_data/plugin.video.kod/changelog.txt")
addonIcon = os.path.join(__settings__.getAddonInfo( "path" ),'resources', 'media', "logo.png" )



def getAddonCore():
    return __settings__


def getAddonVersion(with_fix=True):
    '''
    Returns the version number of the addon, and optionally fix number if there is one
    '''
    if with_fix:
        return __settings__.getAddonInfo('version') + " " + getAddonVersionFix()
    else:
        return __settings__.getAddonInfo('version')


def getAddonVersionFix():
    global __version_fix
    ret = __version_fix
    if not ret:
        if not devMode():
            try:
                sha = open(os.path.join(getRuntimePath(), 'last_commit.txt')).readline()
                ret = sha[:7]
            except:
                ret = '??'
        else:
            ret = 'DEV'
    return ret


def devMode():
    global __devMode
    if not __devMode:
        __devMode = os.path.isdir(getRuntimePath() + '/.git')
    return __devMode


def getXBMCPlatform(full_version=False):
    """
        Returns the information the version of xbmc or kodi on which the plugin is run

        @param full_version: indicates if we want all the information or not
        @type full_version: bool
        @rtype: str o dict
        @return: If the full_version parameter is True, a dictionary with the following keys is returned:
            'num_version': (float) version number in XX.X format
            'name_version': (str) key name of each version
            'video_db': (str) name of the file that contains the video database
            'plaform': (str) is made up of "kodi-" or "xbmc-" plus the version name as appropriate.
        If the full_version parameter is False (default) the value of the 'plaform' key from the previous dictionary is returned.
    """
    import re

    ret = {}
    codename = {"10": "dharma", "11": "eden", "12": "frodo",
                "13": "gotham", "14": "helix", "15": "isengard",
                "16": "jarvis", "17": "krypton", "18": "leia", 
                "19": "matrix"}
    code_db = {'10': 'MyVideos37.db', '11': 'MyVideos60.db', '12': 'MyVideos75.db',
               '13': 'MyVideos78.db', '14': 'MyVideos90.db', '15': 'MyVideos93.db',
               '16': 'MyVideos99.db', '17': 'MyVideos107.db', '18': 'MyVideos116.db', 
               '19': 'MyVideos119.db'}

    num_version = xbmc.getInfoLabel('System.BuildVersion')
    num_version = re.match("\d+\.\d+", num_version).group(0)
    ret['name_version'] = codename.get(num_version.split('.')[0], num_version)
    ret['video_db'] = code_db.get(num_version.split('.')[0], "")
    ret['num_version'] = float(num_version)
    if ret['num_version'] < 14:
        ret['platform'] = "xbmc-" + ret['name_version']
    else:
        ret['platform'] = "kodi-" + ret['name_version']

    if full_version:
        return ret
    else:
        return ret['platform']

def getPlatform():
    import platform
    build = xbmc.getInfoLabel("System.BuildVersion")
    kodi_version = int(build.split()[0][:2])
    ret = {
        "auto_arch": sys.maxsize > 2 ** 32 and "64-bit" or "32-bit",
        "arch": sys.maxsize > 2 ** 32 and "x64" or "ia32",
        "os": "",
        "version": platform.release(),
        "kodi": kodi_version,
        "build": build
    }
    if xbmc.getCondVisibility("system.platform.android"):
        ret["os"] = "android"
        if "arm" in platform.machine() or "aarch" in platform.machine():
            ret["arch"] = "arm"
            if "64" in platform.machine() and ret["auto_arch"] == "64-bit":
                ret["arch"] = "arm64"
    elif xbmc.getCondVisibility("system.platform.linux"):
        ret["os"] = "linux"
        if "aarch" in platform.machine() or "arm64" in platform.machine():
            if xbmc.getCondVisibility("system.platform.linux.raspberrypi"):
                ret["arch"] = "armv7"
            elif ret["auto_arch"] == "32-bit":
                ret["arch"] = "armv7"
            elif ret["auto_arch"] == "64-bit":
                ret["arch"] = "arm64"
            elif platform.architecture()[0].startswith("32"):
                ret["arch"] = "arm"
            else:
                ret["arch"] = "arm64"
        elif "armv7" in platform.machine():
            ret["arch"] = "armv7"
        elif "arm" in platform.machine():
            ret["arch"] = "arm"
    elif xbmc.getCondVisibility("system.platform.xbox"):
        ret["os"] = "win"
        ret["arch"] = "x64"
    elif xbmc.getCondVisibility("system.platform.windows"):
        ret["os"] = "win"
        if platform.machine().endswith('64'):
            ret["arch"] = "x64"
    elif xbmc.getCondVisibility("system.platform.osx"):
        ret["os"] = "mac"
        ret["arch"] = "x64"
    elif xbmc.getCondVisibility("system.platform.ios"):
        ret["os"] = "ios"
        ret["arch"] = "arm"

    return ret


def is_xbmc():
    return True


def get_videolibrary_support():
    return True


def get_channel_url(findhostMethod=None, name=None, forceFindhost=False):
    from core import jsontools
    import inspect

    LOCAL_FILE = os.path.join(getRuntimePath(), "channels.json")
    global channelsData
    if not channelsData:
        with open(LOCAL_FILE) as f:
            channelsData = jsontools.load(f.read())

    frame = inspect.stack()[1]
    if not name:
        name = os.path.basename(frame[0].f_code.co_filename).replace('.py', '')
    if findhostMethod:
        url = jsontools.getNodeFromFile(name, 'url')
        if not url or forceFindhost:
            url = findhostMethod(channelsData['findhost'][name])
            jsontools.updateNode(url, name, 'url')
        return url
    else:
        return channelsData['direct'][name]


def getSystemPlatform():
    """ function: to recover the platform that xbmc is running """
    platform = "unknown"
    if xbmc.getCondVisibility("system.platform.linux"):
        platform = "linux"
    elif xbmc.getCondVisibility("system.platform.windows"):
        platform = "windows"
    elif xbmc.getCondVisibility("system.platform.osx"):
        platform = "osx"
    return platform


def getAllSettingsAddon():
    # Read the settings.xml file and return a dictionary with {id: value}
    from core import scrapertools

    with open(os.path.join(getDataPath(), "settings.xml"), "rb") as infile:
        data = infile.read().decode('utf-8')

    ret = {}
    matches = scrapertools.findMultipleMatches(data, '<setting id=\"([^\"]+)\"[^>]*>')

    for _id in matches:
        ret[_id] = getSetting(_id)

    return ret


def openSettings():
    xbmc.executebuiltin('Addon.OpenSettings(plugin.video.%s)' % PLUGIN_NAME)


def getSetting(name, channel="", server="", default=None):
    """
    Returns the configuration value of the requested parameter.

    Returns the value of the parameter 'name' in the global configuration, in the own configuration of the channel 'channel' or in that of the server 'server'.

    The channel and server parameters should not be used simultaneously. If the channel name is specified it will be returned
    the result of calling channeltools.getChannelSetting (name, channel, default). If the name of the
    server will return the result of calling servertools.getChannelSetting (name, server, default). If I dont know
    Specify none of the above will return the value of the parameter in the global configuration if it exists or
    the default value otherwise.

    @param name: parameter name
    @type name: str
    @param channel: channel name
    @type channel: str
    @param server: server name
    @type server: str
    @param default: return value in case the name parameter does not exist
    @type default: any

    @return: The value of the parameter 'name'
    @rtype: any

    """

    # Specific channel setting
    if channel:
        # logger.info("getSetting reading channel setting '"+name+"' from channel json")
        from core import channeltools
        value = channeltools.getChannelSetting(name, channel, default)
        # logger.info("getSetting -> '"+repr(value)+"'")
        return value

    # Specific server setting
    elif server:
        # logger.info("getSetting reading server setting '"+name+"' from server json")
        from core import servertools
        value = servertools.getServerSetting(name, server, default)
        # logger.info("getSetting -> '"+repr(value)+"'")
        return value

    # Global setting
    else:
        # logger.info("getSetting reading main setting '"+name+"'")
        value = __settings__.getSetting(name)
        if not value:
            return default
        # Translate Path if start with "special://"
        if value.startswith("special://") and "videolibrarypath" not in name:
            value = xbmc.translatePath(value)

        # hack para devolver el tipo correspondiente
        if value == "true":
            return True
        elif value == "false":
            return False
        else:
            # special case return as str
            try:
                value = int(value)
            except ValueError:
                pass
            return value


def setSetting(name, value, channel="", server=""):
    """
    Sets the configuration value of the indicated parameter.

    Set 'value' as the value of the parameter 'name' in the global configuration or in the own configuration of the channel 'channel'.
    Returns the changed value or None if the assignment could not be completed.

    If the name of the channel is specified, search in the path \ addon_data \ plugin.video.kod \ settings_channels the
    channel_data.json file and set the parameter 'name' to the value indicated by 'value'. If the file
    channel_data.json does not exist look in the channels folder for the channel.json file and create a channel_data.json file before modifying the 'name' parameter.
    If the parameter 'name' does not exist, it adds it, with its value, to the corresponding file.


    Parameters:
    name - name of the parameter
    value - value of the parameter
    channel [optional] - channel name

    Returns:
    'value' if the value could be set and None otherwise

    """
    if channel:
        from core import channeltools
        return channeltools.setChannelSetting(name, value, channel)
    elif server:
        from core import servertools
        return servertools.setServerSetting(name, value, server)
    else:
        try:
            if isinstance(value, bool):
                if value:
                    value = "true"
                else:
                    value = "false"

            elif isinstance(value, (int, long)):
                value = str(value)

            __settings__.setSetting(name, value)

        except Exception as ex:
            from platformcode import logger
            logger.error("Error converting '%s' value is not saved \n%s" % (name, ex))
            return None

        return value


def getLocalizedString(code):
    dev = __language__(code)

    try:
        # Unicode to utf8
        if isinstance(dev, unicode):
            dev = dev.encode("utf8")
            if PY3: dev = dev.decode("utf8")

        # All encodings to utf8
        elif not PY3 and isinstance(dev, str):
            dev = unicode(dev, "utf8", errors="replace").encode("utf8")

        # Bytes encodings to utf8
        elif PY3 and isinstance(dev, bytes):
            dev = dev.decode("utf8")
    except:
        pass

    return dev

def getLocalizedCategory(categ):
    categories = {'movie': getLocalizedString(30122), 'tvshow': getLocalizedString(30123),
                  'anime': getLocalizedString(30124), 'documentary': getLocalizedString(30125),
                  'vos': getLocalizedString(30136), 'sub': getLocalizedString(30136),
                  'direct': getLocalizedString(30137), 'torrent': getLocalizedString(70015),
                  'live': getLocalizedString(30138), 'music': getLocalizedString(30139)
    }
    return categories[categ] if categ in categories else categ


def getLocalizedLanguage(lang):
    languages = {'ita': 'ITA', 'sub-ita': 'Sub-ITA'}
    return languages[lang] if lang in languages else lang



def getVideolibraryConfigPath():
    value = getSetting("videolibrarypath")
    if value == "":
        verifyDirectoriesCreated()
        value = getSetting("videolibrarypath")
    return value


def getVideolibraryPath():
    return xbmc.translatePath(getVideolibraryConfigPath())


def getTempFile(filename):
    return xbmc.translatePath(os.path.join("special://temp/", filename))


def getRuntimePath():
    return xbmc.translatePath(__settings__.getAddonInfo('Path'))


def getDataPath():
    dev = xbmc.translatePath(__settings__.getAddonInfo('Profile'))

    # Create the directory if it doesn't exist
    if not os.path.exists(dev):
        os.makedirs(dev)

    return dev


def getIcon():
    return xbmc.translatePath(__settings__.getAddonInfo('icon'))


def getFanart():
    return xbmc.translatePath(__settings__.getAddonInfo('fanart'))


def getCookieData():
    import os
    ficherocookies = os.path.join(getDataPath(), 'cookies.dat')

    cookiedatafile = open(ficherocookies, 'r')
    cookiedata = cookiedatafile.read()
    cookiedatafile.close()

    return cookiedata


# Test if all the required directories are created
def verifyDirectoriesCreated():
    from platformcode import logger
    from core import filetools
    from platformcode import xbmc_videolibrary

    config_paths = [["videolibrarypath", "videolibrary"],
                    ["downloadpath", "downloads"],
                    ["downloadlistpath", "downloads/list"],
                    ["settings_path", "settings_channels"]]

    for path, default in config_paths:
        saved_path = getSetting(path)

        # video store
        if path == "videolibrarypath":
            if not saved_path:
                saved_path = xbmc_videolibrary.search_library_path()
                if saved_path:
                    setSetting(path, saved_path)

        if not saved_path:
            saved_path = "special://profile/addon_data/plugin.video." + PLUGIN_NAME + "/" + default
            setSetting(path, saved_path)

        saved_path = xbmc.translatePath(saved_path)
        if not filetools.exists(saved_path):
            logger.debug("Creating %s: %s" % (path, saved_path))
            filetools.mkdir(saved_path)

    config_paths = [["folder_movies", "Film"],
                    ["folder_tvshows", "Serie TV"]]

    for path, default in config_paths:
        saved_path = getSetting(path)

        if not saved_path:
            saved_path = default
            setSetting(path, saved_path)

        content_path = filetools.join(getVideolibraryPath(), saved_path)
        if not filetools.exists(content_path):
            logger.debug("Creating %s: %s" % (path, content_path))

            # if the directory is created
            filetools.mkdir(content_path)

    from platformcode import xbmc_videolibrary
    xbmc_videolibrary.update_sources(getSetting("videolibrarypath"))
    xbmc_videolibrary.update_sources(getSetting("downloadpath"))

    try:
        from core import scrapertools
        # We look for the addon.xml file of the active skin
        skindir = filetools.join(xbmc.translatePath("special://home"), 'addons', xbmc.getSkinDir(), 'addon.xml')
        if not os.path.isdir(skindir): return # No need to show error in log if folder doesn't exist
        # We extract the name of the default resolution folder
        folder = ""
        data = filetools.read(skindir)
        res = scrapertools.findMultipleMatches(data, '(<res .*?>)')
        for r in res:
            if 'default="true"' in r:
                folder = scrapertools.find_single_match(r, 'folder="([^"]+)"')
                break

        # We check if it exists in the addon and if not, we create it
        default = filetools.join(getRuntimePath(), 'resources', 'skins', 'Default')
        if folder and not filetools.exists(filetools.join(default, folder)):
            filetools.mkdir(filetools.join(default, folder))

        # We copy the file to said folder from the 720p folder if it does not exist or if the size is different
        if folder and folder != '720p':
            for root, folders, files in filetools.walk(filetools.join(default, '720p')):
                for f in files:
                    if not filetools.exists(filetools.join(default, folder, f)) or (filetools.getsize(filetools.join(default, folder, f)) != filetools.getsize(filetools.join(default, '720p', f))):
                        filetools.copy(filetools.join(default, '720p', f), filetools.join(default, folder, f), True)
    except:
        import traceback
        logger.error("When checking or creating the resolution folder")
        logger.error(traceback.format_exc())


def getOnlineServerThumb(server):
    return "https://raw.github.com/kodiondemand/media/master/resources/servers/" + server.lower().replace('_server','') + '.png'
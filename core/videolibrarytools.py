# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Common Library Tools
# ------------------------------------------------------------

#from builtins import str
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import errno, math, traceback, re, os

from core import filetools, scraper, scrapertools
from core.item import Item
from lib import generictools
from platformcode import config, logger, platformtools
from platformcode.autorenumber import RENUMBER

FOLDER_MOVIES = config.get_setting("folder_movies")
FOLDER_TVSHOWS = config.get_setting("folder_tvshows")
VIDEOLIBRARY_PATH = config.get_videolibrary_path()
MOVIES_PATH = filetools.join(VIDEOLIBRARY_PATH, FOLDER_MOVIES)
TVSHOWS_PATH = filetools.join(VIDEOLIBRARY_PATH, FOLDER_TVSHOWS)

if not FOLDER_MOVIES or not FOLDER_TVSHOWS or not VIDEOLIBRARY_PATH \
        or not filetools.exists(MOVIES_PATH) or not filetools.exists(TVSHOWS_PATH):
    config.verify_directories_created()

addon_name = "plugin://plugin.video.%s/" % config.PLUGIN_NAME


def read_nfo(path_nfo, item=None):
    """
    Method to read nfo files.
        Nfo files have the following structure: url_scraper | xml + item_json [url_scraper] and [xml] are optional, but only one of them must always exist.
    @param path_nfo: absolute path to nfo file
    @type path_nfo: str
    @param item: If this parameter is passed the returned item will be a copy of it with the values ​​of 'infoLabels', 'library_playcounts' and 'path' read from the nfo
    @type: Item
    @return: A tuple consisting of the header (head_nfo = 'url_scraper' | 'xml') and the object 'item_json'
    @rtype: tuple (str, Item)
    """
    head_nfo = ""
    it = Item()

    data = filetools.read(path_nfo)

    if data:
        head_nfo = data.splitlines()[0] + "\n"
        data = "\n".join(data.splitlines()[1:])

        it_nfo = Item().fromjson(data)
        if not it_nfo.library_playcounts:  # may be corrupted
            it_nfo.library_playcounts = {}

        if item:
            it = item.clone()
            it.infoLabels = it_nfo.infoLabels
            if 'library_playcounts' in it_nfo:
                it.library_playcounts = it_nfo.library_playcounts
            if it_nfo.path:
                it.path = it_nfo.path
        else:
            it = it_nfo

        if 'fanart' in it.infoLabels:
            it.fanart = it.infoLabels['fanart']

    return head_nfo, it


def save_movie(item, silent=False):
    """
    saves the item element in the movie library, with the values ​​it contains.
    @type item: item
    @param item: item to be saved.
    @rtype insertados: int
    @return: the number of elements inserted
    @rtype sobreescritos: int
    @return: the number of overwritten elements
    @rtype fallidos: int
    @return: the number of failed items or -1 if all failed
    """
    logger.debug()
    # logger.debug(item.tostring('\n'))
    insertados = 0
    sobreescritos = 0
    fallidos = 0
    path = ""

    # We try to obtain the correct title:
    # 1. contentTitle: This should be the correct site, since the title usually contains "Add to the video library..."
    # 2. fulltitle
    # 3. title
    # if item.contentTitle: item.title = item.contentTitle
    # elif item.fulltitle: item.title = item.fulltitle

    if not item.contentTitle:
        # We put the correct title on your site so that scraper can locate it
        if item.fulltitle:
            item.contentTitle = item.fulltitle
        else:
            item.contentTitle = item.title

    # If at this point we do not have a title, we leave
    if not item.contentTitle or not item.channel:
        logger.debug("contentTitle NOT FOUND")
        return 0, 0, -1, path  # Salimos sin guardar

    scraper_return = scraper.find_and_set_infoLabels(item)

    # At this point we can have:
    #  scraper_return = True: An item with infoLabels with the updated information of the movie
    #  scraper_return = False: An item without movie information (it has been canceled in the window)
    #  item.infoLabels['code'] == "" : The required IMDB identifier was not found to continue, we quit
    if not scraper_return or not item.infoLabels['code']:
        logger.debug("NOT FOUND IN SCRAPER OR DO NOT HAVE code")
        return 0, 0, -1, path

    _id = item.infoLabels['code'][0]

    # progress dialog
    if not silent:
        p_dialog = platformtools.dialog_progress(config.get_localized_string(20000), config.get_localized_string(60062))

    if config.get_setting("original_title_folder", "videolibrary") and item.infoLabels['originaltitle']:
        base_name = item.infoLabels['originaltitle']
    else:
        base_name = item.contentTitle

    base_name = base_name.lstrip('.')

    if not PY3:
        base_name = unicode(filetools.validate_path(base_name.replace('/', '-')), "utf8").encode("utf8")
    else:
        base_name = filetools.validate_path(base_name.replace('/', '-'))

    if config.get_setting("lowerize_title", "videolibrary"):
        base_name = base_name.lower()

    for raiz, subcarpetas, ficheros in filetools.walk(MOVIES_PATH):
        for c in subcarpetas:
            code = scrapertools.find_single_match(c, r'\[(.*?)\]')
            if code and code in item.infoLabels['code']:
                path = filetools.join(raiz, c)
                _id = code
                break

    if not path:
        # Create folder
        path = filetools.join(MOVIES_PATH, ("%s [%s]" % (base_name, _id)).strip())
        logger.debug("Creating movie directory:" + path)
        if not filetools.mkdir(path):
            logger.debug("Could not create directory")
            return 0, 0, -1, path

    nfo_path = filetools.join(path, "%s [%s].nfo" % (base_name, _id))
    strm_path = filetools.join(path, "%s.strm" % base_name)
    json_path = filetools.join(path, ("%s [%s].json" % (base_name, item.channel.lower())))

    nfo_exists = filetools.exists(nfo_path)
    strm_exists = filetools.exists(strm_path)
    json_exists = filetools.exists(json_path)

    if not nfo_exists:
        # We create .nfo if it doesn't exist
        logger.debug("Creating .nfo: " + nfo_path)
        head_nfo = scraper.get_nfo(item)

        item_nfo = Item(title=item.contentTitle, channel="videolibrary", action='findvideos',
                        library_playcounts={"%s [%s]" % (base_name, _id): 0}, infoLabels=item.infoLabels,
                        library_urls={})

    else:
        # If .nfo exists, but we are adding a new channel we open it
        head_nfo, item_nfo = read_nfo(nfo_path)

    if not strm_exists:
        # Create base_name.strm if you do not exist
        item_strm = Item(channel='videolibrary', action='play_from_library',
                         strm_path=strm_path.replace(MOVIES_PATH, ""), contentType='movie',
                         contentTitle=item.contentTitle)
        strm_exists = filetools.write(strm_path, '%s?%s' % (addon_name, item_strm.tourl()))
        item_nfo.strm_path = strm_path.replace(MOVIES_PATH, "")

    # Only if item_nfo and .strm exist we continue
    if item_nfo and strm_exists:

        if json_exists:
            logger.debug("The file exists. Is overwritten")
            sobreescritos += 1
        else:
            insertados += 1

        # If the emergency url option has been checked, it is added to the movie after running Findvideos from the channel
        try:
            headers = {}
            if item.headers:
                headers = item.headers
            channel = item.channel
            if config.get_setting("emergency_urls", channel) in [1, 3]:
                item = emergency_urls(item, None, json_path, headers=headers)
                if item_nfo.emergency_urls and not isinstance(item_nfo.emergency_urls, dict):
                    del item_nfo.emergency_urls
                if not item_nfo.emergency_urls:
                    item_nfo.emergency_urls = dict()
                item_nfo.emergency_urls.update({item.channel: True})
        except:
            logger.error("Unable to save %s emergency urls in the video library" % item.contentTitle)
            logger.error(traceback.format_exc())

        if filetools.write(json_path, item.tojson()):
            if not silent: p_dialog.update(100, item.contentTitle)
            item_nfo.library_urls[item.channel] = item.url

            if filetools.write(nfo_path, head_nfo + item_nfo.tojson()):
                #logger.debug("FOLDER_MOVIES : %s" % FOLDER_MOVIES)
                # We update the Kodi video library with the movie
                if config.is_xbmc() and config.get_setting("videolibrary_kodi") and not silent:
                    from platformcode import xbmc_videolibrary
                    xbmc_videolibrary.update()

                if not silent: p_dialog.close()
                return insertados, sobreescritos, fallidos, path

    # If we get to this point it is because something has gone wrong
    logger.error("Could not save %s in the video library" % item.contentTitle)
    if not silent:
        p_dialog.update(100, item.contentTitle)
        p_dialog.close()
    return 0, 0, -1, path

def update_renumber_options(item, head_nfo, path):
    from core import jsontools
    # from core.support import dbg;dbg()
    tvshow_path = filetools.join(path, 'tvshow.nfo')
    if filetools.isfile(tvshow_path) and item.channel_prefs:
        for channel in item.channel_prefs:
            filename = filetools.join(config.get_data_path(), "settings_channels", channel + '_data.json')
            if filetools.isfile(filename):
                json_file = jsontools.load(filetools.read(filename))
                if RENUMBER in json_file:
                    json = json_file[RENUMBER]
                    if item.fulltitle in json:
                        item.channel_prefs[channel][RENUMBER] = json[item.fulltitle]
                        logger.debug('UPDATED=\n' + str(item.channel_prefs))
                        filetools.write(tvshow_path, head_nfo + item.tojson())

def add_renumber_options(item, head_nfo, path):
    from core import jsontools
    # from core.support import dbg;dbg()
    ret = None
    filename = filetools.join(config.get_data_path(), "settings_channels", item.channel + '_data.json')
    json_file = jsontools.load(filetools.read(filename))
    if RENUMBER in json_file:
        json = json_file[RENUMBER]
        if item.fulltitle in json:
            ret = json[item.fulltitle]
    return ret

def check_renumber_options(item):
    from platformcode.autorenumber import load, write
    for key in item.channel_prefs:
        if RENUMBER in item.channel_prefs[key]:
            item.channel = key
            json = load(item)
            if not json or item.fulltitle not in json:
                json[item.fulltitle] = item.channel_prefs[key][RENUMBER]
                write(item, json)

    # head_nfo, tvshow_item = read_nfo(filetools.join(item.context[0]['nfo']))
    # if tvshow_item['channel_prefs'][item.fullti]


def filter_list(episodelist, action=None, path=None):
    # if path: path = path.decode('utf8')
    # import xbmc
    # if xbmc.getCondVisibility('system.platform.windows') > 0: path = path.replace('smb:','').replace('/','\\')
    channel_prefs = {}
    lang_sel = quality_sel = show_title = channel =''

    if action: 
        tvshow_path = filetools.join(path, "tvshow.nfo")
        head_nfo, tvshow_item = read_nfo(tvshow_path)
        channel = episodelist[0].channel
        show_title = tvshow_item.infoLabels['tvshowtitle']
        if not tvshow_item.channel_prefs:
            tvshow_item.channel_prefs={channel:{}}
            list_item = filetools.listdir(path)
            for File in list_item:
                if (File.endswith('.strm') or File.endswith('.json') or File.endswith('.nfo')):
                    filetools.remove(filetools.join(path, File))
        if channel not in tvshow_item.channel_prefs:
            tvshow_item.channel_prefs[channel] = {}

        channel_prefs = tvshow_item.channel_prefs[channel]

        renumber = add_renumber_options(episodelist[0], head_nfo, tvshow_path)
        if renumber:
            channel_prefs[RENUMBER] = renumber

        if action == 'get_seasons':
            if 'favourite_language' not in channel_prefs:
                channel_prefs['favourite_language'] = ''
            if 'favourite_quality' not in channel_prefs:
                channel_prefs['favourite_quality'] = ''
            if channel_prefs['favourite_language']:
                lang_sel = channel_prefs['favourite_language']
            if channel_prefs['favourite_quality']:
                quality_sel = channel_prefs['favourite_quality']
    # if Download
        if not show_title: show_title = episodelist[0].fulltitle
        if not channel: channel= episodelist[0].channel
    # SELECT EISODE BY LANG AND QUALITY
    quality_dict = {'N/A': ['n/a'],
                    'BLURAY': ['br', 'bluray'],
                    'FULLHD': ['fullhd', 'fullhd 1080', 'fullhd 1080p', 'full hd', 'full hd 1080', 'full hd 1080p', 'hd1080', 'hd1080p', 'hd 1080', 'hd 1080p', '1080', '1080p'],
                    'HD': ['hd', 'hd720', 'hd720p', 'hd 720', 'hd 720p', '720', '720p', 'hdtv'],
                    '480P': ['sd', '480p', '480'],
                    '360P': ['360p', '360'],
                    '240P': ['240p', '240'],
                    'MAX':['MAX']}
    quality_order = ['N/A', '240P', '360P','480P', 'HD', 'FULLHD', 'BLURAY', 'MAX']


    lang_list = []
    sub_list = []
    quality_list = ['MAX']

    # Make Language List
    for episode in episodelist:
        if not episode.contentLanguage: episode.contentLanguage = 'ITA'
        if type(episode.contentLanguage) == list and episode.contentLanguage not in lang_list:
           pass
        else:
            if episode.contentLanguage and episode.contentLanguage not in lang_list:
                # Make list of subtitled languages
                if 'sub' in episode.contentLanguage.lower():
                    sub = re.sub('Sub-','', episode.contentLanguage)
                    if sub not in sub_list: sub_list.append(sub)
                else:
                    lang_list.append(episode.contentLanguage)

    # add to Language List subtitled languages
    if sub_list:
        for sub in sub_list:
            if sub in lang_list:
                lang_list.insert(lang_list.index(sub) + 1, 'Sub-' + sub)
                lang_list.insert(lang_list.index(sub) + 2, sub + ' + Sub-' + sub)
            else:
                lang_list.append('Sub-' + sub)

    # Make Quality List
    for episode in episodelist:
        for name, var in quality_dict.items():
            if not episode.quality and 'N/A' not in quality_list:
                quality_list.append('N/A')
            elif episode.quality and episode.quality.lower() in var and name not in quality_list:
                quality_list.append(name)
    quality_list = sorted(quality_list, key=lambda x:quality_order.index(x))

    # if more than one language
    if len(lang_list) > 1:
        selection = lang_list.index(lang_sel) if lang_sel else platformtools.dialog_select(config.get_localized_string(70725) % (show_title, channel),lang_list)
        if action: lang_sel = channel_prefs['favourite_language'] = lang_list[selection]
        langs = lang_list[selection].split(' + ')

        ep_list = []
        count = 0
        stop = False
        while not stop:
            for episode in episodelist:
                title = scrapertools.find_single_match(episode.title, r'(\d+x\d+)')
                if not any(title in word for word in ep_list) and episode.contentLanguage == langs[count]:
                    ep_list.append(episode.title)
            if count < len(langs)-1: count += 1
            else: stop = True
        it = []
        for episode in episodelist:
            if episode.title in ep_list:
                it.append(episode)
        episodelist = it

    else: channel_prefs['favourite_language'] = ''

    # if more than one quality
    if len(quality_list) > 2:
        if config.get_setting('videolibrary_max_quality'): selection = favourite_quality_selection = len(quality_list)-1
        else: selection = favourite_quality_selection = quality_list.index(quality_sel) if quality_sel else platformtools.dialog_select(config.get_localized_string(70726) % (show_title, channel) ,quality_list)

        ep_list = []
        stop = False
        while not stop:
            for episode in episodelist:
                title = scrapertools.find_single_match(episode.title, r'(\d+x\d+)')
                if not any(title in word for word in ep_list) and episode.quality.lower() in quality_dict[quality_list[selection]]:
                    ep_list.append(episode.title)
            if selection != 0: selection = selection - 1
            else: stop = True
            if quality_list[selection] == 'N/A':
                for episode in episodelist:
                    title = scrapertools.find_single_match(episode.title, r'(\d+x\d+)')
                    if not any(title in word for word in ep_list):
                        ep_list.append(episode.title)

        it = []
        for episode in episodelist:
            if episode.title in ep_list:
                if action: channel_prefs['favourite_quality'] = quality_list[favourite_quality_selection]
                it.append(episode)
        episodelist = it

    else:channel_prefs['favourite_quality'] = ''

    if action: filetools.write(tvshow_path, head_nfo + tvshow_item.tojson())

    return episodelist

def save_tvshow(item, episodelist, silent=False):
    """
    stores in the series library the series with all the chapters included in the episodelist
    @type item: item
    @param item: item that represents the series to save
    @type episodelist: list
    @param episodelist: list of items that represent the episodes to be saved.
    @rtype insertados: int
    @return: the number of episodes inserted
    @rtype sobreescritos: int
    @return: the number of overwritten episodes
    @rtype fallidos: int
    @return: the number of failed episodes or -1 if the entire series has failed
    @rtype path: str
    @return: serial directory
    """
    logger.debug()
    # logger.debug(item.tostring('\n'))
    path = ""

    # If at this point we do not have a title or code, we leave
    if not (item.contentSerieName or item.infoLabels['code']) or not item.channel:
        logger.debug("NOT FOUND contentSerieName or code")
        return 0, 0, -1, path  # Salimos sin guardar

    contentTypeBackup = item.contentType  # Fix errors in some channels
    if not item.infoLabels['code']:
        scraper_return = scraper.find_and_set_infoLabels(item)
    else:
        scraper_return = True
    item.contentType = contentTypeBackup  # Fix errors in some channels
    # At this point we can have:
    #  scraper_return = True: An item with infoLabels with the updated information of the series
    #  scraper_return = False: An item without movie information (it has been canceled in the window)
    #  item.infoLabels['code'] == "" :T he required IMDB identifier was not found to continue, we quit
    if not scraper_return or not item.infoLabels['code']:
        logger.debug("NOT FOUND IN SCRAPER OR DO NOT HAVE code")
        return 0, 0, -1, path

    _id = item.infoLabels['code'][0]
    if not item.infoLabels['code'][0] or item.infoLabels['code'][0] == 'None': 
        if item.infoLabels['code'][1] and item.infoLabels['code'][1] != 'None':
            _id = item.infoLabels['code'][1]
        elif item.infoLabels['code'][2] and item.infoLabels['code'][2] != 'None':
            _id = item.infoLabels['code'][2]
        else:
            logger.error("NOT FOUND IN SCRAPER OR HAS NO CODE: " + item.url  + ' / ' + item.infoLabels['code'])
            return 0, 0, -1, path

    if config.get_setting("original_title_folder", "videolibrary") and item.infoLabels['originaltitle']:
        base_name = item.infoLabels['originaltitle']
    elif item.infoLabels['tvshowtitle']:
        base_name = item.infoLabels['tvshowtitle']
    elif item.infoLabels['title']:
        base_name = item.infoLabels['title']
    else:
        base_name = item.contentSerieName

    base_name = base_name.lstrip('.')

    if not PY3:
        base_name = unicode(filetools.validate_path(base_name.replace('/', '-')), "utf8").encode("utf8")
    else:
        base_name = filetools.validate_path(base_name.replace('/', '-'))


    if config.get_setting("lowerize_title", "videolibrary"):
        base_name = base_name.lower()

    for raiz, subcarpetas, ficheros in filetools.walk(TVSHOWS_PATH):
        for c in subcarpetas:
            code = scrapertools.find_single_match(c, r'\[(.*?)\]')
            if code and code != 'None' and code in item.infoLabels['code']:
                path = filetools.join(raiz, c)
                _id = code
                break

    if not path:
        path = filetools.join(TVSHOWS_PATH, ("%s [%s]" % (base_name, _id)).strip())
        logger.debug("Creating series directory: " + path)
        try:
            filetools.mkdir(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

    tvshow_path = filetools.join(path, "tvshow.nfo")
    if not filetools.exists(tvshow_path):
        # We create tvshow.nfo, if it does not exist, with the head_nfo, series info and watched episode marks
        logger.debug("Creating tvshow.nfo: " + tvshow_path)
        head_nfo = scraper.get_nfo(item, search_groups=True)
        if not head_nfo:
            return 0, 0, 0, ''
        item.infoLabels['mediatype'] = "tvshow"
        item.infoLabels['title'] = item.contentSerieName
        item_tvshow = Item(title=item.contentSerieName, channel="videolibrary", action="get_seasons",
                           fanart=item.infoLabels['fanart'], thumbnail=item.infoLabels['thumbnail'],
                           infoLabels=item.infoLabels, path=path.replace(TVSHOWS_PATH, ""), fulltitle=item.fulltitle)
        item_tvshow.library_playcounts = {}
        item_tvshow.library_urls = {item.channel: item.url}

    else:
        # If tvshow.nfo exists, but we are adding a new channel we update the list of urls
        head_nfo, item_tvshow = read_nfo(tvshow_path)
        item_tvshow.fulltitle = item.fulltitle
        item_tvshow.channel = "videolibrary"
        item_tvshow.action = "get_seasons"
        item_tvshow.library_urls[item.channel] = item.url

    # FILTERTOOLS
    # if the channel has a language filter, we add the channel and the show
    if episodelist and "list_language" in episodelist[0]:
        # if we have already added a previously filtered channel, we add or update the channel and show
        if "library_filter_show" in item_tvshow:
            if item.title_from_channel:
                item_tvshow.library_filter_show[item.channel] = item.title_from_channel
            else:
                item_tvshow.library_filter_show[item.channel] = item.show
        # there was no filter channel and we generated it for the first time
        else:
            if item.title_from_channel:
                item_tvshow.library_filter_show = {item.channel: item.title_from_channel}
            else:
                item_tvshow.library_filter_show = {item.channel: item.show}

    if item.channel != "downloads":
        item_tvshow.active = 1  # to be updated daily when service is called

    filetools.write(tvshow_path, head_nfo + item_tvshow.tojson())

    if not episodelist:
        # The episode list is empty
        return 0, 0, 0, path

    # Save the episodes
    '''import time
    start_time = time.time()'''
    insertados, sobreescritos, fallidos = save_episodes(path, episodelist, item, silent=silent)
    '''msg = "Insertados: %d | Sobreescritos: %d | Fallidos: %d | Tiempo: %2.2f segundos" % \
          (insertados, sobreescritos, fallidos, time.time() - start_time)
    logger.debug(msg)'''

    return insertados, sobreescritos, fallidos, path


def save_episodes(path, episodelist, serie, silent=False, overwrite=True):
    """
    saves in the indicated path all the chapters included in the episodelist
    @type path: str
    @param path: path to save the episodes
    @type episodelist: list
    @param episodelist: list of items that represent the episodes to be saved.
    @type serie: item
    @param serie: series from which to save the episodes
    @type silent: bool
    @param silent: sets whether notification is displayed
    @param overwrite: allows to overwrite existing files
    @type overwrite: bool
    @rtype insertados: int
    @return: the number of episodes inserted
    @rtype sobreescritos: int
    @return: the number of overwritten episodes
    @rtype fallidos: int
    @return: the number of failed episodes
    """
    logger.debug()
    if episodelist:
        episodelist = filter_list(episodelist, serie.action, path)
    # No episode list, nothing to save
    if not len(episodelist):
        logger.debug("There is no episode list, we go out without creating strm")
        return 0, 0, 0

    # process local episodes
    local_episodes_path = ''
    update = False
    nfo_path = filetools.join(path, "tvshow.nfo")
    head_nfo, item_nfo = read_nfo(nfo_path)
    local_episodelist = item_nfo.local_episodes_list if item_nfo.local_episodes_list else []

    if config.get_setting('videolibrary_kodi'):
        from platformcode.xbmc_videolibrary import check_db
        for p in check_db(item_nfo.infoLabels['code']):
            local_episodelist += get_local_content(p)
        item_nfo.local_episodes_list = local_episodelist
        filetools.write(nfo_path, head_nfo + item_nfo.tojson())

    if item_nfo.update_last:
        local_episodes_path = item_nfo.local_episodes_path
    elif config.get_setting("local_episodes", "videolibrary"):
        done, local_episodes_path = config_local_episodes_path(path, serie)
        if done < 0:
            logger.debug("An issue has occurred while configuring local episodes, going out without creating strm")
            return 0, 0, done
        item_nfo.local_episodes_path = local_episodes_path
        filetools.write(nfo_path, head_nfo + item_nfo.tojson())

    if local_episodes_path:
        process_local_episodes(local_episodes_path, path, local_episodelist)

    insertados = 0
    sobreescritos = 0
    fallidos = 0
    news_in_playcounts = {}
    # We list all the files in the series, so we avoid having to check if they exist one by one
    raiz, carpetas_series, ficheros = next(filetools.walk(path))
    ficheros = [filetools.join(path, f) for f in ficheros]

    # Silent is to show no progress (for service)
    if not silent:
        # progress dialog
        p_dialog = platformtools.dialog_progress(config.get_localized_string(60064) ,'')
        # p_dialog.update(0, config.get_localized_string(60065))

    channel_alt = serie.channel                                                    # We prepare to add the emergency urls
    emergency_urls_stat = config.get_setting("emergency_urls", channel_alt)         # Does the channel want emergency urls?
    emergency_urls_succ = False
    try: channel = __import__('specials.%s' % channel_alt, fromlist=["specials.%s" % channel_alt])
    except: channel = __import__('channels.%s' % channel_alt, fromlist=["channels.%s" % channel_alt])
    if serie.torrent_caching_fail:                                                  # If the conversion process has failed, they are not cached
        emergency_urls_stat = 0
        del serie.torrent_caching_fail

    new_episodelist = []
    # We obtain the season and episode number and discard those that are not

    for e in episodelist:
        headers = {}
        if e.headers:
            headers = e.headers

        try:
            season_episode = scrapertools.get_season_and_episode(e.title)

            # If the emergency url option has been checked, it is added to each episode after running Findvideos from the channel
            if e.emergency_urls and isinstance(e.emergency_urls, dict): del e.emergency_urls    # We erase previous traces
            json_path = filetools.join(path, ("%s [%s].json" % (season_episode, e.channel)).lower())    # Path of the episode .json
            if emergency_urls_stat == 1 and not e.emergency_urls and e.contentType == 'episode':     # Do we keep emergency urls?
                if not silent:
                    p_dialog.update(0, 'Caching links and .torren filest...\n' + e.title)     # progress dialog
                if json_path in ficheros:                                   # If there is the .json we get the urls from there
                    if overwrite:                                           # but only if .json are overwritten
                        json_epi = Item().fromjson(filetools.read(json_path))                   #We read the .json
                        if json_epi.emergency_urls:                         # if there are emergency urls ...
                            e.emergency_urls = json_epi.emergency_urls      # ... we copy them
                        else:                                               # if not...
                            e = emergency_urls(e, channel, json_path, headers=headers)  # ... we generate them
                else:
                    e = emergency_urls(e, channel, json_path, headers=headers)  # If the episode does not exist, we generate the urls
                if e.emergency_urls:                                        #If we already have urls...
                    emergency_urls_succ = True                              # ... is a success and we are going to mark the .nfo
            elif emergency_urls_stat == 2 and e.contentType == 'episode':   # Do we delete emergency urls?
                if e.emergency_urls: del e.emergency_urls
                emergency_urls_succ = True                                  # ... is a success and we are going to mark the .nfo
            elif emergency_urls_stat == 3 and e.contentType == 'episode':   # Do we update emergency urls?
                if not silent:
                    p_dialog.update(0, 'Caching links and .torrent files...\n' + e.title)     # progress dialog
                e = emergency_urls(e, channel, json_path, headers=headers)  # we generate the urls
                if e.emergency_urls:                                        # If we already have urls...
                    emergency_urls_succ = True                              # ... is a success and we are going to mark the .nfo

            if not e.infoLabels["tmdb_id"] or (serie.infoLabels["tmdb_id"] and e.infoLabels["tmdb_id"] != serie.infoLabels["tmdb_id"]):                                                    #en series multicanal, prevalece el infolabels...
                e.infoLabels = serie.infoLabels                             # ... dthe current channel and not the original one
            e.contentSeason, e.contentEpisodeNumber = season_episode.split("x")
            if e.videolibray_emergency_urls:
                del e.videolibray_emergency_urls
            if e.channel_redir:
                del e.channel_redir                                         # ... and redirect marks are erased
            new_episodelist.append(e)
        except:
            if e.contentType == 'episode':
                logger.error("Unable to save %s emergency urls in the video library" % e.contentTitle)
            continue

    # No episode list, nothing to save
    if not len(new_episodelist):
        logger.debug("There is no episode list, we go out without creating strm")
        return 0, 0, 0

    local_episodelist += get_local_content(path)

    # fix float because division is done poorly in python 2.x
    try:
        t = float(100) / len(new_episodelist)
    except:
        t = 0
    for i, e in enumerate(scraper.sort_episode_list(new_episodelist)):
        if not silent:
            p_dialog.update(int(math.ceil((i + 1) * t)), e.title)

        high_sea = e.contentSeason
        high_epi = e.contentEpisodeNumber
        if scrapertools.find_single_match(e.title, r'[a|A][l|L]\s*(\d+)'):
            high_epi = int(scrapertools.find_single_match(e.title, r'al\s*(\d+)'))
        max_sea = e.infoLabels["number_of_seasons"]
        max_epi = 0
        if e.infoLabels["number_of_seasons"] and (e.infoLabels["temporada_num_episodios"] or e.infoLabels["number_of_seasons"] == 1):
            if e.infoLabels["number_of_seasons"] == 1 and e.infoLabels["number_of_episodes"]:
                max_epi = e.infoLabels["number_of_episodes"]
            else:
                max_epi = e.infoLabels["temporada_num_episodios"]

        season_episode = "%sx%s" % (e.contentSeason, str(e.contentEpisodeNumber).zfill(2))
        strm_path = filetools.join(path, "%s.strm" % season_episode)
        nfo_path = filetools.join(path, "%s.nfo" % season_episode)
        json_path = filetools.join(path, ("%s [%s].json" % (season_episode, e.channel)).lower())

        if season_episode in local_episodelist:
            logger.debug('Skipped: Serie ' + serie.contentSerieName + ' ' + season_episode + ' available as local content')
            continue

        # check if the episode has been downloaded
        if filetools.join(path, "%s [downloads].json" % season_episode) in ficheros:
            logger.debug('INFO: "%s" episode %s has been downloaded, skipping it' % (serie.contentSerieName, season_episode))
            continue

        strm_exists = strm_path in ficheros
        nfo_exists = nfo_path in ficheros
        json_exists = json_path in ficheros

        if not strm_exists:
            # If there is no season_episode.strm add it
            item_strm = Item(action='play_from_library', channel='videolibrary', strm_path=strm_path.replace(TVSHOWS_PATH, ""), infoLabels={})
            item_strm.contentSeason = e.contentSeason
            item_strm.contentEpisodeNumber = e.contentEpisodeNumber
            item_strm.contentType = e.contentType
            item_strm.contentTitle = season_episode

            # FILTERTOOLS
            if item_strm.list_language:
                # if tvshow.nfo has a filter it is passed to the item_strm to be generated
                if "library_filter_show" in serie:
                    item_strm.library_filter_show = serie.library_filter_show

                if item_strm.library_filter_show == "":
                    logger.error("There was an error getting the name of the series to filter")

            # logger.debug("item_strm" + item_strm.tostring('\n'))
            # logger.debug("serie " + serie.tostring('\n'))
            strm_exists = filetools.write(strm_path, '%s?%s' % (addon_name, item_strm.tourl()))

        item_nfo = None
        if not nfo_exists and e.infoLabels["code"]:
            # If there is no season_episode.nfo add it
            if serie.infoLabels["code"]:
                e.infoLabels["code"] = serie.infoLabels["code"]
            else:
                scraper.find_and_set_infoLabels(e)
            head_nfo = scraper.get_nfo(e)

            item_nfo = e.clone(channel="videolibrary", url="", action='findvideos', strm_path=strm_path.replace(TVSHOWS_PATH, ""))
            if item_nfo.emergency_urls:
                del item_nfo.emergency_urls                     # It only stays in the episode's .json

            nfo_exists = filetools.write(nfo_path, head_nfo + item_nfo.tojson())

        # Only if there are season_episode.nfo and season_episode.strm we continue
        if nfo_exists and strm_exists:
            if not json_exists or overwrite:
                # We get infoLabel from the episode
                if not item_nfo:
                    head_nfo, item_nfo = read_nfo(nfo_path)

                # In multichannel series, the infolabels of the current channel prevail and not that of the original
                if not e.infoLabels["tmdb_id"] or (item_nfo.infoLabels["tmdb_id"] and e.infoLabels["tmdb_id"] != item_nfo.infoLabels["tmdb_id"]): 
                    e.infoLabels = item_nfo.infoLabels

                if filetools.write(json_path, e.tojson()):
                    if not json_exists:
                        logger.debug("Inserted: %s" % json_path)
                        insertados += 1
                        # We mark episode as unseen
                        news_in_playcounts[season_episode] = 0
                        # We mark the season as unseen
                        news_in_playcounts["season %s" % e.contentSeason] = 0
                        # We mark the series as unseen
                        # logger.debug("serie " + serie.tostring('\n'))
                        news_in_playcounts[serie.contentSerieName] = 0

                    else:
                        logger.debug("Overwritten: %s" % json_path)
                        sobreescritos += 1
                else:
                    logger.debug("Failed: %s" % json_path)
                    fallidos += 1

        else:
            logger.debug("Failed: %s" % json_path)
            fallidos += 1

        if not silent and p_dialog.iscanceled():
            break

    #logger.debug('high_sea x high_epi: %sx%s' % (str(high_sea), str(high_epi)))
    #logger.debug('max_sea x max_epi: %sx%s' % (str(max_sea), str(max_epi)))
    if not silent:
        p_dialog.close()

    if news_in_playcounts or emergency_urls_succ or serie.infoLabels["status"] == "Ended" or serie.infoLabels["status"] == "Canceled":
        # If there are new episodes we mark them as unseen on tvshow.nfo ...
        tvshow_path = filetools.join(path, "tvshow.nfo")
        try:
            import datetime
            head_nfo, tvshow_item = read_nfo(tvshow_path)
            tvshow_item.library_playcounts.update(news_in_playcounts)

            # If the emergency url insert / delete operation in the .jsons of the episodes was successful, the .nfo is checked
            if emergency_urls_succ:
                if tvshow_item.emergency_urls and not isinstance(tvshow_item.emergency_urls, dict):
                    del tvshow_item.emergency_urls
                if emergency_urls_stat in [1, 3]:                               # Save / update links operation
                    if not tvshow_item.emergency_urls:
                        tvshow_item.emergency_urls = dict()
                    if tvshow_item.library_urls.get(serie.channel, False):
                        tvshow_item.emergency_urls.update({serie.channel: True})
                elif emergency_urls_stat == 2:                                  # Delete links operation
                    if tvshow_item.emergency_urls and tvshow_item.emergency_urls.get(serie.channel, False):
                        tvshow_item.emergency_urls.pop(serie.channel, None)     # delete the entry of the .nfo

            if tvshow_item.active == 30:
                tvshow_item.active = 1
            if tvshow_item.infoLabels["tmdb_id"] == serie.infoLabels["tmdb_id"]:
                tvshow_item.infoLabels = serie.infoLabels
                tvshow_item.infoLabels["title"] = tvshow_item.infoLabels["tvshowtitle"] 

            if max_sea == high_sea and max_epi == high_epi and (tvshow_item.infoLabels["status"] == "Ended" or tvshow_item.infoLabels["status"] == "Canceled") and insertados == 0 and fallidos == 0 and not tvshow_item.local_episodes_path:
                tvshow_item.active = 0                                          # ... nor we will update it more
                logger.debug("%s [%s]: 'Finished' or 'Canceled' series. Periodic update is disabled" %  (serie.contentSerieName, serie.channel))

            update_last = datetime.date.today()
            tvshow_item.update_last = update_last.strftime('%Y-%m-%d')
            update_next = datetime.date.today() + datetime.timedelta(days=int(tvshow_item.active))
            tvshow_item.update_next = update_next.strftime('%Y-%m-%d')

            filetools.write(tvshow_path, head_nfo + tvshow_item.tojson())
        except:
            logger.error("Error updating tvshow.nfo")
            logger.error("Unable to save %s emergency urls in the video library" % serie.contentSerieName)
            logger.error(traceback.format_exc())
            fallidos = -1
        else:
            # ... if it was correct we update the Kodi video library
            if config.is_xbmc() and config.get_setting("videolibrary_kodi") and not silent:
                update = True

    if update:
        from platformcode import xbmc_videolibrary
        xbmc_videolibrary.update()

    if fallidos == len(episodelist):
        fallidos = -1

    logger.debug("%s [%s]: inserted= %s, overwritten= %s, failed= %s" % (serie.contentSerieName, serie.channel, insertados, sobreescritos, fallidos))
    return insertados, sobreescritos, fallidos


def config_local_episodes_path(path, item, silent=False):
    logger.debug(item)
    from platformcode.xbmc_videolibrary import search_local_path
    local_episodes_path=search_local_path(item)
    if not local_episodes_path:
        title = item.contentSerieName if item.contentSerieName else item.show
        if not silent:
            silent = platformtools.dialog_yesno(config.get_localized_string(30131), config.get_localized_string(80044) % title)
        if silent:
            if config.is_xbmc() and not config.get_setting("videolibrary_kodi"):
                platformtools.dialog_ok(config.get_localized_string(30131), config.get_localized_string(80043))
            local_episodes_path = platformtools.dialog_browse(0, config.get_localized_string(80046))
            if local_episodes_path == '':
                logger.debug("User has canceled the dialog")
                return -2, local_episodes_path
            elif path in local_episodes_path:
                platformtools.dialog_ok(config.get_localized_string(30131), config.get_localized_string(80045))
                logger.debug("Selected folder is the same of the TV show one")
                return -2, local_episodes_path

    if local_episodes_path:
        # import artwork
        artwork_extensions = ['.jpg', '.jpeg', '.png']
        files = filetools.listdir(local_episodes_path)
        for file in files:
            if os.path.splitext(file)[1] in artwork_extensions:
                filetools.copy(filetools.join(local_episodes_path, file), filetools.join(path, file))

    return 0, local_episodes_path


def process_local_episodes(local_episodes_path, path, local_episodes_list):
    logger.debug()

    sub_extensions = ['.srt', '.sub', '.sbv', '.ass', '.idx', '.ssa', '.smi']
    artwork_extensions = ['.jpg', '.jpeg', '.png']
    extensions = sub_extensions + artwork_extensions

    files_list = []
    for root, folders, files in filetools.walk(local_episodes_path):
        for file in files:
            if os.path.splitext(file)[1] in extensions:
                continue
            season_episode = scrapertools.get_season_and_episode(file)
            if season_episode and season_episode not in local_episodes_list:
                local_episodes_list.append(season_episode)
                files_list.append(file)

    nfo_path = filetools.join(path, "tvshow.nfo")
    head_nfo, item_nfo = read_nfo(nfo_path)

    # if a local episode has been added, overwrites the strm
    for season_episode, file in zip(local_episodes_list, files_list):
        if not season_episode in item_nfo.local_episodes_list:
            filetools.write(filetools.join(path, season_episode + '.strm'), filetools.join(root, file))

    # if a local episode has been removed, deletes the strm
    for season_episode in set(item_nfo.local_episodes_list).difference(local_episodes_list):
        filetools.remove(filetools.join(path, season_episode + '.strm'))

    # updates the local episodes path and list in the nfo
    if not local_episodes_list:
        item_nfo.local_episodes_path = ''
    item_nfo.local_episodes_list = sorted(set(local_episodes_list))

    filetools.write(nfo_path, head_nfo + item_nfo.tojson())


def get_local_content(path):
    logger.debug()

    local_episodelist = []
    for root, folders, files in filetools.walk(path):
        for file in files:
            season_episode = scrapertools.get_season_and_episode(file)
            if season_episode == "" or filetools.exists(filetools.join(path, "%s.strm" % season_episode)):
                continue
            local_episodelist.append(season_episode)
    local_episodelist = sorted(set(local_episodelist))

    return local_episodelist


def add_to_videolibrary(item, channel):
    itemlist = getattr(channel, item.from_action)(item)
    if itemlist and itemlist[0].contentType == 'episode':
        return add_tvshow(item, channel, itemlist)
    else:
        return add_movie(item)


def add_movie(item):
    """
        Keep a movie at the movie library. The movie can be a link within a channel or a previously downloaded video.

        To add locally downloaded episodes, the item must have exclusively:
            - contentTitle: title of the movie
            - title: title to show next to the list of links -findvideos- ("Play local HD video")
            - infoLabels ["tmdb_id"] o infoLabels ["imdb_id"]
            - contentType == "movie"
            - channel = "downloads"
            - url: local path to the video

        @type item: item
        @param item: item to be saved.
    """
    logger.debug()
    # from platformcode.launcher import set_search_temp; set_search_temp(item)
    item.contentType = 'movie'

    # To disambiguate titles, TMDB is caused to ask for the really desired title
    # The user can select the title among those offered on the first screen
    # or you can cancel and enter a new title on the second screen
    # If you do it in "Enter another name", TMDB will automatically search for the new title
    # If you do it in "Complete Information", it partially changes to the new title, but does not search TMDB. We have to do it
    # If the second screen is canceled, the variable "scraper_return" will be False. The user does not want to continue
    item = generictools.update_title(item) # We call the method that updates the title with tmdb.find_and_set_infoLabels
    #if item.tmdb_stat:
    #    del item.tmdb_stat          # We clean the status so that it is not recorded in the Video Library
    if item:
        new_item = item.clone(action="findvideos")
        insertados, sobreescritos, fallidos, path = save_movie(new_item)

        if fallidos == 0:
            platformtools.dialog_ok(config.get_localized_string(30131),
                                    config.get_localized_string(30135) % new_item.contentTitle)  # 'has been added to the video library'
        else:
            filetools.rmdirtree(path)
            platformtools.dialog_ok(config.get_localized_string(30131),
                                    config.get_localized_string(60066) % new_item.contentTitle)  # "ERROR, the movie has NOT been added to the video library")


def add_tvshow(item, channel=None, itemlist=[]):
    """
        Save content in the series library. This content can be one of these two:
            - The series with all the chapters included in the episodelist.
            - A single chapter previously downloaded locally.

        To add locally downloaded episodes, the item must have exclusively:
            - contentSerieName (or show): Title of the series
            - contentTitle: title of the episode to extract season_and_episode ("1x01 Pilot")
            - title: title to show next to the list of links -findvideos- ("Play local video")
            - infoLabels ["tmdb_id"] o infoLabels ["imdb_id"]
            - contentType != "movie"
            - channel = "downloads"
            - url: local path to the video

        @type item: item
        @param item: item that represents the series to save
        @type channel: modulo
        @param channel: channel from which the series will be saved. By default, item.from_channel or item.channel will be imported.

    """

    logger.debug("show=#" + item.show + "#")
    item.contentType = 'tvshow'
    # from platformcode.launcher import set_search_temp; set_search_temp(item)

    if item.channel == "downloads":
        itemlist = [item.clone()]

    else:
        # This mark is because the item has something else apart in the "extra" attribute
        # item.action = item.extra if item.extra else item.action
        if isinstance(item.extra, str) and "###" in item.extra:
            item.action = item.extra.split("###")[0]
            item.extra = item.extra.split("###")[1]

        if item.from_action:
            item.__dict__["action"] = item.__dict__.pop("from_action")
        if item.from_channel:
            item.__dict__["channel"] = item.__dict__.pop("from_channel")

        if not channel:
            try:
                channel = __import__('channels.%s' % item.channel, fromlist=["channels.%s" % item.channel])
                # channel = __import__('specials.%s' % item.channel, fromlist=["specials.%s" % item.channel])
            except ImportError:
                exec("import channels." + item.channel + " as channel")

        # To disambiguate titles, TMDB is caused to ask for the really desired title
        # The user can select the title among those offered on the first screen
        # or you can cancel and enter a new title on the second screen
        # If you do it in "Enter another name", TMDB will automatically search for the new title
        # If you do it in "Complete Information", it partially changes to the new title, but does not search TMDB. We have to do it
        # If the second screen is canceled, the variable "scraper_return" will be False. The user does not want to continue

        item = generictools.update_title(item) # We call the method that updates the title with tmdb.find_and_set_infoLabels
        if not item: return
        #if item.tmdb_stat:
        #    del item.tmdb_stat          # We clean the status so that it is not recorded in the Video Library

        # Get the episode list
        # from core.support import dbg;dbg()
        if not itemlist: itemlist = getattr(channel, item.action)(item)
        if itemlist and not scrapertools.find_single_match(itemlist[0].title, r'[Ss]?(\d+)(?:x|_|\s+)[Ee]?[Pp]?(\d+)'):
            from platformcode.autorenumber import start, check
            if not check(item):
                action = item.action
                item.renumber = True
                item.disabletmdb = True
                start(item)
                item.renumber = False
                item.action = action
                if not item.exit:
                    return add_tvshow(item, channel)
                itemlist = getattr(channel, item.action)(item)
            else:
                itemlist = getattr(channel, item.action)(item)

    global magnet_caching
    magnet_caching = False
    insertados, sobreescritos, fallidos, path = save_tvshow(item, itemlist)

    if not path:
        pass

    elif not insertados and not sobreescritos and not fallidos:
        filetools.rmdirtree(path)
        platformtools.dialog_ok(config.get_localized_string(30131), config.get_localized_string(60067) % item.show)
        logger.error("The string %s could not be added to the video library. Could not get any episode" % item.show)

    elif fallidos == -1:
        filetools.rmdirtree(path)
        platformtools.dialog_ok(config.get_localized_string(30131), config.get_localized_string(60068) % item.show)
        logger.error("The string %s could not be added to the video library" % item.show)

    elif fallidos == -2:
        filetools.rmdirtree(path)

    elif fallidos > 0:
        platformtools.dialog_ok(config.get_localized_string(30131), config.get_localized_string(60069) % item.show)
        logger.error("Could not add %s episodes of series %s to the video library" % (fallidos, item.show))

    else:
        platformtools.dialog_ok(config.get_localized_string(30131), config.get_localized_string(60070) % item.show)
        logger.debug("%s episodes of series %s have been added to the video library" % (insertados, item.show))
        if config.is_xbmc():
            if config.get_setting("sync_trakt_new_tvshow", "videolibrary"):
                import xbmc
                from platformcode import xbmc_videolibrary
                if config.get_setting("sync_trakt_new_tvshow_wait", "videolibrary"):
                    # Check that you are not looking for content in the Kodi video library
                    while xbmc.getCondVisibility('Library.IsScanningVideo()'):
                        xbmc.sleep(1000)
                # Synchronization for Kodi video library launched
                xbmc_videolibrary.sync_trakt_kodi()
                # Synchronization for the addon video library is launched
                xbmc_videolibrary.sync_trakt_addon(path)


def emergency_urls(item, channel=None, path=None, headers={}):
    logger.debug()
    import re
    from servers import torrent
    try:
        magnet_caching_e = magnet_caching
    except:
        magnet_caching_e = True

    """
    We call Findvideos of the channel with the variable "item.videolibray_emergency_urls = True" to get the variable
    "item.emergency_urls" with the list of tuple lists of torrent links and direct servers for that episode or movie
    Torrents should always go in list [0], if any. If you want to cache the .torrents, the search goes against that list.
    List two will include direct server links, but also magnet links (which are not cacheable).
    """
    # we launched a "lookup" in the "findvideos" of the channel to obtain the emergency links
    try:
        if channel == None:                             # If the caller has not provided the channel structure, it is created
            channel = item.channel                      # It is verified if it is a clone, which returns "newpct1"
            #channel = __import__('channels.%s' % channel, fromlist=["channels.%s" % channel])
            channel = __import__('specials.%s' % channel_alt, fromlist=["specials.%s" % channel_alt])
        if hasattr(channel, 'findvideos'):                                  # If the channel has "findvideos" ...
            item.videolibray_emergency_urls = True                          # ... marks itself as "lookup"
            channel_save = item.channel                 # ... save the original channel in case of fail-over in Newpct1
            category_save = item.category               # ... save the original category in case of fail-over or redirection in Newpct1
            if item.channel_redir:                      # ... if there is a redir, the alternate channel is temporarily restored
                item.channel = scrapertools.find_single_match(item.url, r'http.?\:\/\/(?:www.)?(\w+)\.\w+\/').lower()
                item.category = scrapertools.find_single_match(item.url, r'http.?\:\/\/(?:www.)?(\w+)\.\w+\/').capitalize()
            item_res = getattr(channel, 'findvideos')(item)                 # ... the process of Findvideos
            item_res.channel = channel_save             # ... restore the original channel in case there is a fail-over in Newpct1
            item_res.category = category_save           # ... restore the original category in case there is a fail-over or redirection in Newpct1
            item.category = category_save               # ... restore the original category in case there is a fail-over or redirection in Newpct1
            del item_res.videolibray_emergency_urls                         # ... and the lookup mark is erased
            if item.videolibray_emergency_urls:
                del item.videolibray_emergency_urls                         # ... and the original lookup mark is erased
    except:
        logger.error('ERROR when processing the title in Findvideos del Canal: ' + item.channel + ' / ' + item.title)
        logger.error(traceback.format_exc())
        item.channel = channel_save                     # ... restore the original channel in case of fail-over or redirection in Newpct1
        item.category = category_save                   # ... restore the original category in case there is a fail-over or redirection in Newpct1
        item_res = item.clone()                         # If there has been an error, the original Item is returned
        if item_res.videolibray_emergency_urls:
            del item_res.videolibray_emergency_urls                         # ... and the lookup mark is erased
        if item.videolibray_emergency_urls:
            del item.videolibray_emergency_urls                             # ... and the original lookup mark is erased
    
    # If the user has activated the option "emergency_urls_torrents", the .torrent files of each title will be downloaded
    else:                                                                   # If the links have been successfully cached ...
        try:
            referer = None
            post = None
            channel_bis =item.channel
            if config.get_setting("emergency_urls_torrents", channel_bis) and item_res.emergency_urls and path != None:
                videolibrary_path = config.get_videolibrary_path()          # we detect the absolute path of the title
                movies = config.get_setting("folder_movies")
                series = config.get_setting("folder_tvshows")
                if movies in path:
                    folder = movies
                else:
                    folder = series
                videolibrary_path = filetools.join(videolibrary_path, folder)
                i = 1
                if item_res.referer: referer = item_res.referer
                if item_res.post: post = item_res.post
                for url in item_res.emergency_urls[0]:                      # We go through the emergency urls ...
                    torrents_path = re.sub(r'(?:\.\w+$)', '_%s.torrent' % str(i).zfill(2), path)
                    path_real = ''
                    if magnet_caching_e or not url.startswith('magnet'):
                        path_real = torrent.caching_torrents(url, referer, post, torrents_path=torrents_path, headers=headers)  # ... to download the .torrents
                    if path_real:                                           # If you have been successful ...
                        item_res.emergency_urls[0][i-1] = path_real.replace(videolibrary_path, '')  # if it looks at the relative "path"
                    i += 1

                # We restore original variables
                if item.referer:
                    item_res.referer = item.referer
                elif item_res.referer:
                    del item_res.referer
                if item.referer:
                    item_res.referer = item.referer
                elif item_res.referer:
                    del item_res.referer
                item_res.url = item.url

        except:
            logger.error('ERROR when caching the .torrent of: ' + item.channel + ' / ' + item.title)
            logger.error(traceback.format_exc())
            item_res = item.clone()                             # If there has been an error, the original Item is returned

    #logger.debug(item_res.emergency_urls)
    return item_res                                             # We return the updated Item with the emergency links

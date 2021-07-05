# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Common Library Tools
# ------------------------------------------------------------

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3: from concurrent import futures
else: from concurrent_py2 import futures

import math, traceback, re, os

from core import filetools, scraper, scrapertools, support, httptools, tmdb
from core.item import Item
from lib import generictools
from platformcode import config, logger, platformtools
from platformcode.autorenumber import RENUMBER
from core.videolibrarydb import videolibrarydb

FOLDER_MOVIES = config.get_setting("folder_movies")
FOLDER_TVSHOWS = config.get_setting("folder_tvshows")
VIDEOLIBRARY_PATH = config.get_videolibrary_path()
MOVIES_PATH = filetools.join(VIDEOLIBRARY_PATH, FOLDER_MOVIES)
TVSHOWS_PATH = filetools.join(VIDEOLIBRARY_PATH, FOLDER_TVSHOWS)

if not FOLDER_MOVIES or not FOLDER_TVSHOWS or not VIDEOLIBRARY_PATH or not filetools.exists(MOVIES_PATH) or not filetools.exists(TVSHOWS_PATH):
    config.verify_directories_created()

addon_name = "plugin://plugin.video.%s/" % config.PLUGIN_NAME

quality_order = ['4k', '2160p', '2160', '4k2160p', '4k2160', '4k 2160p', '4k 2160', '2k',
                 'fullhd', 'fullhd 1080', 'fullhd 1080p', 'full hd', 'full hd 1080', 'full hd 1080p', 'hd1080', 'hd1080p', 'hd 1080', 'hd 1080p', '1080', '1080p',
                 'hd', 'hd720', 'hd720p', 'hd 720', 'hd 720p', '720', '720p', 'hdtv',
                 'sd', '480p', '480', '360p', '360', '240p', '240']

video_extensions = ['3g2', '3gp', '3gp2', 'asf', 'avi', 'divx', 'flv', 'iso', 'm4v', 'mk2', 'mk3d', 'mka', 'mkv', 'mov', 'mp4', 'mp4a', 'mpeg', 'mpg', 'ogg', 'ogm', 'ogv', 'qt', 'ra', 'ram', 'rm', 'ts', 'vob', 'wav', 'webm', 'wma', 'wmv']
subtitle_extensions = ['srt', 'idx', 'sub', 'ssa', 'ass']
image_extensions = ['.jpg', '.jpeg', '.png']
library_extension = ['.nfo', '.strm', '.json']


def save_movie(item, silent=False):
    """
    saves the item element in the movie library, with the values ​​it contains.
    @type item: item
    @param item: item to be saved.
    @rtype inserted: int
    @return: the number of elements inserted
    @rtype overwritten: int
    @return: the number of overwritten elements
    @rtype failed: int
    @return: the number of failed items or -1 if all failed
    """

    logger.debug()
    # logger.debug(item.tostring('\n'))
    inserted = 0
    overwritten = 0
    failed = 0
    path = ""

    # Put the correct title on your site so that scraper can locate it
    if not item.contentTitle:
        if item.fulltitle: item.contentTitle = item.fulltitle
        else: item.contentTitle = re.sub(r'\[\s*[^\]]+\]', '', item.title).strip()

    # If at this point we do not have a title, we leave
    if not item.contentTitle or not item.channel:
        logger.debug("contentTitle NOT FOUND")
        return 0, 0, -1, path  # Salimos sin guardar

    # At this point we can have:
    #  scraper_return = True: An item with infoLabels with the updated information of the movie
    #  scraper_return = False: An item without movie information (it has been canceled in the window)
    #  item.infoLabels['code'] == "" : The required IMDB identifier was not found to continue, we quit
    if not item.infoLabels['code']:
        logger.debug("NOT FOUND IN SCRAPER OR DO NOT HAVE code")
        return 0, 0, -1, path

    # Get ID from infoLabels
    _id = get_id(item)
    if not _id:
        logger.debug("NOT FOUND IN SCRAPER OR DO NOT HAVE code")
        return 0, 0, -1, path

    # get parameters from db
    try:
        moviedb = videolibrarydb['movie'].get(_id, {})
        movie_item = moviedb.get('item', Item())
        head_nfo = movie_item.head_nfo
        channels = moviedb.get('channels',{})
    except:
        logger.debug("The film cannot be added to the database")
        videolibrarydb.close()
        return 0, 0, -1, path

    # progress dialog
    if not silent: p_dialog = platformtools.dialog_progress_bg(config.get_localized_string(20000), config.get_localized_string(60062))

    base_name = set_base_name(item, _id)
    path = filetools.join(MOVIES_PATH, base_name)

    it, local_files = get_local_files(path, item)

    # check if path already exist
    if not filetools.exists(path):
        logger.debug("Creating movie directory:" + path)
        if not filetools.mkdir(path):
            logger.debug("Could not create directory")
            videolibrarydb.close()
            return 0, 0, -1, path
    try:
        # set nfo and strm paths
        nfo_path = filetools.join(base_name, "{}.nfo".format(base_name))
        strm_path = filetools.join(base_name, "{}.strm".format(base_name))

        # check if nfo and strm file exist
        nfo_exists = filetools.exists(filetools.join(MOVIES_PATH, nfo_path))
        strm_exists = filetools.exists(filetools.join(MOVIES_PATH, strm_path))

        if not head_nfo:
            head_nfo = scraper.get_nfo(item)


        # get extra info from fanart tv
        # support.dbg()
        extra_info = get_fanart_tv(item)
        if not item.infoLabels.get('posters', []): item.infoLabels['posters'] = []
        item.infoLabels['posters'] += extra_info['poster']
        if not item.infoLabels.get('fanarts', []): item.infoLabels['fanarts'] = []
        item.infoLabels['fanarts'] += extra_info['fanart']
        if not item.infoLabels.get('clearlogos', []): item.infoLabels['clearlogos'] = []
        item.infoLabels['clearlogos'] += extra_info['clearlogo']
        if not item.infoLabels.get('cleararts', []): item.infoLabels['cleararts'] = []
        item.infoLabels['cleararts'] += extra_info['clearart']
        if not item.infoLabels.get('landscapes', []): item.infoLabels['landscapes'] = []
        item.infoLabels['landscapes'] += extra_info['landscape']
        if not item.infoLabels.get('banners', []): item.infoLabels['banners'] = []
        item.infoLabels['banners'] += extra_info['banner']
        if not item.infoLabels.get('discs', []): item.infoLabels['discs'] = []
        item.infoLabels['discs'] += extra_info['disc']

        if 'setid' in item.infoLabels:
            c_playcount = 0
            collection = videolibrarydb['collection'].get(item.infoLabels['setid'], None)
            if item.infoLabels.get('playcount', 0) > 0:
                collections = [c for c in dict(videolibrarydb['collection']).values() if c.infoLabels.get('setid') == item.infoLabels['setid']]
                viewed = [c for c in collections if c.infoLabels.get('playcount') > 0]
                if len(collections) == len(viewed):
                    c_playcount = 1
            if not collection:
                collection = Item(title=item.infoLabels['set'],
                                plot=item.infoLabels['setoverview'],
                                infoLabels={'playcount':c_playcount},
                                thumbnail=item.infoLabels.get('setposters')[0] if item.infoLabels.get('setposters') else item.thumbnail,
                                fanart=item.infoLabels.get('setfanarts')[0] if item.infoLabels.get('setfanarts') else item.fanart,
                                videolibrary_id = item.infoLabels['setid'],
                                set = item.infoLabels['setid'],
                                channel = "videolibrary",
                                action='list_movies')

            if not collection.infoLabels.get('posters') and item.infoLabels.get('setposters'):
                collection.infoLabels['posters'] = item.infoLabels['setposters']
            if not collection.infoLabels.get('fanarts') and item.infoLabels.get('fanarts'):
                collection.infoLabels['fanarts'] = item.infoLabels['setfanarts']
            if not collection.infoLabels.get('clearlogos') and extra_info.get('setclearlogo'):
                collection.infoLabels['clearlogos'] = extra_info['setclearlogo']
                collection.infoLabels['clearlogo'] = extra_info['setclearlogo'][0]
            if not collection.infoLabels.get('cleararts') and extra_info.get('setclearart'):
                collection.infoLabels['cleararts'] = extra_info['setclearart']
                collection.infoLabels['clearart'] = extra_info['setclearart'][0]
            if not collection.infoLabels.get('landscapes') and extra_info.get('setlandscape'):
                collection.infoLabels['landscapes'] = extra_info['setlandscape']
                collection.infoLabels['landscape'] = extra_info['setlandscape'][0]
            if not collection.infoLabels.get('banners') and extra_info.get('setbanner'):
                collection.infoLabels['banners'] = extra_info['setbanner']
                collection.infoLabels['banner'] = extra_info['setbanner'][0]
            if not collection.infoLabels.get('discs') and extra_info.get('setdisc'):
                collection.infoLabels['discs'] = extra_info['setdisc']
                collection.infoLabels['disc'] = extra_info['setdisc'][0]
            videolibrarydb['collection'][item.infoLabels['setid']] = collection


        # Make or update Videolibrary Movie Item
        movie_item.channel = "videolibrary"
        movie_item.action = 'findvideos'
        movie_item.infoLabels = item.infoLabels
        movie_item.infoLabels['playcount'] = item.infoLabels.get('playcount',0)
        if not movie_item.head_nfo: movie_item.head_nfo = head_nfo
        if not movie_item.title: movie_item.title = item.contentTitle
        if not movie_item.videolibrary_id: movie_item.videolibrary_id = _id
        if not movie_item.strm_path: movie_item.strm_path = strm_path
        if not movie_item.nfo_path: movie_item.nfo_path = nfo_path
        if not movie_item.base_name: movie_item.base_name = base_name
        if not movie_item.thumbnail: movie_item.thumbnail = item.infoLabels['thumbnail']
        if not movie_item.fanart: movie_item.fanart = item.infoLabels['fanart']
        if not movie_item.infoLabels['landscape'] and item.infoLabels['landscapes']: movie_item.infoLabels['landscape'] = item.infoLabels['landscapes'][0]
        if not movie_item.infoLabels['banner'] and item.infoLabels['banners']: movie_item.infoLabels['banner']= item.infoLabels['banners'][0]
        if not movie_item.infoLabels['clearart'] and item.infoLabels['cleararts']: movie_item.infoLabels['clearart'] = item.infoLabels['cleararts'][0]
        if not movie_item.infoLabels['clearlogo'] and item.infoLabels['clearlogos']: movie_item.infoLabels['clearlogo'] = item.infoLabels['clearlogos'][0]
        if not movie_item.infoLabels['disc'] and item.infoLabels['discs']: movie_item.infoLabels['disc'] = item.infoLabels['discs'][0]
        if not movie_item.prefered_lang: movie_item.prefered_lang = ''
        if not movie_item.lang_list: movie_item.lang_list = []
        movie_item.no_reload = item.no_reload

        if not item.contentLanguage: item.contentLanguage = 'ITA'
        if not item.contentLanguage in movie_item.lang_list: movie_item.lang_list.append(item.contentLanguage)

        if len(movie_item.lang_list) > 1:
            movie_item.prefered_lang = movie_item.lang_list[platformtools.dialog_select(config.get_localized_string(70246), movie_item.lang_list)]
        else:
            movie_item.prefered_lang = movie_item.lang_list[0]

        # create nfo file if it does not exist

        if not nfo_exists:
            filetools.write(filetools.join(MOVIES_PATH, movie_item.nfo_path), head_nfo)

        # create strm file if it does not exist
        if not strm_exists and not local_files:
            logger.debug("Creating .strm: " + strm_path)
            item_strm = Item(channel='videolibrary', action='play_from_library', strm_path=movie_item.strm_path, contentType='movie', contentTitle=item.contentTitle, videolibrary_id=movie_item.videolibrary_id)
            strm_exists = filetools.write(filetools.join(MOVIES_PATH, movie_item.strm_path), '{}?{}'.format(addon_name, item_strm.tourl()))

        # checks if the content already exists
        if videolibrarydb['movie'].get(_id, {}):
            logger.debug("The file exists. Is overwritten")
            overwritten += 1
        else:
            logger.debug("Creating .nfo: " + nfo_path)
            inserted += 1

        remove_host(item)
        # write on db
        if item.channel in channels and item.channel != 'download':
            channels_url = [u.url for u in channels[item.channel]]
            if item.url not in channels_url:
                channels[item.channel].append(item)
            else:
                del channels[item.channel][channels_url.index(item.url)]
                channels[item.channel].append(item)
        else:
            channels[item.channel] = [item]

        if local_files.get('db') or local_files.get('internal'):
            if local_files.get('db'):
                channels['local']['db'] = local_files['db'][0]
            elif local_files.get('internal'):
                channels['local']['db']  = local_files['internal'][0]

        moviedb['item'] = movie_item
        moviedb['channels'] = channels

        videolibrarydb['movie'][_id] = moviedb
    except:
        failed += 1

    videolibrarydb.close()


    # Only if movie_item and .strm exist we continue
    if failed == 0:
        if not silent:
            p_dialog.update(100, item.contentTitle)
            p_dialog.close()
        # Update Kodi Library
        from platformcode.dbconverter import add_video
        add_video(movie_item)
        # if config.is_xbmc() and config.get_setting("videolibrary_kodi") and not silent and inserted:
            # from platformcode.xbmc_videolibrary import update
            # update(MOVIES_PATH)
        return inserted, overwritten, failed, path

    # If we get to this point it is because something has gone wrong
    logger.error("Could not save %s in the video library" % item.contentTitle)
    if not silent:
        p_dialog.update(100, item.contentTitle)
        p_dialog.close()
    return 0, 0, -1, path


def save_tvshow(item, episodelist, silent=False):
    """
    stores in the series library the series with all the chapters included in the episodelist
    @type item: item
    @param item: item that represents the series to save
    @type episodelist: list
    @param episodelist: list of items that represent the episodes to be saved.
    @rtype inserted: int
    @return: the number of episodes inserted
    @rtype overwritten: int
    @return: the number of overwritten episodes
    @rtype failed: int
    @return: the number of failed episodes or -1 if the entire series has failed
    @rtype path: str
    @return: serial directory
    """

    inserted = 0
    overwritten = 0
    failed = 0
    path = ""

    # If at this point we do not have a title or code, we leave
    if not (item.contentSerieName or item.infoLabels['code']) or not item.channel:
        logger.debug("NOT FOUND contentSerieName or code")
        return 0, 0, -1, path  # Salimos sin guardar

    # contentTypeBackup = item.contentType  # Fix errors in some channels
    # item.contentType = contentTypeBackup  # Fix errors in some channels
    # item.contentType = 'tvshow'

    # At this point we can have:
    #  scraper_return = True: An item with infoLabels with the updated information of the series
    #  scraper_return = False: An item without movie information (it has been canceled in the window)
    #  item.infoLabels['code'] == "" :T he required IMDB identifier was not found to continue, we quit
    if not item.infoLabels['code']:
        logger.debug("NOT FOUND IN SCRAPER OR DO NOT HAVE code")
        return 0, 0, -1, path

    # Get ID from infoLabels
    _id = get_id(item)
    if not _id:
        logger.debug("NOT FOUND IN SCRAPER OR DO NOT HAVE code")
        return 0, 0, -1, path

    # get parameters from db
    try:
        tvshowdb = videolibrarydb['tvshow'].get(_id, {})
        tvshow_item = tvshowdb.get('item', Item())
        head_nfo = tvshow_item.head_nfo
        channels = tvshowdb.get('channels',{})

    except:
        logger.debug("The tv show cannot be added to the database")
        videolibrarydb.close()
        return 0, 0, -1, path

    # set base name
    base_name = set_base_name(item, _id)
    path = filetools.join(TVSHOWS_PATH, base_name)

    item.local_episodes_path = tvshow_item.local_episodes_path
    item, local_files = get_local_files(path, item)
    tvshow_item.local_episodes_path = item.local_episodes_path

    # check if path already exist
    if not filetools.exists(path):
        logger.debug("Creating tv show directory:" + path)
        if not filetools.mkdir(path):
            logger.debug("Could not create directory")
            return 0, 0, -1, path

    nfo_path = filetools.join(base_name, "tvshow.nfo")
    nfo_exists = filetools.exists(filetools.join(TVSHOWS_PATH, nfo_path))

    # get parameters
    if not item.head_nfo:
        head_nfo = scraper.get_nfo(item)
    if not head_nfo: return 0, 0, -1, ''

    extra_info = get_fanart_tv(item)
    if not item.infoLabels.get('posters'):item.infoLabels['posters'] = []
    item.infoLabels['posters'] += extra_info['poster'].get('all',[])
    if not item.infoLabels.get('fanarts'): item.infoLabels['fanarts'] = []
    item.infoLabels['fanarts'] += extra_info['fanart']
    if not item.infoLabels.get('clearlogos'): item.infoLabels['clearlogos'] = []
    item.infoLabels['clearlogos'] += extra_info['clearlogo']
    if not item.infoLabels.get('cleararts'): item.infoLabels['cleararts'] = []
    item.infoLabels['cleararts'] += extra_info['clearart']
    if not item.infoLabels.get('landscapes'): item.infoLabels['landscapes'] = []
    item.infoLabels['landscapes'] += extra_info['landscape'].get('all',[])
    if not item.infoLabels.get('banners'):item.infoLabels['banners'] = []
    item.infoLabels['banners'] += extra_info['banner'].get('all',[])


    item.infoLabels['mediatype'] = 'tvshow'
    item.contentType = 'tvshow'
    if item.contentSerieName: item.infoLabels['title'] = item.contentSerieName
    tvshow_item.infoLabels = item.infoLabels
    if not tvshow_item.infoLabels.get('playcount'): tvshow_item.infoLabels['playcount'] = 0
    tvshow_item.channel = 'videolibrary'
    tvshow_item.action = 'get_seasons'
    tvshow_item.nfo_path = nfo_path
    if not tvshow_item.head_nfo: tvshow_item.head_nfo = head_nfo
    if not tvshow_item.title: tvshow_item.title = item.infoLabels['title']
    if not tvshow_item.videolibrary_id: tvshow_item.videolibrary_id = _id
    if not tvshow_item.thumbnail: tvshow_item.thumbnail = item.infoLabels['thumbnail']
    if not tvshow_item.fanart: tvshow_item.fanart = item.infoLabels['fanart']
    if not tvshow_item.infoLabels.get('landscape'): tvshow_item.infoLabels['landscape'] = item.infoLabels['landscapes'][0] if item.infoLabels['landscapes'] else item.infoLabels['fanart']
    if not tvshow_item.infoLabels.get('banner') and item.infoLabels['banners']: tvshow_item.infoLabels['banner'] = item.infoLabels['banners'][0]
    if not tvshow_item.infoLabels.get('clearart') and item.infoLabels['cleararts']: tvshow_item.infoLabels['clearart'] = item.infoLabels['cleararts'][0]
    if not tvshow_item.infoLabels.get('clearlogo') and item.infoLabels['clearlogos']: tvshow_item.infoLabels['clearlogo'] = item.infoLabels['clearlogos'][0]
    if not tvshow_item.base_name: tvshow_item.base_name = base_name
    if tvshow_item.active == '': tvshow_item.active = True
    if not tvshow_item.prefered_lang: tvshow_item.prefered_lang = ''
    if not tvshow_item.lang_list: tvshow_item.lang_list = []

    tvshow_item.no_reload = item.no_reload

    remove_host(item)

    item.renumber = add_renumber_options(item)

    # write on db
    if item.channel in channels and item.channel != 'download':
        channels_url = [u.url for u in channels[item.channel]]
        if item.url not in channels_url:
            channels[item.channel].append(item)
        else:
            del channels[item.channel][channels_url.index(item.url)]
            channels[item.channel].append(item)
    else:
        channels[item.channel] = [item]
    tvshowdb['item'] = tvshow_item
    tvshowdb['channels'] = channels
    videolibrarydb['tvshow'][_id] = tvshowdb

    if not nfo_exists:
        filetools.write(filetools.join(TVSHOWS_PATH, tvshow_item.nfo_path), head_nfo)

    if not episodelist:
        # The episode list is empty
        return 0, 0, -1, path

    # Save the episodes
    logger.debug()
    inserted, overwritten, failed = save_episodes(tvshow_item, episodelist, extra_info, item.host, local_files, silent=silent)
    videolibrarydb.close()
    if config.is_xbmc() and config.get_setting("videolibrary_kodi") and not silent:# and inserted:
        from platformcode.dbconverter import add_video
        add_video(tvshow_item)


    return inserted, overwritten, failed, path


def save_episodes(item, episodelist, extra_info, host, local_files, silent=False):
    logger.debug()

    def save_episode(item, episodes, e):
        inserted = 0
        overwritten = 0
        failed = 0
        episode = None
        season_episode = None


        if e.contentSeason and e.contentEpisodeNumber:
            season_episode = '{}x{:02d}'.format(e.contentSeason, e.contentEpisodeNumber)
            strm_path = filetools.join(item.base_name, "{}.strm".format(season_episode))

            if item.infoLabels.get('imdb_id'): e.infoLabels['imdb_id'] = item.infoLabels['imdb_id']
            if item.infoLabels.get('tmdb_id'): e.infoLabels['tmdb_id'] = item.infoLabels['tmdb_id']
            if item.infoLabels.get('tvdb_id'): e.infoLabels['tvdb_id'] = item.infoLabels['tvdb_id']

            tmdb.set_infoLabels_item(e)
            if not e.infoLabels.get('playcount'): e.infoLabels['playcount'] = 0
            head_nfo = scraper.get_nfo(e)

            episode_item = Item(action='findvideos',
                                channel='videolibrary',
                                strm_path=strm_path,
                                contentSeason = e.contentSeason,
                                contentEpisodeNumber = e.contentEpisodeNumber,
                                contentType = e.contentType,
                                infoLabels = e.infoLabels,
                                head_nfo = head_nfo,
                                videolibrary_id = item.videolibrary_id,
                                thumbnail = e.infoLabels.get('poster_path') if e.infoLabels.get('poster_path') else item.thumbnail,
                                fanart = e.infoLabels.get('poster_path') if e.infoLabels.get('poster_path') else item.fanart,
                                title = e.infoLabels['title'])

            episode = episodes.get(season_episode, {})

            try:
                if not episode:
                    inserted += 1
                    episode['item'] = episode_item

                # else:
                epchannels = episode.get('channels',{})

                if e.url.startswith(host):
                    remove_host(e)

                e.contentTitle = e.infoLabels['title']
                contentType = e.contentType
                e.infoLabels = {}
                e.contentType = contentType

                if e.channel in epchannels and e.channel != 'download':
                    channels_url = [u.url for u in epchannels[e.channel]]
                    if e.url not in channels_url:
                        epchannels[e.channel].append(e)
                        overwritten += 1
                    else:
                        del epchannels[e.channel][channels_url.index(e.url)]
                        epchannels[e.channel].append(e)
                        overwritten += 1
                else:
                    epchannels[e.channel] = [e]
                    overwritten += 1

                # add local files
                if list(local_files.values()):
                    epchannels['local'] = {}
                    if season_episode in list(local_files.get('db',{}).keys()):
                        epchannels['local']['db'] = local_files['db'][season_episode]
                    if season_episode in list(local_files.get('internal',{}).keys()):
                        epchannels['local']['internal'] = local_files['db'][season_episode]
                    if season_episode in list(local_files.get('connected',{}).keys()):
                        epchannels['local']['connected'] = local_files['connected'][season_episode]
                    logger.debug('LOCALS', epchannels)
                    # if season_episode in list(local_files.get('external',{}).keys()):
                    #     epchannels['external'] = local_files['db'][season_episode]

                # Delete the local key if local files no longer exist
                elif 'local' in epchannels:
                    del epchannels['local']

                episode['channels'] = epchannels

            except:
                logger.error(traceback.format_exc())
                failed += 1

            # add strm_file if episode is not present in db or inside videolibrary path
            # if not filetools.exists(filetools.join(TVSHOWS_PATH, strm_path)):
            if season_episode not in local_files.get('db',{}).keys():
                logger.debug("Creating .strm: " + strm_path)
                item_strm = Item(channel='videolibrary', action='play_from_library', strm_path=strm_path, contentType='episode', videolibrary_id=episode_item.videolibrary_id, contentSeason = episode_item.contentSeason, contentEpisodeNumber = episode_item.contentEpisodeNumber,)
                filetools.write(filetools.join(TVSHOWS_PATH, strm_path), '{}?{}'.format(addon_name, item_strm.tourl()))

            # update db if episode added
            # if failed == 0 and config.get_setting('kod_scraper'):
            #     add_video(episode_item)

        return item, episode, season_episode, e.contentLanguage, inserted, overwritten, failed

    def save_season(item, s, w):
        tmdb_info = tmdb.Tmdb(id_Tmdb = item.infoLabels['tmdb_id'], search_type='tv')
        seasoninfo = tmdb.get_season_dic(tmdb_info.get_season(s))
        infoLabels = {}

        if seasoninfo.get('season_posters'): infoLabels['posters'] = seasoninfo.get('season_posters') + extra_info['poster'].get(str(s), [])
        if seasoninfo.get('season_fanarts'): infoLabels['fanarts'] = seasoninfo.get('season_fanarts') + extra_info['fanart'].get(str(s), [])
        if seasoninfo.get('season_trailer'): infoLabels['trailer'] = seasoninfo.get('season_trailer')
        infoLabels['landscapes'] = extra_info['landscape'].get(str(s), [])
        infoLabels['banners'] = extra_info['banner'].get(str(s), [])
        infoLabels['clearlogos'] = item.infoLabels.get('clearlogos', [])
        infoLabels['cleararts'] = item.infoLabels.get('cleararts', [])
        infoLabels['playcount'] = w

        season_item = Item(action="get_episodes",
                           channel='videolibrary',
                           title=seasoninfo.get('season_title'),
                           thumbnail = seasoninfo.get('season_poster') if seasoninfo.get('season_poster') else item.thumbnail,
                           fanart = item.fanart,
                           plot = seasoninfo.get('season_plot') if seasoninfo.get('season_plot') else item.infoLabels.get('plot'),
                           contentType = 'season',
                           infoLabels = infoLabels,
                           contentSeason = s,
                           videolibrary_id = item.videolibrary_id)

        if infoLabels['clearlogos']: season_item.clearlogo = infoLabels['clearlogos'][0]
        if infoLabels['cleararts']: season_item.clearart = infoLabels['cleararts'][0]
        if infoLabels['landscapes']: season_item.landscape = infoLabels['landscapes'][0]
        if infoLabels['banners']: season_item.banner = infoLabels['banners'][0]

        return s, season_item

    def watched_season(s):
        w = 0
        s_ep = [e['item'] for e in episodes.values() if e['item'].contentSeason == s]
        w_ep = [e for e in s_ep if e.infoLabels.get('playcount') > 0]
        if len(s_ep) == len(w_ep): w = 1
        return s, w


    # No episode list, nothing to save
    if not len(episodelist):
        logger.debug("There is no episode list, we go out without creating strm")
        return 0, 0, 0

    # Silent is to show no progress (for service)
    if not silent:
        # progress dialog
        p_dialog = platformtools.dialog_progress_bg(config.get_localized_string(60064) ,'')

    inserted = 0
    overwritten = 0
    failed = 0
    current_seasons = []
    seasons = videolibrarydb['season'].get(item.videolibrary_id, {})
    episodes = videolibrarydb['episode'].get(item.videolibrary_id, {})
    videolibrarydb.close()

    try: t = float(100) / len(episodelist)
    except: t = 0

    i = 0
    # save episodes Thread
    with futures.ThreadPoolExecutor() as executor:
        itlist = [executor.submit(save_episode, item, episodes, e) for e in episodelist]
        for res in futures.as_completed(itlist):
            if res.result():
                item, episode, season_episode, lang, I, O, F = res.result()
                inserted += I
                overwritten += O
                failed += F
                if episode:
                    episodes[season_episode] = episode
                    e = episode['item']
                    if not e.contentSeason in current_seasons: current_seasons.append(e.contentSeason)
                    if not lang: lang = item.contentLanguage if item.contentLanguage else 'ITA'
                    if not lang in item.lang_list: item.lang_list.append(lang)
                    if not silent:
                        i += 1
                        p_dialog.update(int(math.ceil(i * t)), message=e.title)

    # support.dbg()
    # for e in episodelist:
    #     item, episode, season_episode, lang, I, O, F = save_episode(item, episodes, e)
    #     inserted += I
    #     overwritten += O
    #     failed += F
    #     if episode:
    #         episodes[season_episode] = episode
    #         e = episode['item']
    #         if not e.contentSeason in current_seasons: current_seasons.append(e.contentSeason)
    #         if not lang: lang = item.contentLanguage if item.contentLanguage else 'ITA'
    #         if not lang in item.lang_list: item.lang_list.append(lang)
    #         if not silent:
    #             i += 1
    #             p_dialog.update(int(math.ceil(i * t)), message=e.title)

    # set seasons as watched
    add_seasons = {}
    with futures.ThreadPoolExecutor() as executor:
        itlist = [executor.submit(watched_season, s) for s in current_seasons]
        for res in futures.as_completed(itlist):
            add_seasons[res.result()[0]] = res.result()[1]

    # save seasons
    with futures.ThreadPoolExecutor() as executor:
        itlist = [executor.submit(save_season, item, s, w) for s, w in add_seasons.items()]
        for res in futures.as_completed(itlist):
            if res.result():
                s, season_item = res.result()
                seasons[s] = season_item

                # Add to Kodi DB if Kod is set to add information
                # if config.get_setting('kod_scraper'):
                #     add_video(season_item)


    if not silent:
        # update tvshow info if forced
        if len(item.lang_list) > 1:
            item.prefered_lang = item.lang_list[platformtools.dialog_select(config.get_localized_string(70246), item.lang_list)]
        else:
            item.prefered_lang = item.lang_list[0]

        tvshowdb = videolibrarydb['tvshow'][item.videolibrary_id]
        tvshowdb['item'] = item
        videolibrarydb['tvshow'][item.videolibrary_id] = tvshowdb
        videolibrarydb.close()

    videolibrarydb['episode'][item.videolibrary_id] = episodes
    videolibrarydb['season'][item.videolibrary_id] = seasons

    videolibrarydb.close()
    if not silent:
        p_dialog.close()

    return inserted, overwritten, failed


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
    from platformcode.launcher import set_search_temp; set_search_temp(item)

    # To disambiguate titles, TMDB is caused to ask for the really desired title
    # The user can select the title among those offered on the first screen
    # or you can cancel and enter a new title on the second screen
    # If you do it in "Enter another name", TMDB will automatically search for the new title
    # If you do it in "Complete Information", it partially changes to the new title, but does not search TMDB. We have to do it
    # If the second screen is canceled, the variable "scraper_return" will be False. The user does not want to continue

    item = generictools.update_title(item) # We call the method that updates the title with tmdb.find_and_set_infoLabels

    if item:
        new_item = item.clone(action="findvideos")
        inserted, overwritten, failed, path = save_movie(new_item)

        if failed == 0:
            platformtools.dialog_notification(config.get_localized_string(30131), config.get_localized_string(30135) % new_item.contentTitle)  # 'has been added to the video library'
        else:
            filetools.rmdirtree(path)
            platformtools.dialog_ok(config.get_localized_string(30131), config.get_localized_string(60066) % new_item.contentTitle)  # "ERROR, the movie has NOT been added to the video library")
            movies = videolibrarydb['movie']
            _id = get_id(item)
            if _id in list(movies.keys()):
                del movies[_id]
                videolibrarydb['movie'] = movies
            videolibrarydb.close()


def add_tvshow(item, channel=None):
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
    from platformcode.launcher import set_search_temp; set_search_temp(item)

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
        it = item.clone()
        itemlist = getattr(channel, it.action)(it)
        item.host = channel.host
        if itemlist:
            from platformcode.autorenumber import start, check
            if not check(item):
                action = item.action
                item.setrenumber = True
                start(item)
                item.setrenumber = False
                item.action = action
                if not item.exit:
                    return add_tvshow(item, channel)
                itemlist = getattr(channel, item.action)(item)
            else:
                itemlist = getattr(channel, item.action)(item)

    global magnet_caching
    magnet_caching = False

    inserted, overwritten, failed, path = save_tvshow(item, itemlist)

    if not path:
        pass

    elif not inserted and not overwritten and not failed:
        filetools.rmdirtree(path)
        platformtools.dialog_ok(config.get_localized_string(30131), config.get_localized_string(60067) % item.show)
        logger.error("The string %s could not be added to the video library. Could not get any episode" % item.show)

    elif failed == -1:
        filetools.rmdirtree(path)
        platformtools.dialog_ok(config.get_localized_string(30131), config.get_localized_string(60068) % item.show)
        logger.error("The string %s could not be added to the video library" % item.show)

    elif failed == -2:
        filetools.rmdirtree(path)

    elif failed > 0:
        platformtools.dialog_ok(config.get_localized_string(30131), config.get_localized_string(60069) % item.show)
        logger.error("Could not add %s episodes of series %s to the video library" % (failed, item.show))

    else:
        platformtools.dialog_notification(config.get_localized_string(30131), config.get_localized_string(60070) % item.show)
        logger.debug("%s episodes of series %s have been added to the video library" % (inserted, item.show))
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


def remove_host(item):
    if PY3: import urllib.parse as urlparse  # It is very slow in PY2. In PY3 it is native
    else: import urlparse  # We use the native of PY2 which is faster
    parsed_url = urlparse.urlparse(item.url)
    item.url = urlparse.urlunparse(('', '', parsed_url.path, parsed_url.params, parsed_url.query, parsed_url.fragment))


def get_id(item):
    return item.infoLabels.get('tmdb_id')


def get_fanart_tv(item, set='', ret={}):
    def set_dict(l):
        d = {}
        for k in l:
            o = d.get(k['season'], [])
            o.append(k['url'])
            d[k['season']] = o
        return d

    _id = item.infoLabels.get('tvdb_id', item.infoLabels.get('tmdb_id'))

    if _id:
        _type = item.contentType.replace('show','').replace('movie','movies')
        host = 'http://webservice.fanart.tv/v3/{}/{}?api_key=cab16e262d72fea6a6843d679aa10300'
        url = host.format(_type, _id)
        res = httptools.downloadpage(url).json
        if _type == 'tv':
            ret['clearlogo'] = [k.get('url') for k in res.get('hdtvlogo', [])] + [k.get('url') for k in res.get('tvlogo', [])]
            ret['clearart'] = [k.get('url') for k in res.get('hdclearart', [])] + [k.get('url') for k in res.get('hdclearart', [])]
            ret['fanart'] = set_dict(res.get('showbackground', []))
            ret['poster'] = set_dict(res.get('seasonposter', []))
            ret['poster']['all'] = [k.get('url') for k in res.get('tvposter', [])]
            ret['landscape'] = set_dict(res.get('seasonthumb', []))
            ret['landscape']['all'] = [k.get('url') for k in res.get('tvthumb', [])]
            ret['banner'] = set_dict(res.get('seasonbanner', []))
            ret['banner']['all'] = [k.get('url') for k in res.get('tvbanner', [])]

        elif _type == 'movies':
            ret[set + 'clearlogo'] = [k.get('url') for k in res.get('hdmovielogo', [])] + [k.get('url') for k in res.get('movielogo', [])]
            ret[set + 'poster'] = [k.get('url') for k in res.get('movieposter', [])]
            ret[set + 'fanart'] = [k.get('url') for k in res.get('moviebackground', [])]
            ret[set + 'clearart'] = [k.get('url') for k in res.get('hdmovieclearart', [])] + [k.get('url') for k in res.get('movieclearart', [])]
            ret[set + 'landscape'] = [k.get('url') for k in res.get('moviethumb', [])]
            ret[set + 'banner'] = [k.get('url') for k in res.get('moviebanner', [])]
            ret[set + 'disc'] = [k.get('url') for k in res.get('moviedisc', [])]
            if item.infoLabels.get('setid'):
                it = item.clone(infoLabels = {'tmdb_id':item.infoLabels['setid']})
                get_fanart_tv(it, 'set', ret)

    return ret


def get_local_files(path, item):
    from platformcode.xbmc_videolibrary import execute_sql_kodi
    # check if movie or season already exist in path or db
    excluded_extensions = subtitle_extensions + image_extensions + library_extension

    local_files = {}
    if item.contentType == 'movie':
        # search on path:
        internal = [f for f in filetools.listdir(path) if not (f.endswith('nfo') or f.endswith('strm') or f.endswith('json'))]
        if internal:
            local_files['internal'] = internal

        # search on db:
        sql = 'SELECT c22, uniqueid_value FROM movie_view WHERE uniqueid_type != "kod"'
        n, records = execute_sql_kodi(sql)
        if records:
            local_files['db']= [r[0] for r in records if r[1] in item.infoLabels['code'] and not r[0].endswith('strm')]

    else:
        # search on path:
        internal = {scrapertools.get_season_and_episode(f):f for f in filetools.listdir(path) if os.path.splitext(f)[1] not in excluded_extensions}
        if internal:
            local_files['internal'] = internal

        # search on db:
        sql = 'SELECT idShow, uniqueid_value FROM tvshow_view WHERE uniqueid_type != "kod"'
        n, records = execute_sql_kodi(sql)
        if records:
            for r in records:
                if r[1] in item.infoLabels['code']:
                    sql = 'SELECT strPath, strFilename From episode_view WHERE idShow = {}'.format(r[0])
                    n, ep_records = execute_sql_kodi(sql)
                    if ep_records:
                        local_files['db'] = {scrapertools.get_season_and_episode(e[1]):e[0]+e[1] for e in ep_records if not e[1].endswith('strm')}
                        break

        # search on custom path
        item = select_local_path(item)
        if item.local_episodes_path:
            connected = {scrapertools.get_season_and_episode(f):filetools.join(item.local_episodes_path, f) for f in filetools.listdir(item.local_episodes_path) if os.path.splitext(f)[1] not in excluded_extensions}
            if connected:
                local_files['connected'] = connected

    return item, local_files


def select_local_path(item):
    if not item.local_episodes_path and config.get_setting('local_episodes'):
        if platformtools.dialog_yesno(config.get_localized_string(30131), config.get_localized_string(80044) % item.title):
            local_episodes_path = platformtools.dialog_browse(0, config.get_localized_string(80046))
            if local_episodes_path:
                item.local_episodes_path = local_episodes_path
    return item


def update_renumber_options(item):
    from core import jsontools

    filename = filetools.join(config.get_data_path(), "settings_channels", item.channel + '_data.json')
    if filetools.isfile(filename):
        json_file = jsontools.load(filetools.read(filename))
        json = json_file.get(RENUMBER,{}).get(item.fulltitle,{})
    if json:
        logger.debug('UPDATED=\n' + item.fulltitle)
        item.renumber = json
    return item


def add_renumber_options(item):
    from core import jsontools
    ret = None
    filename = filetools.join(config.get_data_path(), "settings_channels", item.channel + '_data.json')
    json_file = jsontools.load(filetools.read(filename))
    if item.renumber and not json_file.get(RENUMBER,{}).get(item.fulltitle):
        check_renumber_options(item)
    if RENUMBER in json_file:
        json = json_file[RENUMBER]
        if item.fulltitle in json:
            ret = json[item.fulltitle]
    return ret


def check_renumber_options(item):
    from platformcode.autorenumber import load, write
    if item.renumber:
        json = load(item)
        if not json or item.fulltitle not in json:
            json[item.fulltitle] = item.renumber
            write(item, json)


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
    it = None

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


def set_base_name(item, _id):
    # set base_name for videolibrary
    logger.debug()
    if item.contentType == 'movie':
        if config.get_setting("original_title_folder", "videolibrary") and item.infoLabels['originaltitle']:
            base_name = item.infoLabels['originaltitle']
        else:
            base_name = item.contentTitle
    else:
        if config.get_setting("original_title_folder", "videolibrary") and item.infoLabels['originaltitle']:
            base_name = item.infoLabels['originaltitle']
        elif item.infoLabels['tvshowtitle']:
            base_name = item.infoLabels['tvshowtitle']
        elif item.infoLabels['title']:
            base_name = item.infoLabels['title']
        else:
            base_name = item.contentSerieName

    if not PY3:
        base_name = unicode(filetools.validate_path(base_name.replace('/', '-')), "utf8").encode("utf8")
    else:
        base_name = filetools.validate_path(base_name.replace('/', '-'))

    if config.get_setting("lowerize_title", "videolibrary"):
        base_name = base_name.lower()

    return '{} [{}]'.format(base_name, _id)
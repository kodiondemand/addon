# -*- coding: utf-8 -*-

#from builtins import str
import sys
from core import httptools, support

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import xbmc, os, traceback
from time import time

from core import filetools, scrapertools, videolibrarytools
from core.support import typo, thumb, videolibrary
from core.item import Item
from platformcode import config, launcher, logger, platformtools
if PY3:
    from concurrent import futures
    import urllib.parse as urlparse
else:
    from concurrent_py2 import futures
    import urlparse

from core.videolibrarytools import videolibrarydb


def mainlist(item):
    logger.debug()

    itemlist = [Item(channel=item.channel, action="list_movies", title=config.get_localized_string(60509),
                     category=config.get_localized_string(70270), thumbnail=thumb("videolibrary_movie")),
                Item(channel=item.channel, action="list_tvshows",title=config.get_localized_string(60600),
                     category=config.get_localized_string(70271), thumbnail=thumb("videolibrary_tvshow"),
                     context=[{"channel":"videolibrary", "action":"update_videolibrary", "title":config.get_localized_string(70269)}]),
                Item(channel='shortcuts', action="SettingOnPosition", title=typo(config.get_localized_string(70287),'bold color kod'),
                     category=2, setting=1, thumbnail = thumb("setting_0"),folder=False)]
    return itemlist


def channel_config(item):
    return platformtools.show_channel_settings(channelpath=os.path.join(config.get_runtime_path(), "channels", item.channel), caption=config.get_localized_string(60598))


def list_movies(item, silent=False):
    from core import jsontools
    logger.debug()

    itemlist = []
    movies_path = []
    ids = []

    # for root, folders, files in filetools.walk(videolibrarytools.MOVIES_PATH):
    #     for f in folders:
    #         ID = scrapertools.find_single_match(f, r'\[([^\]]+)')
    #         if ID:
    #             ids.append(ID)
    #             if ID not in videolibrarydb['movie']:
    #                 ids.append(ID)
    #                 movies_path += [filetools.join(root, f, f + ".nfo")]
    #                 local = False
    #                 for f in filetools.listdir(filetools.join(root, f)):
    #                     if f.split('.')[-1] not in ['nfo','json','strm']:
    #                         local= True
    #                         break

    # with futures.ThreadPoolExecutor() as executor:
    #     itlist = [executor.submit(get_results, movie_path, root, 'movie', local) for movie_path in movies_path]
    #     for res in futures.as_completed(itlist):
    #         item_movie, value = res.result()
    #         # verify the existence of the channels
    #         if item_movie.library_urls and len(item_movie.library_urls) > 0:
    #             code = scrapertools.find_single_match(item_movie.strm_path, r'\[([^\]]+)')
    #             videolibrarydb['movie'][code] = {'item':jsontools.load(item_movie.tojson())}
    movies = dict(videolibrarydb['movie'])
    videolibrarydb.close()
    for key, value in movies.items():
        # if key not in ids:
        #     del videolibrarydb['movie'][key]
        # else:
        item = value['item']
        item.context = [{'title':config.get_localized_string(70084),'channel':'videolibrary', 'action':'delete'}]
        if len(item.lang_list) > 1:
            item.context += [{"title": config.get_localized_string(70246),
                                "action": "prefered_lang",
                                "channel": "videolibrary"}]
        itemlist.append(item)

    if silent == False: return sorted(itemlist, key=lambda it: it.title.lower())
    else: return


def list_tvshows(item):
    logger.debug()
    itemlist = []
    tvshows_path = []
    ids = []
    # lista = []

    root = videolibrarytools.TVSHOWS_PATH
    # start = time()
    # for root, folders, files in filetools.walk(videolibrarytools.TVSHOWS_PATH):
    #     for f in folders:
    #         ID = scrapertools.find_single_match(f, r'\[([^\]]+)')
    #         if ID:
    #             ids.append(ID)
    #             if ID not in videolibrarydb['movie']:
    #                 ids.append(ID)
    #                 tvshows_path += [filetools.join(root, f, f + ".nfo")]
    #                 local = False
    #                 for f in filetools.listdir(filetools.join(root, f)):
    #                     if f.split('.')[-1] not in ['nfo','json','strm']:
    #                         local= True
    #                         break
    # with futures.ThreadPoolExecutor() as executor:
    #     itlist = [executor.submit(get_results, tvshow_path, root, 'tvshow', local) for tvshow_path in tvshows_path]
    #     itlist = [executor.submit(get_results, filetools.join(root, folder, "tvshow.nfo"), root, 'tvshow') for folder in filetools.listdir(root)]
    #     for res in futures.as_completed(itlist):
    #         item_tvshow, value = res.result()
    #         # verify the existence of the channels
    #         if item_tvshow.library_urls and len(item_tvshow.library_urls) > 0:
    #             code = scrapertools.find_single_match(item_tvshow.strm_path, r'\[([^\]]+)')
    #             db['tvshow'][code] = {'item':jsontools.load(item_tvshow.tojson())}
    #             # itemlist += [item_tvshow]
    #             lista += [{'title':item_tvshow.contentTitle,'thumbnail':item_tvshow.thumbnail,'fanart':item_tvshow.fanart, 'active': value, 'nfo':item_tvshow.nfo}]
    # logger.debug('load list',time() - start)


    series = dict(videolibrarydb['tvshow'])
    videolibrarydb.close()

    for key, value in series.items():

        item = value['item']
        item.contentType = 'tvshow'

        item.context = [{'title':config.get_localized_string(70085),'channel':'videolibrary', 'action':'delete'}]

        if len(item.lang_list) > 1:
            item.context += [{"title": config.get_localized_string(70246),
                              "action": "prefered_lang",
                              "channel": "videolibrary"}]
        if len(value['channels'].keys()) > 1:
            item.context += [{"title": config.get_localized_string(70837),
                              "action": "disable_channels",
                              "channel": "videolibrary"}]
        watched = item.infoLabels.get("playcount", 0)
        if watched > 0:
            title = config.get_localized_string(60020)
            value = 0
        else:
            title = config.get_localized_string(60021)
            value = 1

        item.context += [{"title": title,
                          "action": "mark_content_as_watched",
                          "channel": "videolibrary",
                          "playcount": value,
                          "videolibrary_id": item.videolibrary_id}]
        if not item.active:
            item.title = '{} {}'.format(item.title, support.typo('','bullet bold'))
            title = config.get_localized_string(60023)
        else:
            title = config.get_localized_string(60022)
        item.context += [{"title": title,
                          "action": "set_active",
                          "channel": "videolibrary",
                          "playcount": value,
                          "videolibrary_id": item.videolibrary_id}]
        item.context += [{"title": 'Poster',
                                 "action": "change_poster",
                                 "channel": "videolibrary",
                                 "playcount": value,
                                 "videolibrary_id": item.videolibrary_id}]
        item.context += [{"title": 'fanart',
                                 "action": "change_fanart",
                                 "channel": "videolibrary",
                                 "playcount": value,
                                 "videolibrary_id": item.videolibrary_id}]

        itemlist.append(item)

    if itemlist:
        itemlist = sorted(itemlist, key=lambda it: it.title.lower())

        itemlist += [Item(channel=item.channel, action="update_videolibrary", thumbnail=item.thumbnail,
                          title=typo(config.get_localized_string(70269), 'bold color kod'), folder=False)]
    return itemlist


def get_results(nfo_path, root, Type, local=False):
    value = 0

    if filetools.exists(nfo_path):
        head_nfo, item = videolibrarytools.read_nfo(nfo_path)

        # If you have not read the .nfo well, we will proceed to the next
        if not item:
            logger.error('.nfo erroneous in ' + str(nfo_path))
            return Item(), 0

        if len(item.library_urls) > 1: multichannel = True
        else: multichannel = False

        # continue loading the elements of the video library
        if Type == 'movie':
            folder = "folder_movies"
            item.path = filetools.split(nfo_path)[0]
            item.nfo = nfo_path
            sep = '/' if '/' in nfo_path else '\\'
            item.extra = filetools.join(config.get_setting("videolibrarypath"), config.get_setting(folder), item.path.split(sep)[-1])
            strm_path = item.strm_path.replace("\\", "/").rstrip("/")
            if not item.thumbnail: item.thumbnail = item.infoLabels['thumbnail']
            if '/' in item.path: item.strm_path = strm_path
            # If strm has been removed from kodi library, don't show it
            if not filetools.exists(filetools.join(item.path, filetools.basename(strm_path))) and not local: return Item(), 0

            # Contextual menu: Mark as seen / not seen
            visto = item.library_playcounts.get(strm_path.strip('/').split('/')[0], 0)
            item.infoLabels["playcount"] = visto
            if visto > 0:
                seen_text = config.get_localized_string(60016)
                counter = 0
            else:
                seen_text = config.get_localized_string(60017)
                counter = 1

            # Context menu: Delete series / channel
            channels_num = len(item.library_urls)
            if "downloads" in item.library_urls: channels_num -= 1
            if channels_num > 1: delete_text = config.get_localized_string(60018)
            else: delete_text = config.get_localized_string(60019)

            item.context = [{"title": seen_text, "action": "mark_content_as_watched", "channel": "videolibrary",  "playcount": counter},
                            {"title": delete_text, "action": "delete", "channel": "videolibrary", "multichannel": multichannel}]
        else:
            folder = "folder_tvshows"
            try:
                item.title = item.contentTitle
                item.path = filetools.split(nfo_path)[0]
                item.nfo = nfo_path
                sep = '/' if '/' in nfo_path else '\\'
                item.extra = filetools.join(config.get_setting("videolibrarypath"), config.get_setting(folder), item.path.split(sep)[-1])
                # Contextual menu: Mark as seen / not seen
                visto = item.library_playcounts.get(item.contentTitle, 0)
                item.infoLabels["playcount"] = visto
                logger.debug('item\n' + str(item))
                if visto > 0:
                    seen_text = config.get_localized_string(60020)
                    counter = 0
                else:
                    seen_text = config.get_localized_string(60021)
                    counter = 1

            except:
                logger.error('Not find: ' + str(nfo_path))
                logger.error(traceback.format_exc())
                return Item(), 0

            # Context menu: Automatically search for new episodes or not
            if item.active and int(item.active) > 0:
                update_text = config.get_localized_string(60022)
                value = 0
            else:
                update_text = config.get_localized_string(60023)
                value = 1
                item.title += " [B]" + u"\u2022" + "[/B]"

            # Context menu: Delete series / channel
            channels_num = len(item.library_urls)
            if "downloads" in item.library_urls: channels_num -= 1
            if channels_num > 1: delete_text = config.get_localized_string(60024)
            else: delete_text = config.get_localized_string(60025)

            item.context = [{"title": seen_text, "action": "mark_content_as_watched", "channel": "videolibrary", "playcount": counter},
                            {"title": update_text, "action": "mark_tvshow_as_updatable", "channel": "videolibrary", "active": value},
                            {"title": delete_text, "action": "delete", "channel": "videolibrary", "multichannel": multichannel},
                            {"title": config.get_localized_string(70269), "action": "update_tvshow", "channel": "videolibrary"}]
            if item.local_episodes_path == "": item.context.append({"title": config.get_localized_string(80048), "action": "add_local_episodes", "channel": "videolibrary"})
            else: item.context.append({"title": config.get_localized_string(80049), "action": "remove_local_episodes", "channel": "videolibrary"})
    else: item = Item()
    return item, value


def configure_update_videolibrary(item):
    import xbmcgui
    # Load list of options (active user channels that allow global search)
    lista = []
    ids = []
    preselect = []

    for i, item_tvshow in enumerate(item.lista):
        it = xbmcgui.ListItem(item_tvshow["title"], '')
        it.setArt({'thumb': item_tvshow["thumbnail"], 'fanart': item_tvshow["fanart"]})
        lista.append(it)
        ids.append(Item(nfo=item_tvshow['nfo']))
        if item_tvshow['active']<=0:
            preselect.append(i)

    # Select Dialog
    ret = platformtools.dialog_multiselect(config.get_localized_string(60601), lista, preselect=preselect, useDetails=True)
    if ret is None:
        return False  # order cancel
    selection = [ids[i] for i in ret]

    for tvshow in ids:
        if tvshow not in selection:
            tvshow.active = 0
        elif tvshow in selection:
            tvshow.active = 1
        mark_tvshow_as_updatable(tvshow, silent=True)

    platformtools.itemlist_refresh()

    return True


def get_seasons(item):
    logger.debug()

    itemlist = []
    dict_temp = {}


    if config.get_setting("no_pile_on_seasons", "videolibrary") == 2:  # Ever
        return get_episodes(item)

    if config.get_setting("no_pile_on_seasons", "videolibrary") == 1 and len(dict_temp) == 1:  # Only if there is a season
        item.from_library = True
        return get_episodes(item)
    else:
        from core import tmdb
        seasons = videolibrarydb['season'][item.videolibrary_id]
        videolibrarydb.close()
        # We create one item for each season
        for season in seasons.values():
            new_item = season
            new_item.contentType = 'season'

            #Contextual menu: Mark the season as viewed or not
            watched = new_item.infoLabels.get("playcount", 0)
            if watched > 0:
                title = config.get_localized_string(60028)
                value = 0
            else:
                title = config.get_localized_string(60029)
                value = 1

            new_item.context = [{"title": title,
                                 "action": "mark_content_as_watched",
                                 "channel": "videolibrary",
                                 "playcount": value,
                                 "videolibrary_id": item.videolibrary_id}]

            # logger.debug("new_item:\n" + new_item.tostring('\n'))
            itemlist.append(new_item)

        if len(itemlist) > 1:
            itemlist = sorted(itemlist, key=lambda it: int(it.contentSeason))
        else:
            return get_episodes(itemlist[0])

        if config.get_setting("show_all_seasons", "videolibrary"):
            new_item = item.clone(action="get_episodes", title=config.get_localized_string(60030), all=True)
            new_item.infoLabels["playcount"] = 0
            itemlist.insert(0, new_item)

        add_download_items(item, itemlist)
    return itemlist


def get_episodes(item):
    logger.debug()
    itemlist = []

    episodes = videolibrarydb['episode'][item.videolibrary_id]
    videolibrarydb.close()

    for title, ep in episodes.items():
        it = ep['item']

        if it.contentSeason == item.contentSeason or item.all:
            if config.get_setting("no_pile_on_seasons", "videolibrary") == 2 or item.all:
                it.title = '{}x{}'.format(it.contentSeason, it.title)
            it = get_host(it)
            it.from_library = item.from_library
            watched = it.infoLabels.get("playcount", 0)
            if watched > 0:
                title = config.get_localized_string(60032)
                value = 0
            else:
                title = config.get_localized_string(60033)
                value = 1

            it.context = [{"title": title,
                           "action": "mark_content_as_watched",
                           "channel": "videolibrary",
                           "playcount": value,
                           'allep': True,
                           "videolibrary_id": item.videolibrary_id}]
            itemlist.append(it)

    itemlist = sorted(itemlist, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))
    add_download_items(item, itemlist)
    return itemlist


def findvideos(item):
    from core import autoplay
    from platformcode import platformtools

    logger.debug()
    videolibrarytools.check_renumber_options(item)
    itemlist = []

    if not item.strm_path:
        logger.debug("Unable to search for videos due to lack of parameters")
        return []
    if not item.videolibrary_id: item.videolibrary_id = scrapertools.find_single_match(item.strm_path , r'\[([^\]]+)')
    if item.contentType == 'movie':
        videolibrary_items = videolibrarydb['movie'][item.videolibrary_id]['channels']
        prefered_lang = videolibrarydb['movie'].get(item.videolibrary_id, {}).get('item', Item()).prefered_lang
        disabled = videolibrarydb['movie'].get(item.videolibrary_id, {}).get('item', Item()).disabled
    else:
        ep = '{:d}x{:02d}'.format(item.contentSeason, item.contentEpisodeNumber)
        videolibrary_items = videolibrarydb['episode'][item.videolibrary_id][ep]['channels']
        prefered_lang = videolibrarydb['tvshow'].get(item.videolibrary_id, {}).get('item', Item()).prefered_lang
        disabled = videolibrarydb['tvshow'].get(item.videolibrary_id, {}).get('item', Item()).disabled
    videolibrarydb.close()
    if 'local' in videolibrary_items:
        try:
            item.channel = 'local'
            item.url = filetools.join(videolibrarytools.TVSHOWS_PATH, videolibrary_items['local'])
            return play(item)
        except: pass
    else:
        if prefered_lang:
            for key, values in videolibrary_items.items():
                if len(values) > 1:
                    allowed = []
                    for v in values:
                        v.contentTitle = item.title
                        if v.contentLanguage == prefered_lang:
                            allowed.append(v)
                    if allowed:
                        videolibrary_items[key] = allowed
                    else:
                        videolibrary_items[key] = values
                else:
                    videolibrary_items[key] = values

        with futures.ThreadPoolExecutor() as executor:
            itlist = [executor.submit(servers, ch, value) for ch, value in videolibrary_items.items() if ch not in disabled]
            for res in futures.as_completed(itlist):
                itemlist += res.result()

        if len(itlist) > 1:
            for it in itemlist:
                it.title = '[{}] {}'.format(it.ch_name, it.title)

        if autoplay.play_multi_channel(item, itemlist):  # hideserver
            return []

    itemlist.sort(key=lambda it: (videolibrarytools.quality_order.index(it.quality.lower()) if it.quality and it.quality.lower() in videolibrarytools.quality_order else 999, it.server))
    add_download_items(item, itemlist)

    return itemlist


def servers(ch, items):
    serverlist = []
    from core import channeltools
    ch_params = channeltools.get_channel_parameters(ch)
    ch_name = ch_params.get('title', '')

    if ch_params.get('active', False):

        if os.path.isfile(os.path.join(config.get_runtime_path(), 'channels', ch + ".py")): CHANNELS = 'channels'
        else: CHANNELS = 'specials'
        try: channel = __import__('%s.%s' % (CHANNELS, ch), None, None, ['%s.%s' % (CHANNELS, ch)])
        except ImportError: exec("import " + CHANNELS + "." + ch + " as channel")
        with futures.ThreadPoolExecutor() as executor:
            itlist = [executor.submit(channel_servers, it, channel, ch_name) for it in items]
            for res in futures.as_completed(itlist):
                serverlist += res.result()
    return serverlist

def channel_servers(it, channel, ch_name):
    serverlist = []
    it.contentChannel = 'videolibrary'
    it = get_host(it, channel)
    for item in getattr(channel, it.action)(it):
        if item.server and item.channel:
            item.ch_name = ch_name
            serverlist.append(item)
    return serverlist


def play(item):
    logger.debug()

    itemlist = []
    # logger.debug("item:\n" + item.tostring('\n'))

    if not item.channel == "local":
        try:
            channel = __import__('specials.%s' % item.channel, fromlist=["channels.%s" % item.channel])
        except:
            channel = __import__('channels.%s' % item.channel, fromlist=["channels.%s" % item.channel])
        if hasattr(channel, "play"):
            itemlist = getattr(channel, "play")(item)

        else:
            itemlist = [item.clone()]
    else:
        itemlist = [item]

    if not itemlist:
        return []
    # For direct links in list format
    if isinstance(itemlist[0], list):
        item.video_urls = itemlist
        itemlist = [item]

    # # This is necessary in case the channel play deletes the data
    # for v in itemlist:
    #     if isinstance(v, Item):
    #         v.nfo = item.nfo
    #         v.strm_path = item.strm_path
    #         v.infoLabels = item.infoLabels
    #         if item.contentTitle:
    #             v.title = item.contentTitle
    #         else:
    #             if item.contentType == "episode":
    #                 v.title = config.get_localized_string(60036) % item.contentEpisodeNumber
    #         v.thumbnail = item.thumbnail
    #         v.contentThumbnail = item.thumbnail
    #         v.channel = item.channel

    return itemlist


def update_videolibrary(item=''):
    logger.debug()

    # Update active series by overwriting
    # import service
    # service.check_for_update(overwrite=True)
    check_for_update(item)

    # Delete movie folders that do not contain strm file
    # for raiz, subcarpetas, ficheros in filetools.walk(videolibrarytools.MOVIES_PATH):
    #     strm = False
    #     for f in ficheros:
    #         if f.endswith(".strm"):
    #             strm = True
    #             break

    #     if ficheros and not strm:
    #         logger.debug("Deleting deleted movie folder: %s" % raiz)
    #         filetools.rmdirtree(raiz)


def check_for_update(ITEM = None):
    logger.debug("Update Series...")

    import datetime
    p_dialog = None
    update_when_finished = False
    now = datetime.date.today()

    try:
        if config.get_setting("update", "videolibrary") != 0:
            config.set_setting("updatelibrary_last_check", now.strftime('%Y-%m-%d'), "videolibrary")

            heading = config.get_localized_string(60389)
            p_dialog = platformtools.dialog_progress_bg(config.get_localized_string(20000), config.get_localized_string(60037))
            p_dialog.update(0, '')
            show_list = []

            if ITEM:
                show = videolibrarydb['tvshow'][ITEM.videolibrary_id]
                videolibrarydb.close()
                for s in show['channels'].values():
                    show_list += s
            else:
                shows = dict(videolibrarydb['tvshow']).values()
                videolibrarydb.close()

                for show in shows:
                    if show['item'].active:
                        for s in show['channels'].values():
                            show_list += s

            t = float(100) / len(show_list)
            i = 0
            for item in show_list:
                i += 1
                p_dialog.update(int(i * t), heading % (item.fulltitle, item.channel) )
                item = get_host(item)
                try: channel = __import__('channels.%s' % item.channel, fromlist=["channels.%s" % item.channel])
                except: channel = __import__('specials.%s' % item.channel, fromlist=["specials.%s" % item.channel])
                itemlist = getattr(channel, item.action)(item)
                videolibrarytools.save_tvshow(item, itemlist, silent=True)
            p_dialog.close()
    except:
        p_dialog.close()
        logger.error(traceback.format_exc())

    if ITEM:
        update_when_finished = set_active_tvshow(show)
    else:
        for show in shows:
            update_when_finished = set_active_tvshow(show)

    if update_when_finished:
        platformtools.itemlist_refresh()



    # if config.get_setting('trakt_sync'):
    #     from core import trakt_tools
    #     trakt_tools.update_all()

def set_active_tvshow(show):
    update_when_finished = False
    if show['item'].active:
        prefered_lang = show['item'].prefered_lang
        active = False if show['item'].infoLabels['status'].lower() == 'ended' else True
        episodes = videolibrarydb['episode'][show['item'].videolibrary_id]
        videolibrarydb.close()
        if not active:
            total_episodes = show['item'].infoLabels['number_of_episodes']
            episodes_list = []
            for episode in episodes.values():
                for ep in episode['channels'].values():
                    ep_list = [e for e in ep if e.contentLanguage == prefered_lang]
                    if ep_list: episodes_list.append(ep_list)

            if len(episodes_list) == total_episodes:
                a = False
                update_when_finished = True
                for i in range(len(episodes_list) - 1):
                    if len(episodes_list[i]) == len(episodes_list[i + 1]):
                        a = False
                        update_when_finished = True
                    else:
                        a = True
                        break
                if not a:
                    show['item'].active = a
                    videolibrarydb['tvshow'][show['item'].videolibrary_id] = show
                    videolibrarydb.close()
    return update_when_finished


def move_videolibrary(current_path, new_path, current_movies_folder, new_movies_folder, current_tvshows_folder, new_tvshows_folder):
    from distutils import dir_util

    logger.debug()

    backup_current_path = current_path
    backup_new_path = new_path

    logger.info('current_path: ' + current_path)
    logger.info('new_path: ' + new_path)
    logger.info('current_movies_folder: ' + current_movies_folder)
    logger.info('new_movies_folder: ' + new_movies_folder)
    logger.info('current_tvshows_folder: ' + current_tvshows_folder)
    logger.info('new_tvshows_folder: ' + new_tvshows_folder)

    notify = False
    progress = platformtools.dialog_progress_bg(config.get_localized_string(20000), config.get_localized_string(80011))
    xbmc.sleep(1000)
    current_path = u'' + xbmc.translatePath(current_path)
    new_path = u'' + xbmc.translatePath(new_path)
    current_movies_path = u'' + filetools.join(current_path, current_movies_folder)
    new_movies_path = u'' + filetools.join(new_path, new_movies_folder)
    current_tvshows_path = u'' + filetools.join(current_path, current_tvshows_folder)
    new_tvshows_path = u'' + filetools.join(new_path, new_tvshows_folder)

    logger.info('current_movies_path: ' + current_movies_path)
    logger.info('new_movies_path: ' + new_movies_path)
    logger.info('current_tvshows_path: ' + current_tvshows_path)
    logger.info('new_tvshows_path: ' + new_tvshows_path)

    from platformcode import xbmc_videolibrary
    movies_path, tvshows_path = xbmc_videolibrary.check_sources(new_movies_path, new_tvshows_path)
    logger.info('check_sources: ' + str(movies_path) + ', ' + str(tvshows_path))
    if movies_path or tvshows_path:
        if not movies_path:
            filetools.rmdir(new_movies_path)
        if not tvshows_path:
            filetools.rmdir(new_tvshows_path)
        config.set_setting("videolibrarypath", backup_current_path)
        config.set_setting("folder_movies", current_movies_folder)
        config.set_setting("folder_tvshows", current_tvshows_folder)
        xbmc_videolibrary.update_sources(backup_current_path, backup_new_path)
        progress.update(100)
        xbmc.sleep(1000)
        progress.close()
        platformtools.dialog_ok(config.get_localized_string(20000), config.get_localized_string(80028))
        return

    config.verify_directories_created()
    progress.update(10, config.get_localized_string(20000), config.get_localized_string(80012))
    if current_movies_path != new_movies_path:
        if filetools.listdir(current_movies_path):
            dir_util.copy_tree(current_movies_path, new_movies_path)
            notify = True
        filetools.rmdirtree(current_movies_path)
    progress.update(40)
    if current_tvshows_path != new_tvshows_path:
        if filetools.listdir(current_tvshows_path):
            dir_util.copy_tree(current_tvshows_path, new_tvshows_path)
            notify = True
        filetools.rmdirtree(current_tvshows_path)
    progress.update(70)
    if current_path != new_path and not filetools.listdir(current_path) and not "plugin.video.kod\\videolibrary" in current_path:
        filetools.rmdirtree(current_path)

    xbmc_videolibrary.update_sources(backup_new_path, backup_current_path)
    if config.is_xbmc() and config.get_setting("videolibrary_kodi"):
        xbmc_videolibrary.update_db(backup_current_path, backup_new_path, current_movies_folder, new_movies_folder, current_tvshows_folder, new_tvshows_folder, progress)
    else:
        progress.update(100)
        xbmc.sleep(1000)
        progress.close()
    if notify:
        platformtools.dialog_notification(config.get_localized_string(20000), config.get_localized_string(80014), time=5000, sound=False)


def delete_videolibrary(item):
    logger.debug()

    if not platformtools.dialog_yesno(config.get_localized_string(20000), config.get_localized_string(80037)):
        return

    p_dialog = platformtools.dialog_progress_bg(config.get_localized_string(20000), config.get_localized_string(80038))
    p_dialog.update(0)

    if config.is_xbmc() and config.get_setting("videolibrary_kodi"):
        from platformcode import xbmc_videolibrary
        xbmc_videolibrary.clean()
    p_dialog.update(10)
    filetools.rmdirtree(videolibrarytools.MOVIES_PATH)
    p_dialog.update(50)
    filetools.rmdirtree(videolibrarytools.TVSHOWS_PATH)
    p_dialog.update(90)

    config.verify_directories_created()
    p_dialog.update(100)
    xbmc.sleep(1000)
    p_dialog.close()
    platformtools.dialog_notification(config.get_localized_string(20000), config.get_localized_string(80039), time=5000, sound=False)


# context menu methods
def update_tvshow(item):
    logger.debug()
    # logger.debug("item:\n" + item.tostring('\n'))

    heading = config.get_localized_string(60037)
    p_dialog = platformtools.dialog_progress_bg(config.get_localized_string(20000), heading)
    p_dialog.update(0, heading, item.contentSerieName)

    import service
    if service.update(item.path, p_dialog, 0, 100, item, False) and config.is_xbmc() and config.get_setting("videolibrary_kodi"):
        from platformcode import xbmc_videolibrary
        xbmc_videolibrary.update(folder=filetools.basename(item.path))

    p_dialog.close()

    # check if the TV show is ended or has been canceled and ask the user to remove it from the video library update
    nfo_path = filetools.join(item.path, "tvshow.nfo")
    head_nfo, item_nfo = videolibrarytools.read_nfo(nfo_path)
    if item.active and not item_nfo.active:
        # if not platformtools.dialog_yesno(config.get_localized_string(60037).replace('...',''), config.get_localized_string(70268) % item.contentSerieName):
        item_nfo.active = 1
        filetools.write(nfo_path, head_nfo + item_nfo.tojson())

    platformtools.itemlist_refresh()


def add_local_episodes(item):
    logger.debug()

    done, local_episodes_path = videolibrarytools.config_local_episodes_path(item.path, item, silent=True)
    if done < 0:
        logger.debug("An issue has occurred while configuring local episodes")
    elif local_episodes_path:
        nfo_path = filetools.join(item.path, "tvshow.nfo")
        head_nfo, item_nfo = videolibrarytools.read_nfo(nfo_path)
        item_nfo.local_episodes_path = local_episodes_path
        if not item_nfo.active:
            item_nfo.active = 1
        filetools.write(nfo_path, head_nfo + item_nfo.tojson())

        update_tvshow(item)

        platformtools.itemlist_refresh()


def remove_local_episodes(item):
    logger.debug()

    nfo_path = filetools.join(item.path, "tvshow.nfo")
    head_nfo, item_nfo = videolibrarytools.read_nfo(nfo_path)

    for season_episode in item_nfo.local_episodes_list:
        filetools.remove(filetools.join(item.path, season_episode + '.strm'))

    item_nfo.local_episodes_list = []
    item_nfo.local_episodes_path = ''
    filetools.write(nfo_path, head_nfo + item_nfo.tojson())

    update_tvshow(item)

    platformtools.itemlist_refresh()


def verify_playcount_series(item, path):
    logger.debug()

    """
    This method reviews and repairs the PlayCount of a series that has become out of sync with the actual list of episodes in its folder. Entries for missing episodes, seasons, or series are created with the "not seen" mark. Later it is sent to verify the counters of Seasons and Series
    On return it sends status of True if updated or False if not, usually by mistake. With this status, the caller can update the status of the "verify_playcount" option in "videolibrary.py". The intention of this method is to give a pass that repairs all the errors and then deactivate it. It can be reactivated in the Alpha Video Library menu.

    """
    #logger.debug("item:\n" + item.tostring('\n'))

    # If you have never done verification, we force it
    estado = config.get_setting("verify_playcount", "videolibrary")
    if not estado or estado == False:
        estado = True                                                               # If you have never done verification, we force it
    else:
        estado = False

    if item.contentType == 'movie':                                                 # This is only for Series
        return (item, False)
    if filetools.exists(path):
        nfo_path = filetools.join(path, "tvshow.nfo")
        head_nfo, it = videolibrarytools.read_nfo(nfo_path)                         # We get the .nfo of the Series
        if not hasattr(it, 'library_playcounts') or not it.library_playcounts:      # If the .nfo does not have library_playcounts we will create it for you
            logger.error('** It does not have PlayCount')
            it.library_playcounts = {}

        # We get the archives of the episodes
        raiz, carpetas_series, ficheros = next(filetools.walk(path))
        # Create an item in the list for each strm found
        estado_update = False
        for i in ficheros:
            if i.endswith('.strm'):
                season_episode = scrapertools.get_season_and_episode(i)
                if not season_episode:
                    # The file does not include the season and episode number
                    continue
                season, episode = season_episode.split("x")
                if season_episode not in it.library_playcounts:                     # The episode is not included
                    it.library_playcounts.update({season_episode: 0})               # update the .nfo playCount
                    estado_update = True                                            # We mark that we have updated something

                if 'season %s' % season not in it.library_playcounts:               # Season is not included
                    it.library_playcounts.update({'season %s' % season: 0})         # update the .nfo playCount
                    estado_update = True                                            # We mark that we have updated something

                if it.contentSerieName not in it.library_playcounts:                # Series not included
                    it.library_playcounts.update({item.contentSerieName: 0})        # update the .nfo playCount
                    estado_update = True                                            # We mark that we have updated something

        if estado_update:
            logger.error('** Update status: ' + str(estado) + ' / PlayCount: ' + str(it.library_playcounts))
            estado = estado_update
        # it is verified that if all the episodes of a season are marked, tb the season is marked
        for key, value in it.library_playcounts.items():
            if key.startswith("season"):
                season = scrapertools.find_single_match(key, r'season (\d+)')        # We obtain in no. seasonal
                it = check_season_playcount(it, season)
        # We save the changes to item.nfo
        if filetools.write(nfo_path, head_nfo + it.tojson()):
            return (it, estado)
    return (item, False)


def mark_content_as_watched(item):
    logger.debug()

    if not item.videolibrary_id:
        for code in item.infoLabels['code']:
            if code and code != 'None':
                break
        item.videolibrary_id=code
    if item.contentType == 'episode':
        episodes = videolibrarydb['episode'][item.videolibrary_id]
        episodes['{}x{}'.format(item.contentSeason, str(item.contentEpisodeNumber).zfill(2))]['item'].infoLabels['playcount'] = item.playcount
        videolibrarydb['episode'][item.videolibrary_id] = episodes
        videolibrarydb.close()

        season_episodes = [ep for ep in episodes.values() if ep['item'].contentSeason == item.contentSeason]
        watched = [ep for ep in season_episodes if ep['item'].infoLabels['playcount'] > 0]
        if len(watched) == len(season_episodes):
            item.playcount = 1
        else:
            item.playcount = 0
        mark_season_as_watched(item)

    elif item.contentType == 'season':
        mark_season_as_watched(item)

    else:
        content = videolibrarydb[item.contentType][item.videolibrary_id]
        content['item'].infoLabels['playcount'] = item.playcount
        videolibrarydb[item.contentType][item.videolibrary_id] = content
        seasons = videolibrarydb['season'][item.videolibrary_id]
        videolibrarydb.close()
        item.all_ep = True
        if item.contentType == 'tvshow':
            for season in seasons.keys():
                item.contentSeason = season
                mark_season_as_watched(item)

    if config.is_xbmc() and not item.not_update:
        from platformcode import xbmc_videolibrary
        xbmc_videolibrary.mark_content_as_watched_on_kodi(item, item.playcount)


def mark_season_as_watched(item):
    logger.debug()

    seasons = videolibrarydb['season'][item.videolibrary_id]
    seasons[item.contentSeason].infoLabels['playcount'] = item.playcount
    videolibrarydb['season'][item.videolibrary_id] = seasons
    episodes = videolibrarydb['episode'][item.videolibrary_id]
    videolibrarydb.close()

    for n, ep in episodes.items():
        if ep['item'].contentSeason == item.contentSeason:
            episodes[n]['item'].infoLabels['playcount'] = item.playcount

    videolibrarydb['episode'][item.videolibrary_id] = episodes
    videolibrarydb.close()

    watched = True
    for season in seasons.values():
        if season.infoLabels['playcount'] != item.playcount:
            watched = False

    if watched or item.playcount == 0:
        tvshow = videolibrarydb['tvshow'][item.videolibrary_id]
        it = videolibrarydb['tvshow'][item.videolibrary_id]['item']
        it.infoLabels['playcount'] = item.playcount
        tvshow['item'] = it
        videolibrarydb['tvshow'][item.videolibrary_id] = tvshow
        videolibrarydb.close()



def mark_tvshow_as_updatable(item, silent=False):
    logger.debug()
    head_nfo, it = videolibrarytools.read_nfo(item.nfo)
    it.active = item.active
    filetools.write(item.nfo, head_nfo + it.tojson())

    if not silent:
        platformtools.itemlist_refresh()


def delete(item):
    from platformcode import xbmc_videolibrary
    select = None
    delete = None
    if item.contentType == 'movie':
        library_path = videolibrarytools.MOVIES_PATH
        head = 70084
    else:
        library_path = videolibrarytools.TVSHOWS_PATH
        head = 70085
    from core import channeltools

    channels = [c for c in videolibrarydb[item.contentType].get(item.videolibrary_id,{}).get('channels',{}).keys()]
    channels.sort()
    option_list = [config.get_localized_string(head)]
    for channel in channels:
        option_list.append(channeltools.get_channel_parameters(channel)['title'])

    if len(option_list) > 2:
        select = platformtools.dialog_select(config.get_localized_string(70088) % item.infoLabels['title'], option_list)
    else:
        delete = platformtools.dialog_yesno(config.get_localized_string(head), config.get_localized_string(70088) % item.infoLabels['title'])
    if select == 0 or delete:
        del videolibrarydb[item.contentType][item.videolibrary_id]
        if item.contentType == 'tvshow':
            del videolibrarydb['season'][item.videolibrary_id]
            del videolibrarydb['episode'][item.videolibrary_id]
        path = filetools.join(library_path, item.base_name)

        filetools.rmdirtree(path)
        if config.is_xbmc() and config.get_setting("videolibrary_kodi"):
            from platformcode import xbmc_videolibrary
            xbmc_videolibrary.clean_by_id(item)
        platformtools.itemlist_refresh()
    if select and select > 0:

        channel_name = channels[select - 1]

        if item.contentType != 'movie':
            episodes = videolibrarydb['episode'][item.videolibrary_id]
            seasons = videolibrarydb['season'][item.videolibrary_id]
            episodes_dict = dict(episodes)
            seasons_dict = dict(seasons)

            for key, episode in episodes_dict.items():
                if len(episode['channels']) > 1:
                    del episode['channels'][channel_name]
                elif channel_name in episode['channels']:
                    xbmc_videolibrary.clean_by_id(episodes[key]['item'])
                    del episodes[key]
            videolibrarydb['episode'][item.videolibrary_id] = episodes
            seasons_list = []

            for episode in episodes:
                season = int(episode.split('x')[0])
                if season not in seasons_list:
                    seasons_list.append(season)

            for season in seasons_dict.keys():
                if season not in seasons_list:
                    xbmc_videolibrary.clean_by_id(seasons[season])
                    del seasons[season]
            videolibrarydb['season'][item.videolibrary_id] = seasons
        channel = videolibrarydb[item.contentType][item.videolibrary_id]
        channels = channel['channels']
        del channels[channel_name]
        channel['channels'] = channels
        videolibrarydb[item.contentType][item.videolibrary_id] = channel

    videolibrarydb.close()



def check_season_playcount(item, season):
    logger.debug()

    if season:
        episodios_temporada = 0
        episodios_vistos_temporada = 0
        for key, value in item.library_playcounts.items():
            if key.startswith("%sx" % season):
                episodios_temporada += 1
                if value > 0:
                    episodios_vistos_temporada += 1

        if episodios_temporada == episodios_vistos_temporada:
            # it is verified that if all the seasons are seen, the series is marked as view
            item.library_playcounts.update({"season %s" % season: 1})
        else:
            # it is verified that if all the seasons are seen, the series is marked as view
            item.library_playcounts.update({"season %s" % season: 0})

    return check_tvshow_playcount(item, season)


def check_tvshow_playcount(item, season):
    logger.debug()
    if season:
        temporadas_serie = 0
        temporadas_vistas_serie = 0
        for key, value in item.library_playcounts.items():
            if key.startswith("season" ):
                temporadas_serie += 1
                if value > 0:
                    temporadas_vistas_serie += 1

        if temporadas_serie == temporadas_vistas_serie:
            item.library_playcounts.update({item.title: 1})
        else:
            item.library_playcounts.update({item.title: 0})

    else:
        playcount = item.library_playcounts.get(item.title, 0)
        item.library_playcounts.update({item.title: playcount})

    return item


def add_download_items(item, itemlist):
    if config.get_setting('downloadenabled'):
        localOnly = True
        for i in itemlist:
            if i.contentChannel != 'local':
                localOnly = False
                break
        if not item.fromLibrary and not localOnly:
            downloadItem = Item(channel='downloads',
                                from_channel=item.channel,
                                title=typo(config.get_localized_string(60355), "color kod bold"),
                                fulltitle=item.fulltitle,
                                show=item.fulltitle,
                                contentType=item.contentType,
                                contentSerieName=item.contentSerieName,
                                url=item.url,
                                action='save_download',
                                from_action="findvideos",
                                contentTitle=item.contentTitle,
                                path=item.path,
                                thumbnail=thumb('downloads'),
                                parent=item.tourl())
            if item.action == 'findvideos':
                if item.contentType != 'movie':
                    downloadItem.title = '{} {}'.format(typo(config.get_localized_string(60356), "color kod bold"), item.title)
                else:  # film
                    downloadItem.title = typo(config.get_localized_string(60354), "color kod bold")
                downloadItem.downloadItemlist = [i.tourl() for i in itemlist]
                itemlist.append(downloadItem)
            else:
                if item.contentSeason:  # season
                    downloadItem.title = typo(config.get_localized_string(60357), "color kod bold")
                    itemlist.append(downloadItem)
                else:  # tvshow + not seen
                    itemlist.append(downloadItem)
                    itemlist.append(downloadItem.clone(title=typo(config.get_localized_string(60003), "color kod bold"), unseen=True))


def prefered_lang(item):
    tempdb = videolibrarydb[item.contentType][item.videolibrary_id]
    videolibrarydb.close()
    item = tempdb['item']
    lang_list = tempdb['item'].lang_list
    prefered = item.lang_list.index(item.prefered_lang)
    item.prefered_lang = lang_list[platformtools.dialog_select(config.get_localized_string(70246), lang_list, prefered)]
    tempdb['item'] = item
    videolibrarydb[item.contentType][item.videolibrary_id] = tempdb
    videolibrarydb.close()

def disable_channels(item):
    from core import channeltools
    tempdb = videolibrarydb[item.contentType][item.videolibrary_id]
    videolibrarydb.close()
    item = tempdb['item']
    channels_list = list(tempdb['channels'].keys())
    channels_name = [channeltools.get_channel_parameters(c).get('title', '') for c in channels_list]
    disabled = [channels_list.index(c) for c in channels_list if c in item.disabled]
    channels_disabled = platformtools.dialog_multiselect(config.get_localized_string(70837), channels_name, preselect=disabled)
    if type(channels_disabled) == list:
        item.disabled = [channels_list[c] for c in channels_disabled]
        videolibrarydb[item.contentType][item.videolibrary_id] = tempdb
        videolibrarydb.close()

def get_host(item , channel=None):
    if item.url.startswith('//'): item.url = 'https:' + item.url
    if not item.url.startswith('/') and not httptools.downloadpage(item.url, only_headers=True).success:
        item.url = urlparse.urlparse(item.url).path
    if item.url.startswith('/'):
        if not channel:
            try : channel = __import__('channels.' + item.channel, None, None, ['channels.' + item.channel])
            except: channel = __import__('specials.' + item.channel, None, None, ['specials.' + item.channel])

        host = channel.host
        if host.endswith('/'): host = host[:-1]
        item.url = host + item.url

    return item

def set_active(item):
    show = videolibrarydb['tvshow'][item.videolibrary_id]
    videolibrarydb.close()
    show['item'].active = False if item.active else True
    videolibrarydb['tvshow'][item.videolibrary_id] = show
    videolibrarydb.close()
    platformtools.itemlist_refresh()

def change_poster(item):
    import xbmcgui
    video = videolibrarydb[item.contentType][item.videolibrary_id]
    videolibrarydb.close()
    options = []
    it = xbmcgui.ListItem('Corrente')
    it.setArt({'thumb':item.thumbnail})
    options.append(it)
    posters = video['item'].infoLabels.get('posters',[])
    for n, poster in enumerate(posters):
        it = xbmcgui.ListItem(str(n))
        it.setArt({'thumb':poster})
        options.append(it)
    selection = platformtools.dialog_select('',options, 0, True)
    if selection > 0:
        video['item'].thumbnail = video['item'].infoLabels['thumbnail'] = posters[selection]
        videolibrarydb[item.contentType][item.videolibrary_id] = video
        videolibrarydb.close()
        platformtools.itemlist_refresh()

def change_fanart(item):
    import xbmcgui
    video = videolibrarydb[item.contentType][item.videolibrary_id]
    videolibrarydb.close()
    options = []
    it = xbmcgui.ListItem('Corrente')
    it.setArt({'thumb':item.fanart})
    options.append(it)
    fanarts = video['item'].infoLabels.get('fanarts',[])
    for n, poster in enumerate(fanarts):
        it = xbmcgui.ListItem(str(n))
        it.setArt({'thumb':poster})
        options.append(it)
    selection = platformtools.dialog_select('',options, 0, True)
    if selection > 0:
        video['item'].fanart = video['item'].infoLabels['fanart'] = fanarts[selection]
        videolibrarydb[item.contentType][item.videolibrary_id] = video
        videolibrarydb.close()
        platformtools.itemlist_refresh()
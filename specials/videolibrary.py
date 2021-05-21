# -*- coding: utf-8 -*-

#from builtins import str
import sys
from core import httptools, support

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import xbmc, os, traceback

from core import filetools, scrapertools, videolibrarytools
from core.support import typo, thumb
from core.item import Item
from platformcode import config, launcher, logger, platformtools
from core.videolibrarytools import videolibrarydb

if PY3:
    from concurrent import futures
    import urllib.parse as urlparse
else:
    from concurrent_py2 import futures
    import urlparse




def mainlist(item):
    logger.debug()

    itemlist = [Item(channel=item.channel, action="list_movies", title=config.get_localized_string(60509),
                     category=config.get_localized_string(70270), thumbnail=thumb("videolibrary_movie")),
                Item(channel=item.channel, action="list_tvshows",title=config.get_localized_string(60600),
                     category=config.get_localized_string(70271), thumbnail=thumb("videolibrary_tvshow"),
                     context=[{"channel":"videolibrary", "action":"update_videolibrary", "title":config.get_localized_string(70269), 'forced':True}]),
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
        it = value['item']
        it.context = [{'title':config.get_localized_string(70084),'channel':'videolibrary', 'action':'delete'}]
        if len(it.lang_list) > 1:
            it.context += [{"title": config.get_localized_string(70246),
                                "action": "prefered_lang",
                                "channel": "videolibrary"}]
        watched = it.infoLabels.get("playcount", 0)
        if watched > 0:
            title = config.get_localized_string(60016)
            value = 0
        else:
            title = config.get_localized_string(60017)
            value = 1

        it.context += [{"title": title,
                          "action": "mark_content_as_watched",
                          "channel": "videolibrary",
                          "playcount": value}]
        itemlist.append(it)

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

    def sub_thread(key, value):
        it = value['item']
        it.contentType = 'tvshow'

        it.context = [{'title':config.get_localized_string(70085),'channel':'videolibrary', 'action':'delete'}]

        if len(it.lang_list) > 1:
            it.context += [{"title": config.get_localized_string(70246),
                              "action": "prefered_lang",
                              "channel": "videolibrary"}]
        if len(value['channels'].keys()) > 1:
            it.context += [{"title": config.get_localized_string(70837),
                              "action": "disable_channels",
                              "channel": "videolibrary"}]
        watched = it.infoLabels.get("playcount", 0)
        if watched > 0:
            title = config.get_localized_string(60020)
            value = 0
        else:
            title = config.get_localized_string(60021)
            value = 1

        it.context += [{"title": title,
                          "action": "mark_content_as_watched",
                          "channel": "videolibrary",
                          "playcount": value}]
        if not it.active:
            it.title = '{} {}'.format(it.title, support.typo('','bullet bold'))
            title = config.get_localized_string(60023)
        else:
            title = config.get_localized_string(60022)
        it.context += [{"title": title,
                        "action": "set_active",
                        "channel": "videolibrary",
                        "playcount": value}]
        it.context += [{"title": config.get_localized_string(70269),
                        "action": "update_videolibrary",
                        "channel": "videolibrary"}]
        it.context += [{"title": 'Poster',
                                 "action": "change_poster",
                                 "channel": "videolibrary",
                                 "playcount": value}]
        it.context += [{"title": 'fanart',
                                 "action": "change_fanart",
                                 "channel": "videolibrary",
                                 "playcount": value}]
        return it

    with futures.ThreadPoolExecutor() as executor:
        _list = [executor.submit(sub_thread, key, value) for key, value in series.items()]
        for res in futures.as_completed(_list):
            itemlist.append(res.result())

    if itemlist:
        itemlist = sorted(itemlist, key=lambda it: it.title.lower())

        itemlist += [Item(channel=item.channel, action="update_videolibrary", thumbnail=item.thumbnail,
                          fanart=item.thumbnail, landscape=item.thumbnail, forced=True,
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

        def sub_thread(season):
            it = season
            it.contentType = 'season'

            #Contextual menu: Mark the season as viewed or not
            watched = it.infoLabels.get("playcount", 0)
            if watched > 0:
                title = config.get_localized_string(60028)
                value = 0
            else:
                title = config.get_localized_string(60029)
                value = 1

            it.context = [{"title": title,
                                 "action": "mark_content_as_watched",
                                 "channel": "videolibrary",
                                 "playcount": value}]
            return it

        with futures.ThreadPoolExecutor() as executor:
            _list = [executor.submit(sub_thread, season) for season in seasons.values()]
            for res in futures.as_completed(_list):
                itemlist.append(res.result())

        if len(itemlist) > 1:
            itemlist = sorted(itemlist, key=lambda it: int(it.contentSeason))
        else:
            return get_episodes(itemlist[0])

        if config.get_setting("show_all_seasons", "videolibrary"):
            it = item.clone(action="get_episodes", title=config.get_localized_string(60030), all=True)
            it.infoLabels["playcount"] = 0
            itemlist.insert(0, it)

        add_download_items(item, itemlist)
    return itemlist


def get_episodes(item):
    logger.debug()
    itemlist = []

    episodes = videolibrarydb['episode'][item.videolibrary_id]
    videolibrarydb.close()

    def sub_thread(title, ep):
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
                           "playcount": value}]
            return it
        return

    with futures.ThreadPoolExecutor() as executor:
        _list = [executor.submit(sub_thread, title, ep) for title, ep in episodes.items()]
        for res in futures.as_completed(_list):
            if res.result(): itemlist.append(res.result())


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
            itlist = [executor.submit(servers, item, ch, value) for ch, value in videolibrary_items.items() if ch not in disabled]
            for res in futures.as_completed(itlist):
                itemlist += res.result()

        pl = [s for s in itemlist if s.contentLanguage in [prefered_lang, '']]
        if pl: itemlist = pl


        if len(itlist) > 1:
            for it in itemlist:
                it.title = '[{}] {}'.format(it.ch_name, it.title)


        if autoplay.play_multi_channel(item, itemlist):  # hideserver
            return []

    itemlist.sort(key=lambda it: (videolibrarytools.quality_order.index(it.quality.lower()) if it.quality and it.quality.lower() in videolibrarytools.quality_order else 999, it.server))
    add_download_items(item, itemlist)

    return itemlist


def servers(item, ch, items):
    serverlist = []
    from core import channeltools
    ch_params = channeltools.get_channel_parameters(ch)
    ch_name = ch_params.get('title', '')

    def channel_servers(item, it, channel, ch_name):
        serverlist = []
        it.contentChannel = 'videolibrary'
        it = get_host(it, channel)
        it.contentTitle = it.fulltitle = item.title
        for item in getattr(channel, it.action)(it):
            if item.server and item.channel:
                item.ch_name = ch_name
                serverlist.append(item)
        return serverlist

    if ch_params.get('active', False):

        if os.path.isfile(os.path.join(config.get_runtime_path(), 'channels', ch + ".py")): CHANNELS = 'channels'
        else: CHANNELS = 'specials'
        try: channel = __import__('%s.%s' % (CHANNELS, ch), None, None, ['%s.%s' % (CHANNELS, ch)])
        except ImportError: exec("import " + CHANNELS + "." + ch + " as channel")
        with futures.ThreadPoolExecutor() as executor:
            itlist = [executor.submit(channel_servers, item, it, channel, ch_name) for it in items]
            for res in futures.as_completed(itlist):
                serverlist += res.result()

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


def update_videolibrary(item=None):
    logger.debug("Update Series...")
    from core import channeltools
    import datetime
    p_dialog = None
    update_when_finished = False
    now = datetime.date.today()
    try:
        config.set_setting("updatelibrary_last_check", now.strftime('%Y-%m-%d'), "videolibrary")

        message = config.get_localized_string(60389)
        p_dialog = platformtools.dialog_progress_bg(config.get_localized_string(20000), config.get_localized_string(60037))
        p_dialog.update(0, '')
        show_list = []

        if item and item.videolibrary_id:
            show = videolibrarydb['tvshow'][item.videolibrary_id]

            for s in show['channels'].values():
                    show_list += s
        else:
            shows = dict(videolibrarydb['tvshow']).values()

            for show in shows:
                if show['item'].active or item.forced:
                    for s in show['channels'].values():
                        show_list += s

        t = float(100) / len(show_list)
        i = 0

        for it in show_list:
            i += 1
            chname = channeltools.get_channel_parameters(it.channel)['title']
            p_dialog.update(int(i * t), message=message % (it.fulltitle, chname))
            it = get_host(it)
            try: channel = __import__('channels.%s' % it.channel, fromlist=["channels.%s" % it.channel])
            except: channel = __import__('specials.%s' % it.channel, fromlist=["specials.%s" % it.channel])
            itemlist = getattr(channel, it.action)(it)
            videolibrarytools.save_tvshow(it, itemlist, True)
        p_dialog.close()

    except:
        p_dialog.close()
        logger.error(traceback.format_exc())

    videolibrarydb.close()

    if item and item.videolibrary_id:
        update_when_finished = set_active_tvshow(show)
    else :
        update_when_finished = set_active_tvshow(list(shows))

    if update_when_finished:
        platformtools.itemlist_refresh()

    # if config.get_setting('trakt_sync'):
    #     from core import trakt_tools
    #     trakt_tools.update_all()


def set_active_tvshow(value):
    update_when_finished = False
    def sub_thread(show, update_when_finished):
        ret = None
        if show['item'].active:
            prefered_lang = show['item'].prefered_lang
            active = False if show['item'].infoLabels['status'].lower() == 'ended' else True
            episodes = videolibrarydb['episode'][show['item'].videolibrary_id]

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
                        ret = show
        return show, ret, update_when_finished

    if type(value) == list:
        with futures.ThreadPoolExecutor() as executor:
            _list = [executor.submit(sub_thread, s, update_when_finished) for s in value]
            for res in futures.as_completed(_list):
                if res.result() and res.result()[1]:
                    videolibrarydb['tvshow'][res.result()[0]['item'].videolibrary_id] = res.result()[1]
                if res.result()[2]:
                    update_when_finished = True
    else:
        show, ret, update_when_finished = sub_thread(value, update_when_finished)
        if ret:
            videolibrarydb['tvshow'][show['item'].videolibrary_id] = ret

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


# def add_local_episodes(item):
#     logger.debug()

#     done, local_episodes_path = videolibrarytools.config_local_episodes_path(item.path, item, silent=True)
#     if done < 0:
#         logger.debug("An issue has occurred while configuring local episodes")
#     elif local_episodes_path:
#         nfo_path = filetools.join(item.path, "tvshow.nfo")
#         head_nfo, item_nfo = videolibrarytools.read_nfo(nfo_path)
#         item_nfo.local_episodes_path = local_episodes_path
#         if not item_nfo.active:
#             item_nfo.active = 1
#         filetools.write(nfo_path, head_nfo + item_nfo.tojson())

#         update_tvshow(item)

#         platformtools.itemlist_refresh()


# def remove_local_episodes(item):
#     logger.debug()

#     nfo_path = filetools.join(item.path, "tvshow.nfo")
#     head_nfo, item_nfo = videolibrarytools.read_nfo(nfo_path)

#     for season_episode in item_nfo.local_episodes_list:
#         filetools.remove(filetools.join(item.path, season_episode + '.strm'))

#     item_nfo.local_episodes_list = []
#     item_nfo.local_episodes_path = ''
#     filetools.write(nfo_path, head_nfo + item_nfo.tojson())

#     update_tvshow(item)

#     platformtools.itemlist_refresh()


def mark_content_as_watched(item):
    class mark_as_watched(object):
        def __init__(self, *args, **kwargs):
            self.item = kwargs.get('item')
            self.s = self.item.contentSeason
            self.e = self.item.contentEpisodeNumber
            self.playcount = self.item.playcount

            if self.item.contentType == 'movie':
                self.movie = videolibrarydb['movie'][self.item.videolibrary_id]
            else:
                self.tvshow = videolibrarydb['tvshow'][self.item.videolibrary_id]
                self.seasons = videolibrarydb['season'][self.item.videolibrary_id]
                self.episodes = videolibrarydb['episode'][self.item.videolibrary_id]

            getattr(self, 'mark_' + self.item.contentType)()

            videolibrarydb.close()
            # support.dbg()
            if config.is_xbmc() and not self.item.not_update:
                from platformcode import xbmc_videolibrary
                xbmc_videolibrary.mark_content_as_watched_on_kodi(self.item, self.playcount)
            else:
                platformtools.itemlist_refresh()

        def mark_episode(self):
            current_playcount = self.episodes['{:d}x{:02d}'.format(self.s, self.e)]['item'].infoLabels['playcount']

            if self.playcount > 0:
                self.episodes['{:d}x{:02d}'.format(self.s, self.e)]['item'].infoLabels['playcount'] += self.playcount
            else:
                self.episodes['{:d}x{:02d}'.format(self.s, self.e)]['item'].infoLabels['playcount'] = 0

            videolibrarydb['episode'][self.item.videolibrary_id] = self.episodes

            if current_playcount == 0 or self.playcount == 0:
                self.check_playcount('episode')

        def mark_season(self):
            current_playcount = self.seasons[self.s].infoLabels['playcount']

            if self.playcount > 0:
                self.seasons[self.s].infoLabels['playcount'] += self.playcount
            else:
                self.seasons[self.s].infoLabels['playcount'] = 0

            videolibrarydb['season'][self.item.videolibrary_id] = self.seasons
            self.mark_all('episodes')

            if current_playcount == 0 or self.playcount == 0:
                self.check_playcount('season')

        def mark_tvshow(self):
            if self.playcount > 0:
                self.tvshow['item'].infoLabels['playcount'] += self.playcount
            else:
                self.tvshow['item'].infoLabels['playcount'] = 0

            videolibrarydb['tvshow'][self.item.videolibrary_id] = self.tvshow
            self.mark_all('seasons')

        def mark_movie(self):
            if self.playcount:
                self.movie['item'].infoLabels['playcount'] += self.playcount
            else:
                self.movie['item'].infoLabels['playcount'] = 0
            videolibrarydb['movie'][self.item.videolibrary_id] = self.movie

        def check_playcount(self, _type):
            tv_playcount = 0
            season_playcount = 0

            if _type == 'episode':
                episodes = [e for e in self.episodes.values() if e['item'].contentSeason == self.s]
                watched = [e for e in episodes if e['item'].infoLabels['playcount'] > 0]
                all_watched  = [e for e in self.episodes.values() if e['item'].infoLabels['playcount'] > 0]
                if len(all_watched) == len(self.episodes):
                    tv_playcount = self.playcount
                if len(watched) == len(episodes):
                    season_playcount = self.playcount
                self.tvshow['item'].infoLabels['playcount'] = tv_playcount
                self.seasons[self.s].infoLabels['playcount'] = season_playcount
                videolibrarydb['season'][self.item.videolibrary_id] = self.seasons
            else:
                watched = [s for s in self.seasons.values() if s.infoLabels['playcount'] > 0]
                if len(watched) == len(self.seasons):
                    tv_playcount = self.playcount
                self.tvshow['item'].infoLabels['playcount'] = tv_playcount
            videolibrarydb['tvshow'][self.item.videolibrary_id] = self.tvshow

        def mark_all(self, _type):
            episodes = [e for e in self.episodes.values() if e['item'].contentSeason == self.s]
            if _type == 'episodes':
                for n, ep in self.episodes.items():
                    self.episodes[n]['item'].infoLabels['playcount'] = self.playcount
                # self.check_playcount('season')
            else:
                for n, season in self.seasons.items():
                    self.seasons[n].infoLabels['playcount'] = self.playcount
                for n, ep in self.episodes.items():
                    self.episodes[n]['item'].infoLabels['playcount'] = self.playcount
                videolibrarydb['season'][self.item.videolibrary_id] = self.seasons
            videolibrarydb['episode'][self.item.videolibrary_id] = self.episodes
    # support.dbg()
    mark_as_watched(item=item)


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
        platformtools.itemlist_refresh(-1)
    if select and select > 0:

        channel_name = channels[select - 1]

        if item.contentType != 'movie':
            episodes = videolibrarydb['episode'][item.videolibrary_id]
            seasons = videolibrarydb['season'][item.videolibrary_id]
            episodes_dict = dict(episodes)
            seasons_dict = dict(seasons)

            for key, episode in episodes_dict.items():
                if len(episode['channels']) > 1 and channel_name in episode['channels']:
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
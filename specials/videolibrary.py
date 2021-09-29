# -*- coding: utf-8 -*-

#from builtins import str
import channels
import sys, os, traceback, xbmc, xbmcgui

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

from core import httptools, support, filetools, scrapertools, videolibrarytools, videolibrarydb
from core.item import Item
from platformcode import config, dbconverter, logger, platformtools

if PY3:
    from concurrent import futures
    import urllib.parse as urlparse
else:
    from concurrent_py2 import futures
    import urlparse


def mainlist(item):
    logger.debug()
    itemlist = [item.clone(title=config.get_localized_string(60509), contentType='movie', action='list_movies', thumbnail=support.thumb('videolibrary_movie')),
                item.clone(title=support.typo(config.get_localized_string(70741) % config.get_localized_string(30122) + '...', 'submenu'), contentType='movie',action='search_list',  thumbnail=support.thumb('search_movie')),
                item.clone(title=config.get_localized_string(60600), contentType='tvshow', action='list_tvshows', thumbnail=support.thumb('videolibrary_tvshow'),
                           context=[{'channel':'videolibrary', 'action':'update_videolibrary', 'title':config.get_localized_string(70269)}]),
                item.clone(title=support.typo(config.get_localized_string(70741) % config.get_localized_string(30123) + '...', 'submenu'),contentType='tvshow', action='search_list', thumbnail=support.thumb('search_tvshow')),
                item.clone(channel='shortcuts', title=support.typo(config.get_localized_string(70287),'bold color kod'), action='SettingOnPosition',
                           category=2, setting=1, thumbnail = support.thumb('setting'),folder=False)]
    support.thumb(itemlist)
    return itemlist


def search_list(item):
    itemlist = [item.clone(title=config.get_localized_string(70032) + '{search}', action='list_genres'),
                item.clone(title=config.get_localized_string(70042) + '{search}', action='list_years'),
                item.clone(title=config.get_localized_string(70314) + '{search}', action='list_az', next_action='list_actors'),
                item.clone(title=config.get_localized_string(70473) + '{search}', action='list_ratings'),
                item.clone(title='Registi' + '{search}', action='list_az', next_action='list_directors'),
                item.clone(title=config.get_localized_string(30980) + '{search}', action='search')]
    if item.contentType == 'movie':
        itemlist.insert(0, item.clone(title='Collezioni', action='list_sets'))
    support.thumb(itemlist)
    return itemlist


def list_az(item):
    videos = dict(videolibrarydb[item.contentType]).values()
    videolibrarydb.close()
    cast = []
    for v in videos:
        if item.next_action == 'list_actors':
            v = v['item'].infoLabels['castandrole']
        else:
            v = v['item'].infoLabels
            if 'director' in v:
                v = v.get('director','').split(',')
            else:
                v= v.get('writer','').split(',')
        cast += [c[0].strip() for c in v if c]

    az = []
    for c in cast:
        if c[0] not in az:
            az.append(c[0])
    itemlist = [item.clone(title=i, action=item.next_action) for i in az]
    return sorted(itemlist, key=lambda it: it.title)


def list_genres(item):
    videos = dict(videolibrarydb[item.contentType]).values()
    videolibrarydb.close()

    genres = []
    for v in videos:
        genres += v['item'].infoLabels['genre'].split(',')

    itemlist = []
    for g in genres:
        g = g.strip()
        if g and g not in [it.list_genre for it in itemlist]:
            it = item.clone(title = g, action='list_{}s'.format(item.contentType), list_genre=g)
            itemlist.append(it)

    itemlist.sort(key=lambda it: it.list_genre)
    support.thumb(itemlist, True)
    return itemlist


def list_sets(item):
    videos = dict(videolibrarydb['collection']).values()
    videolibrarydb.close()
    itemlist = []
    itemlist = [v.clone(contentType='list') for v in videos]
    itemlist.sort(key=lambda it: it.title)
    add_context(itemlist)
    return itemlist


def list_directors(item):
    videos = dict(videolibrarydb[item.contentType]).values()
    videolibrarydb.close()

    directors = []
    director_images = []
    for v in videos:
        v = v['item'].infoLabels
        if 'director' in v:
            directors += v['director'].split(',')
            director_images += v['director_image']
        else:
            directors += v['writer'].split(',')
            director_images += v['writer_image']
    itemlist = []
    for i, d in enumerate(directors):
        d = d.strip()
        if d and d[0][0] == item.title and d not in [it.list_director for it in itemlist]:
            it = item.clone(title = d, action='list_{}s'.format(item.contentType), list_director=d, thumbnail=director_images[i] if len(director_images) > i else filetools.join(config.get_runtime_path(), 'resources','skins','Default','media','Infoplus','no_photo.png'))
            itemlist.append(it)

    itemlist.sort(key=lambda it: it.list_director)
    return itemlist


def list_years(item):
    videos = dict(videolibrarydb[item.contentType]).values()
    videolibrarydb.close()

    years = [v['item'].infoLabels['year'] for v in videos]

    itemlist = []
    for y in years:
        if y and y not in [it.list_year for it in itemlist]:
            it = item.clone(title = str(y), action='list_{}s'.format(item.contentType), list_year=y)
            itemlist.append(it)

    itemlist.sort(key=lambda it: it.list_year, reverse=True)
    return itemlist


def list_ratings(item):
    videos = dict(videolibrarydb[item.contentType]).values()
    videolibrarydb.close()

    ratings = [int(float(v['item'].infoLabels['rating'])) for v in videos]

    itemlist = []
    for r in ratings:
        if r and r not in [it.list_rating for it in itemlist]:
            it = item.clone(title = str(r), action='list_{}s'.format(item.contentType), list_rating=r)
            itemlist.append(it)

    itemlist.sort(key=lambda it: it.list_rating, reverse=True)
    return itemlist


def list_actors(item):
    videos = dict(videolibrarydb[item.contentType]).values()
    videolibrarydb.close()

    actors = []
    for v in videos:
        actors += [[a[0].strip(), a[2].strip(), a[4]] for a in v['item'].infoLabels['castandrole']]

    itemlist = []
    for a in actors:
        if a and a[0][0] == item.title and a[0] not in [it.list_actor for it in itemlist]:
            it = item.clone(title = a[0], action='list_{}s'.format(item.contentType), list_actor=a[0], thumbnail=a[1] if a[1] else filetools.join(config.get_runtime_path(), 'resources','skins','Default','media','Infoplus','no_photo.png'))
            itemlist.append(it)

    itemlist.sort(key=lambda it: it.list_actor)
    return itemlist


def search(item, text):
    item.text = text
    if item.contentType == 'movie':
        return list_movies(item)
    else:
        return list_tvshows(item)


def list_movies(item, silent=False):
    logger.debug()

    videos = dict(videolibrarydb['movie']).values()
    if item.list_year: itemlist = [platformtools.window_type(v['item']) for v in videos if item.list_year == v['item'].infoLabels['year']]
    elif item.list_rating: itemlist = [platformtools.window_type(v['item']) for v in videos if item.list_rating == int(float(v['item'].infoLabels['rating']))]
    elif item.list_genre: itemlist = [platformtools.window_type(v['item']) for v in videos if item.list_genre in v['item'].infoLabels['genre']]
    elif item.list_actor: itemlist = [platformtools.window_type(v['item']) for v in videos if item.list_actor in str(v['item'].infoLabels['castandrole'])]
    elif item.list_director: itemlist = [platformtools.window_type(v['item']) for v in videos if item.list_director in v['item'].infoLabels['director']]
    elif item.set: itemlist = [platformtools.window_type(v['item']) for v in videos if item.set == v['item'].infoLabels.get('setid', '')]
    elif config.get_setting('collection') and not item.text: itemlist = [v['item'] for v in videos if (item.text.lower() in v['item'].title.lower() and not 'setid' in v['item'].infoLabels)] + [v.clone(contentType='list') for v in dict(videolibrarydb['collection']).values()]
    else: itemlist = [platformtools.window_type(v['item']) for v in videos if item.text.lower() in v['item'].title.lower()]
    videolibrarydb.close()
    add_context(itemlist)
    if silent == False:
        if item.set: item.sorted = 'year'
        else: item.sorted = 'name'
    return itemlist


def list_tvshows(item):
    logger.debug()

    item.sorted = 'name'

    itemlist = []

    videos = dict(videolibrarydb['tvshow']).values()

    if item.list_year: series = [platformtools.window_type(v['item']) for v in videos if item.list_year == v['item'].infoLabels['year']]
    elif item.list_rating: series = [platformtools.window_type(v['item']) for v in videos if item.list_rating == int(float(v['item'].infoLabels['rating']))]
    elif item.list_genre: series = [platformtools.window_type(v['item']) for v in videos if item.list_genre in v['item'].infoLabels['genre']]
    elif item.list_actor: series = [platformtools.window_type(v['item']) for v in videos if item.list_actor in str(v['item'].infoLabels['castandrole'])]
    elif item.list_director: series = [platformtools.window_type(v['item']) for v in videos if item.list_director in v['item'].infoLabels['director'] or item.list_director in v['item'].infoLabels['writer']]
    else: series = [platformtools.window_type(v['item']) for v in videos if item.text.lower() in v['item'].title.lower()]

    def sub_thread(it):
        it.contentType = 'tvshow'
        seasons = videolibrarydb['season'][it.videolibrary_id]
        if config.get_setting('no_pile_on_seasons', 'videolibrary') == 2 or config.get_setting('no_pile_on_seasons', 'videolibrary') == 1 and len(seasons) == 1:
            it.action = 'get_episodes'
            it.all = True
        if not it.active:
            it.title += '  [B]•[/B]'
            it.contentTitle += '  [B]•[/B]'

        return it

    with futures.ThreadPoolExecutor() as executor:
        _list = [executor.submit(sub_thread, it) for it in series]
        for res in futures.as_completed(_list):
            itemlist.append(res.result())

    if itemlist:
        itemlist = sorted(itemlist, key=lambda it: it.title.lower())
        add_context(itemlist)
        thumbnail = support.thumb('videolibrary_tvshow')
        itemlist += [Item(channel=item.channel, action='update_videolibrary', thumbnail=thumbnail,
                          fanart=thumbnail, landscape=thumbnail,
                          title=support.typo(config.get_localized_string(70269), 'bold color kod'), folder=False)]
    videolibrarydb.close()
    return itemlist


def configure_update_videolibrary(item):
    import xbmcgui
    # Load list of options (active user channels that allow global search)
    lista = []
    ids = []
    preselect = []

    for i, item_tvshow in enumerate(item.lista):
        it = xbmcgui.ListItem(item_tvshow['title'], '')
        it.setArt({'thumb': item_tvshow['thumbnail'], 'fanart': item_tvshow['fanart']})
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
    item.sorted = None

    seasons = videolibrarydb['season'][item.videolibrary_id]
    videolibrarydb.close()

    itemlist = sorted(seasons.values(), key=lambda it: int(it.contentSeason))

    add_context(itemlist)
    add_download_items(item, itemlist)
    return itemlist


def get_episodes(item):
    logger.debug()
    itemlist = []
    item.sorted = None

    episodes = videolibrarydb['episode'][item.videolibrary_id]
    videolibrarydb.close()

    def sub_thread(title, ep):
        it = ep['item']

        if it.contentSeason == item.contentSeason or item.all:
            if config.get_setting('no_pile_on_seasons', 'videolibrary') == 2 or item.all:
                it.onlyep = False
            else:
                it.onlyep = True
            it = get_host(it)
            it.window = True if item.window_type == 0 or (config.get_setting("window_type") == 0) else False
            if it.window:
                it.folder = False
            it.from_library = item.from_library
            return it
        return

    with futures.ThreadPoolExecutor() as executor:
        _list = [executor.submit(sub_thread, title, ep) for title, ep in episodes.items()]
        for res in futures.as_completed(_list):
            if res.result(): itemlist.append(res.result())


    itemlist = sorted(itemlist, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))
    add_context(itemlist)
    add_download_items(item, itemlist)
    return itemlist


def findvideos(item):
    from core import autoplay, servertools
    from platformcode import platformtools

    videolibrarytools.check_renumber_options(item)
    itemlist = []

    if not item.strm_path:
        logger.debug('Unable to search for videos due to lack of parameters')
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
    if not item.infoLabels.get('tmdb_id'):
        if item.contentType == 'movie':
            item.infoLabels = videolibrarydb['movie'][item.videolibrary_id]['item'].infoLabels
        else:
            ep = '{:d}x{:02d}'.format(item.contentSeason, item.contentEpisodeNumber)
            item.infoLabels = videolibrarydb['episode'][item.videolibrary_id][ep]['item'].infoLabels

    videolibrarydb.close()

    if videolibrary_items.get('local'):
        try:
            local = videolibrary_items['local']
            item.url = local.get('db', local.get('internal', local.get('connected')))
            if not '/' in item.url and not '\\' in item.url:
                path = videolibrarytools.MOVIES_PATH if item.contentType == 'movie' else videolibrarytools.TVSHOWS_PATH
                item.url = filetools.join(path, item.url)
            item.channel = 'local'
            if filetools.exists(item.url):
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

    if config.get_setting('autoplay'):
        itemlist = autoplay.start(itemlist, item)
    else:
        itemlist = servertools.sort_servers(itemlist)

    if config.get_setting('checklinks') and not config.get_setting('autoplay'):
        itemlist = servertools.check_list_links(itemlist, config.get_setting('checklinks_number'))

    if not item.window:
        add_download_items(item, itemlist)

    return itemlist


def servers(item, ch, items):
    serverlist = []
    from core import channeltools
    ch_params = channeltools.get_channel_parameters(ch)
    ch_name = ch_params.get('title', '')

    def channel_servers(item, it, channel, ch_name):
        serverlist = []
        # it.contentChannel = 'videolibrary'
        it = get_host(it, channel)
        it.infoLabels = item.infoLabels
        it.videolibrary_id = item.videolibrary_id
        it.contentTitle = it.fulltitle = item.title
        it.contentChannel = 'videolibrary'
        it.from_library = item.from_library
        for item in getattr(channel, it.action)(it):
            if item.server and item.channel:
                item.ch_name = ch_name
                serverlist.append(item)
        return serverlist

    if ch_params.get('active', False):
        channel = platformtools.channel_import(ch)

        with futures.ThreadPoolExecutor() as executor:
            itlist = [executor.submit(channel_servers, item, it, channel, ch_name) for it in items]
            for res in futures.as_completed(itlist):
                serverlist += res.result()

    return serverlist


def play(item):
    logger.log()
    # logger.dbg()
    # logger.debug("item:\n" + item.tostring('\n'))
    # platformtools.play_video(item)

    if not item.channel == "local":
        channel = platformtools.channel_import(item.channel)

        if hasattr(channel, "play"):
            itemlist = getattr(channel, "play")(item)

        else:
            itemlist = [item.clone()]
    else:
        return platformtools.play_video(item.clone(url=item.url, server="local"))
        # itemlist = [item.clone(url=item.url, server="local")]

    # For direct links in list format
    if isinstance(itemlist[0], list):
        item.video_urls = itemlist
        itemlist = [item]

    # This is necessary in case the channel play deletes the data
    for v in itemlist:
        if isinstance(v, Item):
            v.nfo = item.nfo
            v.strm_path = item.strm_path
            v.infoLabels = item.infoLabels
            if item.contentTitle:
                v.title = item.contentTitle
            else:
                if item.contentType == "episode":
                    v.title = config.get_localized_string(60036) % item.contentEpisodeNumber
            v.thumbnail = item.thumbnail
            v.contentThumbnail = item.thumbnail
            v.contentChannel = item.contentChannel

    return itemlist



def update_videolibrary(item=None):
    logger.debug('Update Series...')
    from core import channeltools
    import datetime
    p_dialog = None
    update_when_finished = False
    now = datetime.date.today()

    try:
        config.set_setting('updatelibrary_last_check', now.strftime('%Y-%m-%d'), 'videolibrary')

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
                if show['item'].active or (item and item.forced):
                    for s in show['channels'].values():
                        show_list += s

        t = float(100) / len(show_list) if len(show_list) > 0 else 1
        i = 0

        for it in show_list:
            i += 1
            it.not_add = True
            chname = channeltools.get_channel_parameters(it.channel)['title']
            p_dialog.update(int(i * t), message=message % (it.fulltitle, chname))
            it = get_host(it)
            channel = platformtools.channel_import(it.channel)
            itemlist = getattr(channel, it.action)(it)
            videolibrarytools.save_tvshow(it, itemlist, True)
        p_dialog.close()
        if config.get_setting("videolibrary_kodi"):
            dbconverter.save_all('tvshow')

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


def mark_content_as_watched(item):
    class mark_as_watched(object):
        def __init__(self, *args, **kwargs):
            self.item = kwargs.get('item')
            self.s = self.item.contentSeason
            self.e = self.item.contentEpisodeNumber
            self.playcount = self.item.playcount
            self.movies = []

            if self.item.set:
                self.mark_collection()
                for m in dict(videolibrarydb['movie']).values():
                    if m['item'].infoLabels.get('setid') == self.item.set:
                        self.movies.append(m['item'])
                        self.item.videolibrary_id = m['item'].videolibrary_id
                        self.movie = m
                        self.mark_movie()

            elif self.item.contentType == 'movie':
                self.movie = videolibrarydb['movie'][self.item.videolibrary_id]
            else:
                self.tvshow = videolibrarydb['tvshow'][self.item.videolibrary_id]
                self.seasons = videolibrarydb['season'][self.item.videolibrary_id]
                self.episodes = videolibrarydb['episode'][self.item.videolibrary_id]

            getattr(self, 'mark_' + (self.item.mark if self.item.mark else self.item.contentType))()
            videolibrarydb.close()

            if config.is_xbmc() and not self.item.not_update:
                from platformcode import xbmc_videolibrary
                if self.movies:
                    for movie in self.movies:
                        xbmc_videolibrary.mark_content_as_watched_on_kodi(movie, self.playcount)
                else:
                    it = None
                    if self.item.contentType == 'movie': it = self.movie['item']
                    elif self.item.contentType == 'episode': it = self.episodes['{:d}x{:02d}'.format(self.s, self.e)]['item']
                    else: it = self.tvshow['item']
                    # elif self.item.contentType == 'season': it = self.seasons[self.s]
                    if it: xbmc_videolibrary.mark_content_as_watched_on_kodi(it, self.playcount)

                platformtools.itemlist_refresh(1, True if item.contentType in ['season', 'episode'] else False)

        def mark_previous(self):
            if self.item.contentType == 'episode':
                current_episode = current_playcount = self.episodes['{:d}x{:02d}'.format(self.s, self.e)]['item']
                seasons = [s for s in self.seasons.keys()]
                seasons.sort()
                for it in self.episodes.values():
                    if (it['item'].contentSeason == current_episode.contentSeason and it['item'].contentEpisodeNumber < current_episode.contentEpisodeNumber) or it['item'].contentSeason < current_episode.contentSeason:
                        it['item'].infoLabels['playcount'] = 1
                videolibrarydb['episode'][self.item.videolibrary_id] = self.episodes
                for s in range(seasons[0], self.item.contentSeason + 1):
                    self.s = s
                    self.check_playcount('episode')
            elif self.item.contentType == 'season':
                seasons = [s for s in self.seasons.keys()]
                seasons.sort()
                for s in range(seasons[0], self.s):
                    self.s = s
                    self.mark_season()

        def mark_following(self):
            if self.item.contentType == 'episode':
                current_episode = current_playcount = self.episodes['{:d}x{:02d}'.format(self.s, self.e)]['item']
                seasons = [s for s in self.seasons.keys()]
                seasons.sort()
                for it in self.episodes.values():
                    if (it['item'].contentSeason == current_episode.contentSeason and it['item'].contentEpisodeNumber > current_episode.contentEpisodeNumber) or it['item'].contentSeason > current_episode.contentSeason:
                        it['item'].infoLabels['playcount'] = 0
                videolibrarydb['episode'][self.item.videolibrary_id] = self.episodes
                for s in range(self.item.contentSeason, seasons[-1] + 1):
                    self.s = s
                    self.check_playcount('episode')
            elif self.item.contentType == 'season':
                seasons = [s for s in self.seasons.keys()]
                seasons.sort()
                for s in range(self.s + 1, seasons[-1] + 1):
                    self.s = s
                    self.mark_season()

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
            self.mark_all('season_episodes')

            if current_playcount == 0 or self.playcount == 0:
                self.check_playcount('season')

        def mark_tvshow(self):
            if self.playcount > 0:
                self.tvshow['item'].infoLabels['playcount'] += self.playcount
            else:
                self.tvshow['item'].infoLabels['playcount'] = 0

            videolibrarydb['tvshow'][self.item.videolibrary_id] = self.tvshow
            self.mark_all('seasons')

        def mark_collection(self):
            self.collection = videolibrarydb['collection'][self.item.set]
            self.collection.infoLabels['playcount'] = self.playcount
            videolibrarydb['collection'][self.item.set] = self.collection

        def mark_movie(self):
            if self.playcount:
                self.movie['item'].infoLabels['playcount'] += self.playcount
            else:
                self.movie['item'].infoLabels['playcount'] = 0
            videolibrarydb['movie'][self.item.videolibrary_id] = self.movie
            movie_collection_id = self.movie['item'].infoLabels.get('setid')
            if not self.item.set and movie_collection_id:
                collection_list = [m['item'].infoLabels['playcount'] for m in dict(videolibrarydb['movie']).values() if m['item'].infoLabels.get('setid') == movie_collection_id]
                if self.playcount == 0 or len(collection_list) == len([v for v in collection_list if v > 0]):
                    self.item.set = movie_collection_id
                    self.mark_collection()


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
                try:
                    self.seasons[self.s].infoLabels['playcount'] = season_playcount
                except:
                    logger.debug('No Season')
                videolibrarydb['season'][self.item.videolibrary_id] = self.seasons
            else:
                watched = [s for s in self.seasons.values() if s.infoLabels['playcount'] > 0]
                if len(watched) == len(self.seasons):
                    tv_playcount = self.playcount
                self.tvshow['item'].infoLabels['playcount'] = tv_playcount
            videolibrarydb['tvshow'][self.item.videolibrary_id] = self.tvshow

        def mark_all(self, _type):
            if _type == 'season_episodes':
                episodes = [e for e in self.episodes.values() if e['item'].contentSeason == self.s]
                for e in episodes:
                    e['item'].infoLabels['playcount'] = self.playcount
            elif _type == 'episodes':
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

    mark_as_watched(item=item)


def mark_tvshow_as_updatable(item, silent=False):
    logger.debug()
    head_nfo, it = videolibrarytools.read_nfo(item.nfo)
    it.active = item.active
    filetools.write(item.nfo, head_nfo + it.tojson())

    if not silent:
        platformtools.itemlist_refresh()


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
            channel = platformtools.channel_import(item.channel)
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


#-------------- CONTEXT --------------

def add_context(itemlist, title=config.get_localized_string(30052)):
    title += '...'
    for item in itemlist:
        item.infoLabels['title'] = item.infoLabels.get('title', item.title)
        item.context = [{'title':title, 'channel':'videolibrary', 'action':'subcontext'}]

class subcontext(object):
    def __init__(self, item):
        self.item = item
        self.context = []
        self.commands = []
        self.titledict = {'movie':{'images':60240, 'notwatched':60016, 'watched':60017, 'delete':70084, 'lang':70246},
                          'tvshow':{'images':60240, 'notwatched':60020, 'watched':60021, 'delete':70085, 'lang':70246, 'notactive':60022, 'active': 60023, 'update':70269},
                          'season':{'images':60240, 'notwatched':60028, 'watched':60029},
                          'episode':{'images':60240, 'notwatched':60032, 'watched':60033},
                          'list':{'images':60240, 'notwatched':60016, 'watched':60017, 'delete':30048}}
        self.makecontext()
        self.run()

    def title(self, _type):
         return config.get_localized_string(self.titledict[self.item.contentType][_type])

    def makecontext(self):
        # logger.dbg()
        # set watched
        # if not self.item.set:
        watched = self.item.infoLabels.get('playcount', 0)
        if watched > 0:
            title = self.title('notwatched')
            value = 0
        else:
            title = self.title('watched')
            value = 1
        self.context.append(title)
        self.context.append('Segna precedenti come visti')
        self.context.append('Segna successivi come non visti')
        self.commands.append(self.item.clone(action='mark_content_as_watched', playcount=value))
        self.commands.append(self.item.clone(action='mark_content_as_watched', playcount=value, mark='previous'))
        self.commands.append(self.item.clone(action='mark_content_as_watched', playcount=value, mark='following'))

        if self.item.contentType in ['movie', 'tvshow', 'list']:
            # delete
            self.context.append(self.title('delete'))
            self.commands.append(self.item.clone(action='delete'))

            # defalut language
            if len(self.item.lang_list) > 1:
                self.context.append(self.title('lang'))
                self.commands.append(self.item.clone(action='prefered_lang'))

        if self.item.contentType in ['movie', 'tvshow']:
            if len(videolibrarydb[self.item.contentType].get(self.item.videolibrary_id, {}).get('channels', {}).keys()) > 1:
                self.context.append(config.get_localized_string(70837))
                self.commands.append(self.item.clone(action='disable_channels'))
            videolibrarydb.close()

        if self.item.contentType in ['tvshow']:
            # set active for update
            if self.item.active: self.context.append(self.title('notactive'))
            else: self.context.append(self.title('active'))
            self.commands.append(self.item.clone(action='set_active'))

            # update
            self.context.append(self.title('update'))
            self.commands.append(self.item.clone(action='update_videolibrary', forced=True))

        self.context.append(self.title('images'))
        self.commands.append(self.item.clone(action='set_images'))


    def run(self):
        index = xbmcgui.Dialog().contextmenu(self.context)
        if index >= 0: xbmc.executebuiltin('RunPlugin({}?{})'.format(sys.argv[0], self.commands[index].tourl()))

class set_images(object):
    def __init__(self, item):
        self.item = item
        self.item_type = self.item.contentType if self.item.contentType != 'list' else 'collection'
        self.type_dict = {'posters':'Poster', 'fanarts':'Fanart', 'banners':'Banner', 'landscapes':'Landscape', 'clearlogos':'ClearLogo'}
        self.video = videolibrarydb[self.item_type][self.item.videolibrary_id]
        self.select_type()
        videolibrarydb.close()

    def select_type(self):
        types = []
        self.types = []
        self.list = []
        for k, v in self.type_dict.items():
            if self.item.infoLabels.get(k):
                it = xbmcgui.ListItem(v)
                it.setArt({'thumb': self.item.infoLabels[k[:-1].replace('poster', 'thumbnail')]})
                types.append(it)
                self.types.append(k)
                self.list.append(self.item.infoLabels[k])
        selection = platformtools.dialog_select(self.item.contentTitle, types, 0, True)
        if selection >= 0:
            self.set_art(self.types[selection])

    def set_art(self, n):
        images = []
        items = []
        t = n[:-1].replace('poster', 'thumbnail')

        for i, a in enumerate([self.item.infoLabels[t]] + self.item.infoLabels[n]):
            title = 'Remote' if i > 0 else 'Current'
            it = xbmcgui.ListItem(title)
            it.setArt({'thumb': a})
            items.append(it)
            images.append(a)

        selection = platformtools.dialog_select(self.item.contentTitle, items, 0, True)
        if selection > 0:
            selected = images[selection]

            index = None
            if self.item_type == 'collection':
                self.video.infoLabels[t] = selected
                if t == 'thumbnail': self.video.thumbnail = selected
                if t == 'fanart': self.video.fanart = selected

            elif self.item_type == 'episode':
                index = '{}x{:02d}'.format(self.item.contentSeason, self.item.contentEpisodeNumber)
                self.video[index]['item'].infoLabels[t] = selected
                if t == 'thumbnail': self.video[index]['item'].thumbnail = selected
                if t == 'fanart': self.video[index]['item'].fanart = selected

            elif self.item_type == 'season':
                index = self.item.contentSeason
                self.video[index].infoLabels[t] = selected
                if t == 'thumbnail': self.video[index].thumbnail = selected
                if t == 'fanart': self.video[index].fanart = selected

            else:
                self.video['item'].infoLabels[t] = selected
                if t == 'thumbnail': self.video['item'].thumbnail = selected
                if t == 'fanart': self.video['item'].fanart = selected

        videolibrarydb[self.item_type][self.item.videolibrary_id] = self.video
        platformtools.itemlist_refresh()

#-------------- DOWNLOAD --------------

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
                                title=support.typo(config.get_localized_string(60355), 'color kod bold'),
                                fulltitle=item.fulltitle,
                                show=item.fulltitle,
                                contentType=item.contentType,
                                contentSerieName=item.contentSerieName,
                                url=item.url,
                                action='save_download',
                                from_action='findvideos',
                                contentTitle=config.get_localized_string(60355),
                                path=item.path,
                                thumbnail=support.thumb('download'),
                                parent=item.tourl())

            if item.action == 'findvideos':
                if item.contentType != 'movie':
                    downloadItem.title = '{} {}'.format(support.typo(config.get_localized_string(60356), 'color kod bold'), item.title)
                else:  # film
                    downloadItem.title = support.typo(config.get_localized_string(60354), 'color kod bold')
                downloadItem.downloadItemlist = [i.tourl() for i in itemlist]
                itemlist.append(downloadItem)
            else:
                if item.contentSeason:  # season
                    downloadItem.title = support.typo(config.get_localized_string(60357), 'color kod bold')
                    itemlist.append(downloadItem)
                else:  # tvshow + not seen
                    itemlist.append(downloadItem)
                    itemlist.append(downloadItem.clone(title=support.typo(config.get_localized_string(60003), 'color kod bold'), contentTitle=config.get_localized_string(60003), unseen=True))

#-------------- DELETE --------------

def delete(item):
    # logger.dbg()
    from platformcode import xbmc_videolibrary
    select = None
    delete = None

    # get videolibrary path
    if item.contentType == 'movie':
        library_path = videolibrarytools.MOVIES_PATH
        head = 70084
    else:
        library_path = videolibrarytools.TVSHOWS_PATH
        head = 70085

    # load channel in videoitem
    from core import channeltools
    channels = [c for c in videolibrarydb[item.contentType].get(item.videolibrary_id,{}).get('channels',{}).keys()]
    channels.sort()
    option_list = [config.get_localized_string(head)]
    for channel in channels:
        option_list.append(channeltools.get_channel_parameters(channel)['title'])

    # If there are more channels shows the dialogue of choice
    if len(option_list) > 2:
        select = platformtools.dialog_select(config.get_localized_string(70088) % item.infoLabels['title'], option_list)
    else:
        delete = platformtools.dialog_yesno(config.get_localized_string(head), config.get_localized_string(70088) % item.infoLabels['title'])

    # If you have chosen to delete the movie, the collection or the series
    if select == 0 or delete:
        # delete collection
        if item.set:
            del videolibrarydb['collection'][item.set]
            for k, v in dict(videolibrarydb['movie']).items():
                if v['item'].infoLabels.get('setid') == item.set:
                    del videolibrarydb['movie'][k]
            platformtools.itemlist_refresh(-1)
        else:
            # delete movie or series
            del videolibrarydb[item.contentType][item.videolibrary_id]

            # check if there is movies in collection
            if item.contentType == 'movie':
                if item.infoLabels.get('setid'):
                    find = 0
                    for v in dict(videolibrarydb['movie']).values():
                        if v['item'].infoLabels.get('setid') == item.infoLabels.get('setid'):
                            find += 1
                    if find == 0:
                        del videolibrarydb['collection'][item.infoLabels.get('setid')]

            # delete seasons and episodes
            if item.contentType == 'tvshow':
                del videolibrarydb['season'][item.videolibrary_id]
                del videolibrarydb['episode'][item.videolibrary_id]

            # remove files
            path = filetools.join(library_path, item.base_name)

            filetools.rmdirtree(path)
            if config.is_xbmc() and config.get_setting('videolibrary_kodi'):
                from platformcode import xbmc_videolibrary
                xbmc_videolibrary.clean_by_id(item)
            else:
                platformtools.itemlist_refresh(-1)

    # delete channel from video item
    if select and select > 0:
        channel_name = channels[select - 1]

        if item.contentType != 'movie':
            episodes = videolibrarydb['episode'][item.videolibrary_id]
            seasons = videolibrarydb['season'][item.videolibrary_id]
            episodes_dict = dict(episodes)
            seasons_dict = dict(seasons)

            # delete episodes if they have no channels
            for key, episode in episodes_dict.items():
                if len(episode['channels']) > 1 and channel_name in episode['channels']:
                    del episode['channels'][channel_name]
                elif channel_name in episode['channels']:
                    xbmc_videolibrary.clean_by_id(episodes[key]['item'])
                    del episodes[key]

            videolibrarydb['episode'][item.videolibrary_id] = episodes
            seasons_list = []

            # delete seasons if they have no channels
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


def delete_videolibrary(item):
    logger.debug()

    if not platformtools.dialog_yesno(config.get_localized_string(20000), config.get_localized_string(80037)):
        return

    p_dialog = platformtools.dialog_progress_bg(config.get_localized_string(20000), config.get_localized_string(80038))
    p_dialog.update(0)

    if config.is_xbmc() and config.get_setting('videolibrary_kodi'):
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

    videolibrarydb['collection'].clear()
    videolibrarydb['movie'].clear()
    videolibrarydb['tvshow'].clear()
    videolibrarydb['season'].clear()
    videolibrarydb['episode'].clear()
    videolibrarydb.close()

    platformtools.dialog_notification(config.get_localized_string(20000), config.get_localized_string(80039), time=5000, sound=False)

#-------------- MOVE --------------

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
        config.set_setting('videolibrarypath', backup_current_path)
        config.set_setting('folder_movies', current_movies_folder)
        config.set_setting('folder_tvshows', current_tvshows_folder)
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
    if current_path != new_path and not filetools.listdir(current_path) and not 'plugin.video.kod\\videolibrary' in current_path:
        filetools.rmdirtree(current_path)

    xbmc_videolibrary.update_sources(backup_new_path, backup_current_path)
    if config.is_xbmc() and config.get_setting('videolibrary_kodi'):
        xbmc_videolibrary.update_db(backup_current_path, backup_new_path, current_movies_folder, new_movies_folder, current_tvshows_folder, new_tvshows_folder, progress)
    else:
        progress.update(100)
        xbmc.sleep(1000)
        progress.close()
    if notify:
        platformtools.dialog_notification(config.get_localized_string(20000), config.get_localized_string(80014), time=5000, sound=False)

#------------------------------------------------
#                OLD FUNCTIONS
#------------------------------------------------

def channel_config(item):
    return platformtools.show_channel_settings(channelpath=os.path.join(config.get_runtime_path(), 'channels', item.channel), caption=config.get_localized_string(60598))

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
            folder = 'folder_movies'
            item.path = filetools.split(nfo_path)[0]
            item.nfo = nfo_path
            sep = '/' if '/' in nfo_path else '\\'
            item.extra = filetools.join(config.get_setting('videolibrarypath'), config.get_setting(folder), item.path.split(sep)[-1])
            strm_path = item.strm_path.replace('\\', '/').rstrip('/')
            if not item.thumbnail: item.thumbnail = item.infoLabels['thumbnail']
            if '/' in item.path: item.strm_path = strm_path
            # If strm has been removed from kodi library, don't show it
            if not filetools.exists(filetools.join(item.path, filetools.basename(strm_path))) and not local: return Item(), 0

            # Contextual menu: Mark as seen / not seen
            visto = item.library_playcounts.get(strm_path.strip('/').split('/')[0], 0)
            item.infoLabels['playcount'] = visto
            if visto > 0:
                seen_text = config.get_localized_string(60016)
                counter = 0
            else:
                seen_text = config.get_localized_string(60017)
                counter = 1

            # Context menu: Delete series / channel
            channels_num = len(item.library_urls)
            if 'downloads' in item.library_urls: channels_num -= 1
            if channels_num > 1: delete_text = config.get_localized_string(60018)
            else: delete_text = config.get_localized_string(60019)

            item.context = [{'title': seen_text, 'action': 'mark_content_as_watched', 'channel': 'videolibrary',  'playcount': counter},
                            {'title': delete_text, 'action': 'delete', 'channel': 'videolibrary', 'multichannel': multichannel}]
        else:
            folder = 'folder_tvshows'
            try:
                item.title = item.contentTitle
                item.path = filetools.split(nfo_path)[0]
                item.nfo = nfo_path
                sep = '/' if '/' in nfo_path else '\\'
                item.extra = filetools.join(config.get_setting('videolibrarypath'), config.get_setting(folder), item.path.split(sep)[-1])
                # Contextual menu: Mark as seen / not seen
                visto = item.library_playcounts.get(item.contentTitle, 0)
                item.infoLabels['playcount'] = visto
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
                item.title += ' [B]' + u'\u2022' + '[/B]'

            # Context menu: Delete series / channel
            channels_num = len(item.library_urls)
            if 'downloads' in item.library_urls: channels_num -= 1
            if channels_num > 1: delete_text = config.get_localized_string(60024)
            else: delete_text = config.get_localized_string(60025)

            item.context = [{'title': seen_text, 'action': 'mark_content_as_watched', 'channel': 'videolibrary', 'playcount': counter},
                            {'title': update_text, 'action': 'mark_tvshow_as_updatable', 'channel': 'videolibrary', 'active': value},
                            {'title': delete_text, 'action': 'delete', 'channel': 'videolibrary', 'multichannel': multichannel},
                            {'title': config.get_localized_string(70269), 'action': 'update_tvshow', 'channel': 'videolibrary'}]
            if item.local_episodes_path == '': item.context.append({'title': config.get_localized_string(80048), 'action': 'add_local_episodes', 'channel': 'videolibrary'})
            else: item.context.append({'title': config.get_localized_string(80049), 'action': 'remove_local_episodes', 'channel': 'videolibrary'})
    else: item = Item()
    return item, value


def convert_videolibrary(item):
    videolibrarytools.convert_videolibrary()

def restore_videolibrary(item):
    videolibrarytools.restore_videolibrary()


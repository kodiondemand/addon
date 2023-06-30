# -*- coding: utf-8 -*-
# -*- Channel Community -*-


import re, inspect, mimetypes, xbmcgui

from core import httptools, jsontools, tmdb, support, filetools
from core.item import Item
from lib import unshortenit
from platformcode import config, platformtools, logger
from channelselector import get_thumb
from collections import OrderedDict
from core import servertools

info_language = ["de", "en", "es", "fr", "it", "pt"]  # from videolibrary.json
try:
    lang = info_language[config.get_setting("info_language", "videolibrary")]
except:
    lang = 'it'

defpage = ["", "20", "40", "60", "80", "100"]
defp = defpage[config.get_setting('pagination', 'community')]
disable_pagination = False
show_seasons = config.get_setting('show_seasons', 'community')

tmdb_api = 'a1ab8b8669da03637a4b98fa39c39228'


def mainlist(item):
    logger.debug()

    path = filetools.join(config.get_data_path(), 'community_channels.json')
    if not filetools.exists(path):
        with open(path, "w") as file:
            file.write('{"channels":{}}')
            file.close()

    return show_channels(item)


def show_channels(item):
    logger.debug()
    itemlist = []

    # add context menu
    context = [{"title": config.get_localized_string(50005), "action": "remove_channel", "channel": "community"}]

    # read json
    json = load_and_check(item)

    itemlist.append(Item(channel=item.channel,
                         title=support.typo(config.get_localized_string(70676), 'bold color kod'),
                         action='add_channel',
                         thumbnail=get_thumb('add.png')))

    for key, channel in json['channels'].items():
        path = filetools.dirname(channel['path'])  # relative path
        channel_json = load_json(channel)  # read channel json

        # retrieve information from json
        thumbnail = relative('thumbnail', channel_json, path)
        if not thumbnail: thumbnail = item.thumbnail
        fanart = relative('fanart', channel_json, path)
        plot = channel_json['plot'] if 'plot' in channel_json else ''

        itemlist.append(Item(channel=item.channel,
                             title=support.typo(channel['channel_name'], 'bold'),
                             url=channel['url'] if 'url' in channel else path,
                             thumbnail=thumbnail,
                             fanart=fanart,
                             plot=plot,
                             action='show_menu',
                             channel_id=key,
                             context=context,
                             path=path))

    support.channel_config(item, itemlist)
    return itemlist


def show_menu(item):
    logger.debug()
    itemlist = []

    if item.menu:  # if second level menu
        get_sub_menu(item, item.menu, 'level2', itemlist)
    else:
        if type(item.url) == dict:
            json = item.url
        else:
            json = load_json(item)
        if 'disable_pagination' in json:
            item.disable_pagination = True
        if 'sort' in json and json['sort']:
            item.sort = True

        for key in json:
            if key != 'sort':
                if key == 'menu':
                    get_menu(item, json, key, itemlist)
                if item.filterkey and not item.filter:
                    itemlist += submenu(item, json, key)
                elif key in ['movies_list', 'tvshows_list', 'generic_list']:
                    itemlist += peliculas(item, json, key)
                elif key in ['seasons_list']:
                    item.url = json
                    itemlist += get_seasons(item)
                elif key in ['episodes_list']:
                    itemlist += episodios(item, json, key)
                elif key in ['links', 'find_links']:
                    itemlist += findvideos(item)
                elif key in ['search'] and 'url' in json['search']:
                    search_json = json['search']
                    itemlist += get_search_menu(item, search_json)

        if 'channel_name' in json and not 'disable_search' in json and 'search' not in json:
            itemlist += get_search_menu(item, json, channel_name=json['channel_name'])
    logger.debug('PAGINATION:', disable_pagination)
    return itemlist


def search(item, text):
    logger.info('search', text)
    itemlist = []

    if item.custom_search:
        if '{}' in item.url:
            item.url = item.custom_search.format(text)
        else:
            item.url = item.custom_search + text
    elif item.global_search:
        itemlist = global_search(item, text)
    else:
        item.search = text

    json = load_json(item)
    if json:
        for key in json:
            if key not in ['sort']:
                if item.custom_search and key == 'menu':
                    get_menu(item, json, key, itemlist)
                else:
                    peliculas(item, json, key, itemlist)

    return itemlist


def global_search(item, text):
    itemlist = []
    json = load_json(item)
    item.global_search = None

    if 'menu' in json:
        for option in json['menu']:
            if option in ['submenu', 'level2'] and 'seach' in json['menu'][option] and 'url' in json['menu'][option][
                'search']:
                item.custom_search = json['menu'][option]['search']['url']
                itemlist += search(item, text)
            else:
                extra = set_extra_values(item, option, item.path)
                item.url = extra.url
                if item.url:
                    itemlist += global_search(item, text)

    if any(key in json for key in ['movies_list', 'tvshows_list', 'generic_list']):
        itemlist += search(item, text)
    return itemlist


def peliculas(item, json='', key='', itemlist=[]):
    item.plot = item.thumb = item.fanart = ''
    logger.debug('PAGINATION:', item.disable_pagination)
    if not json:
        key = item.key
        json = load_json(item)[key]
    else:
        json = json[key]

    # logger.debug('DEBUG:', json)

    if item.sort:
        json.sort(key=lambda x: x.get('title', ''), reverse=False)

    infoLabels = item.infoLabels if item.infoLabels else {}
    contentType = 'tvshow' if 'tvshow' in key else 'movie'
    itlist = filterkey = []
    action = 'findvideos'

    if inspect.stack(0)[1][3] not in ['add_tvshow', 'get_episodes', 'update', 'find_episodes',
                                     'search'] and not item.filterkey and not item.disable_pagination:
        Pagination = int(defp) if defp.isdigit() else ''
    else:
        Pagination = ''
    pag = item.page if item.page else 1

    for i, option in enumerate(json):
        if Pagination and (pag - 1) * Pagination > i: continue  # pagination
        if Pagination and i >= pag * Pagination: break
        if item.filterkey and item.filterkey in option:
            filterkey = [it.lower() for it in option[item.filterkey]] if type(option[item.filterkey]) == list else [
                option[item.filterkey].lower()]
        else:
            filterkey = []
        title = option['title'] if 'title' in option else ''

        if 'tvshows_list' in key and 'links' not in option:
            action = 'episodios'

        # filter elements
        if (not item.filter or item.filter.lower() in filterkey) and item.search.lower() in title.lower() and title:

            if 'generic_list' in key and 'links' not in option and 'url' in option:
                option['links'] = []
                option['links'].append({'url': option['url']})
                option['url'] = ''

            extra = set_extra_values(item, option, item.path)

            infoLabels['year'] = option['year'] if 'year' in option else ''
            infoLabels['tmdb_id'] = option['tmdb_id'] if 'tmdb_id' in option else ''

            it = Item(channel=item.channel,
                      title=set_title(title, extra.language, extra.quality),
                      fulltitle=title,
                      show=title,
                      contentTitle=title if contentType == 'movie' else '',
                      contentSerieName=title if contentType != 'movie' else '',
                      contentType=contentType,
                      infoLabels=infoLabels,
                      url=extra.url,
                      path=item.path,
                      thumbnail=extra.thumb,
                      fanart=extra.fanart,
                      plot=extra.plot,
                      personal_plot=extra.plot,
                      action=action)
            itlist.append(it)

    if not 'generic_list' in key:
        tmdb.set_infoLabels(itlist, seekTmdb=True)
    itemlist += itlist

    # if item.sort:
    #     itemlist.sort(key=lambda x: x.title.lower(), reverse=False)
    if Pagination and len(itemlist) >= Pagination:
        if inspect.stack(0)[1][3] != 'get_newest':
            item.title = support.typo(config.get_localized_string(30992), 'color kod bold')
            item.page = pag + 1
            item.thumbnail = support.thumb()
            itemlist.append(item)
    return itemlist


def get_seasons(item):
    logger.debug()
    itemlist = []
    infoLabels = item.infoLabels
    json = item.url if type(item.url) == dict else item.url
    if 'seasons_list' in json:
        json = json['seasons_list']
    elif 'tvshows_list' in json:
        return show_menu(item)
    for option in json:
        infoLabels['season'] = option['season']
        title = config.get_localized_string(60027) % option['season']
        extra = set_extra_values(item, option, item.path)
        # url = relative('link', option, item.path)

        itemlist.append(Item(channel=item.channel,
                             title=set_title(title),
                             fulltitle=item.fulltitle,
                             show=item.show,
                             thumbnail=extra.thumb,
                             filterseason=int(option['season']),
                             url=extra.url,
                             action='episodios',
                             contentSeason=option['season'],
                             infoLabels=infoLabels,
                             contentType='season' if show_seasons else 'tvshow',
                             path=extra.path))

    if inspect.stack(0)[2][3] in ['add_tvshow', 'get_episodes', 'update', 'find_episodes',
                                 'get_newest'] or show_seasons == False:
        itlist = []
        for item in itemlist:
            itlist = episodios(item)
        itemlist = itlist
        if inspect.stack(0)[2][3] not in ['add_tvshow', 'get_episodes', 'update', 'find_episodes',
                                         'get_newest'] and defp and not item.disable_pagination:
            itemlist = pagination(item, itemlist)

    # if show_seasons:
    support.videolibrary(itemlist, item)
    support.download(itemlist, item)
    return itemlist


def episodios(item, json='', key='', itemlist=[]):
    logger.debug()
    infoLabels = item.infoLabels
    itm = item

    if type(item.url) == dict:
        if 'seasons_list' in item.url:
            return get_seasons(item)
        elif 'tvshows_list' in item.url:
            return peliculas(item, item.url, 'tvshows_list')
        else:
            json = {}
            json = item.url['episodes_list']
    else:
        json = load_json(item)
        if 'episodes_list' in json:
            json = json['episodes_list']
        elif 'seasons_list' in json:
            item.url = json['seasons_list']
            return get_seasons(item)
        elif 'tvshows_list' in json:
            return peliculas(item, json, 'tvshows_list')

    # set variable
    ep = 1
    season = infoLabels['season'] if 'season' in infoLabels else item.contentSeason if item.contentSeason else 1

    if inspect.stack(0)[1][3] not in ['add_tvshow', 'get_episodes', 'update', 'find_episodes',
                                     'search'] and not show_seasons:
        Pagination = int(defp) if defp.isdigit() else ''
    else:
        Pagination = ''
    pag = item.page if item.page else 1

    # make items
    for i, option in enumerate(json):
        if Pagination and (pag - 1) * Pagination > i: continue  # pagination
        if Pagination and i >= pag * Pagination: break
        # build numeration of episodes
        numeration = option['number'] if 'number' in option else option['title']
        match = support.match(numeration, patron=r'(?P<season>\d+)x(?P<episode>\d+)').match
        if match:
            episode_number = match[1]
            ep = int(match[1]) + 1
            season_number = int(match[0])
        else:
            season_number = option['season'] if 'season' in option else season if season else 1
            episode_number = option['number'] if 'number' in option else option['episode'] if 'episode' else ''
            if type(episode_number) == int:
                pass
            elif not episode_number.isdigit():
                episode_number = support.match(option['title'], patron=r'(?P<episode>\d+)').match
            ep = int(episode_number) if episode_number else ep
            if not episode_number:
                episode_number = str(ep).zfill(2)
                ep += 1

        infoLabels['season'] = season_number
        infoLabels['episode'] = episode_number
        title = ' - ' + option['title'] if 'title' in option else ''
        title = '%sx%s%s' % (season_number, episode_number, title)
        extra = set_extra_values(item, option, item.path)
        if not item.filterseason or season_number == int(item.filterseason):
            itemlist.append(Item(channel=item.channel,
                                 title=set_title(title, extra.language, extra.quality),
                                 fulltitle=item.fulltitle,
                                 show=item.show,
                                 url=option,
                                 action='findvideos',
                                 plot=extra.plot,
                                 thumbnail=extra.thumb if extra.thumb else item.thumbnail,
                                 fanart=extra.fanart,
                                 contentSeason=season_number,
                                 contentEpisode=episode_number,
                                 infoLabels=infoLabels,
                                 contentType='episode',
                                 path=item.path))

    # if showseason
    if inspect.stack(0)[1][3] not in ['add_tvshow', 'get_episodes', 'update', 'find_episodes', 'get_newest', 'search']:
        if show_seasons and not item.filterseason:
            itm.contentType = 'season'
            season_list = []
            for item in itemlist:
                if item.contentSeason not in season_list:
                    season_list.append(item.contentSeason)
            itemlist = []
            for season in season_list:
                itemlist.append(Item(channel=item.channel,
                                     title=set_title(config.get_localized_string(60027) % season),
                                     fulltitle=itm.fulltitle,
                                     show=itm.show,
                                     thumbnails=itm.thumbnails,
                                     url=itm.url,
                                     action='episodios',
                                     contentSeason=season,
                                     contentType='episode',
                                     infoLabels=infoLabels,
                                     filterseason=str(season),
                                     path=item.path))

            support.videolibrary(itemlist, item)
            support.download(itemlist, item)

        elif defp and inspect.stack(0)[1][3] not in ['get_seasons'] and not item.disable_pagination:
            if Pagination and len(itemlist) >= Pagination:
                if inspect.stack(0)[1][3] != 'get_newest':
                    item.title = support.typo(config.get_localized_string(30992), 'color kod bold')
                    item.page = pag + 1
                    item.thumbnail = support.thumb()
                    itemlist.append(item)

        if inspect.stack(0)[1][3] not in ['get_seasons'] and not show_seasons:
            support.videolibrary(itemlist, item)
            support.download(itemlist, item)
    return itemlist


# Find Servers
def findvideos(item):
    # logger.debug('DEBUG', item)
    item.contentTitle = item.fulltitle
    itemlist = []
    json = []
    if 'links' in item.url:
        json = item.url['links']
    elif 'find_links' in item.url:
        for link in item.url['find_links']:
            link['url'] = unshortenit.findlinks(link['url'])
            mimetype = findS = None
            mimetype = mimetypes.MimeTypes().guess_type(link['url'])[0]
            if mimetype is None:
                findS = servertools.get_server_from_url(link['url'])
            if mimetype is None and findS is None:
                data = support.match(link['url']).data
                itemlist_url = servertools.find_video_items(data=data)
                if len(itemlist_url):
                    for item_url in itemlist_url:
                        valid = True
                        patterns = link.get('patterns', False)
                        if patterns:
                            valid = False
                            for pattern in patterns:
                                match = re.search(pattern, item_url.url)
                                if match:
                                    valid = True
                                    break
                        if valid:
                            json.append({"url": item_url.url})
            else:
                json.append(link)

    else:
        url = item.url
        item.url = {}
        json.append({"url": url})

    # support.dbg()
    for option in json:
        extra = set_extra_values(item, option, item.path)
        itemlist.append(
            item.clone(url=option['url'],
                       action='play',
                       quality=extra.quality,
                       subtitle=extra.subtitle,
                       contentLanguage=extra.language,
                       extraInfo=extra.info))

    videolibrary = item.url.get('videolibrary', True)
    item.autoplay = item.url.get('autoplay', False)

    item.url = ''  # do not pass referer
    return support.server(item, itemlist=itemlist, Videolibrary=videolibrary)


################################   Menu   ################################

def get_menu(item, json, key, itemlist=[]):
    json = json[key]
    for option in json:
        title = option['title'] if 'title' in option else json[option] if 'search' not in option else ''
        extra = set_extra_values(item, option, item.path)
        level2 = option if 'level2' in option else []
        it = Item(channel=item.channel,
                  title=support.typo(title, 'bullet bold'),
                  fulltitle=title,
                  show=title,
                  url=extra.url,
                  path=item.path,
                  thumbnail=extra.thumb,
                  fanart=extra.fanart,
                  plot=extra.plot,
                  action='show_menu',
                  menu=level2 if not item.menu else None,
                  filterkey=extra.filterkey,
                  filter=extra.filter)
        if title:
            itemlist.append(it)

        if 'search' in option:
            get_search_menu(it, json, itemlist)

        elif 'submenu' in option:
            get_sub_menu(it, option, 'submenu', itemlist)

    for item in itemlist:
        if not item.thumbnail: support.thumb(item)

    return itemlist


def get_sub_menu(item, json, key, itemlist=[]):
    logger.debug()
    json = json[key]
    search = False
    if item.menu:
        item.menu = None
        itemlist.append(item)
    for option in json:
        title = json[option]['title'] if 'title' in json[option] else json[option] if option != 'search' else ''
        if title:
            extra = set_extra_values(item, json[option], item.path)
            if not extra.url: extra.url = item.url
            filterkey = option
            level2 = option if 'level2' in option else []
            it = Item(channel=item.channel,
                      title=support.typo(title, 'submenu'),
                      fulltitle=title,
                      show=title,
                      url=extra.url,
                      path=item.path,
                      thumbnail=extra.thumb,
                      fanart=extra.fanart,
                      plot=extra.plot,
                      action='show_menu',
                      menu=level2 if not item.menu else None,
                      filterkey=filterkey,
                      description=extra.description)
            itemlist.append(it)

        if 'search' in option:
            search = True
            search_json = json[option]

    if search:
        get_search_menu(item, search_json, itemlist)

    return itemlist


def get_search_menu(item, json='', itemlist=[], channel_name=''):
    logger.debug()
    if 'title' in json:
        title = json['title']
    elif channel_name:
        title = 'Cerca in ' + channel_name + '...'
    else:
        title = 'Cerca ' + item.fulltitle + '...'
    extra = set_extra_values(item, json, item.path)

    itemlist.append(Item(channel=item.channel,
                         title=support.typo(title, 'submenu bold'),
                         fulltitle=title,
                         show=title,
                         thumbnail=extra.thumb,
                         faneart=extra.fanart if extra.fanart else item.fanart,
                         plot=extra.plot,
                         action='search',
                         url=item.url,
                         custom_search=extra.url if extra.url != item.url else '',
                         path=item.path,
                         global_search=True if channel_name else False))

    return itemlist


def submenu(item, json, key, itemlist=[], filter_list=[]):
    logger.debug(item)
    import sys
    if sys.version_info[0] >= 3:
        from concurrent import futures
    else:
        from concurrent_py2 import futures

    if item.description:
        if type(item.description) == dict:
            description = item.description
        else:
            if ':/' in item.description:
                url = item.description
            else:
                url = filetools.join(item.path, item.description)
            description = load_json(url, no_order=True)
    else:
        description = None

    if item.thumb: item.thumbnail = item.thumb

    if not filter_list:
        for option in json[key]:
            if item.filterkey in option and option[item.filterkey]:
                if type(option[item.filterkey]) == str and option[item.filterkey] not in filter_list:
                    filter_list.append(option[item.filterkey])
                elif type(option[item.filterkey]) == list:
                    for f in option[item.filterkey]:
                        if f not in filter_list:
                            filter_list.append(f)

        filter_list.sort()

    Pagination = int(defp) if defp.isdigit() else ''
    pag = item.page if item.page else 1
    filters = []
    for i, filter in enumerate(filter_list):
        if Pagination and (pag - 1) * Pagination > i: continue  # pagination
        if Pagination and i >= pag * Pagination: break
        filters.append(filter)

    with futures.ThreadPoolExecutor() as executor:
        List = [executor.submit(filter_thread, filter, key, item, description) for filter in filters]
        for res in futures.as_completed(List):
            if res.result():
                itemlist.append(res.result())

    if Pagination and len(itemlist) >= Pagination:
        item.title = support.typo(config.get_localized_string(30992), 'color kod bold')
        item.page = pag + 1
        item.thumb = item.thumbnail
        item.thumbnail = support.thumb()
        itemlist.append(item)

    itemlist = sorted(itemlist, key=lambda it: it.title)
    return itemlist


################################   Filter results   ################################

# filter results
def filter_thread(filter, key, item, description):
    thumbnail = plot = fanart = ''
    if item.filterkey in ['actors', 'director']:
        dict_ = {'url': 'search/person', 'language': lang, 'query': filter, 'page': 1}
        tmdb_inf = tmdb.discovery(item, dict_=dict_)
        id = None
        if tmdb_inf.results:
            results = tmdb_inf.results[0]
            id = results['id']
        if id:
            thumbnail = 'https://image.tmdb.org/t/p/original' + results['profile_path'] if results[
                'profile_path'] else item.thumbnail
            json_file = httptools.downloadpage(
                'http://api.themoviedb.org/3/person/' + str(id) + '?api_key=' + tmdb_api + '&language=en',
                use_requests=True).data
            plot += jsontools.load(json_file)['biography']

    if description:
        if filter in description:
            extra = set_extra_values(item, description[filter], item.path)
            thumbnail = extra.thumb if extra.thumb else item.thumbnail
            fanart = extra.fanart if extra.fanart else item.fanart
            plot = extra.plot if extra.plot else item.plot

    item = Item(channel=item.channel,
                title=support.typo(filter, 'bold'),
                url=item.url,
                media_type=item.media_type,
                action='peliculas',
                thumbnail=thumbnail if thumbnail else item.thumbnail,
                fanart=fanart if fanart else item.fanart,
                plot=plot if plot else item.plot,
                path=item.path,
                filterkey=item.filterkey,
                filter=filter,
                sort=item.sort,
                key=key)

    if item.filterkey in ['genre']:
        support.thumb(item)

    return item


################################   Utils   ################################

# for load json from item or url
def load_json(item, no_order=False):
    logger.debug()
    if type(item) == Item:
        url = item.url
        filterkey = item.filterkey
    else:
        url = item['url'] if 'url' in item else item
        filterkey = ''
    try:
        if url.startswith('http'):
            json_file = httptools.downloadpage(url).data
        else:
            json_file = open(url, "r", encoding='utf-8').read()
        if no_order or filterkey:
            json = jsontools.load(json_file)
        else:
            json = jsontools.load(json_file, object_pairs_hook=OrderedDict)

    except:
        json = {}

    return json


# Load Channels json and check that the paths and channel titles are correct
def load_and_check(item):
    logger.debug()
    path = filetools.join(config.get_data_path(), 'community_channels.json')
    file = open(path, "r")
    json = jsontools.load(file.read())

    for key, channel in json['channels'].items():
        if not 'check' in channel:
            response = httptools.downloadpage(channel['path'], follow_redirects=True, timeout=5)
            if response.success:
                channel['url'] = channel['path']
                channel['path'] = response.url
                channel['channel_name'] = re.sub(r'\[[^\]]+\]', '', channel['channel_name'])
                channel['check'] = True

                with open(path, "w") as file:
                    file.write(jsontools.dump(json))
                file.close()
    return json


# set extra values
def set_extra_values(item, json, path):
    logger.debug()
    # support.dbg()
    ret = Item()
    for key in json:
        if key == 'quality':
            ret.quality = json[key]
            if ret.quality and not ret.quality[0].isdigit(): ret.quality = ret.quality.upper()
        elif key == 'language':
            ret.language = json[key].upper()
        elif key == 'plot':
            ret.plot = json[key]
        elif key in ['poster', 'thumbnail']:
            ret.thumb = json[key] if ':/' in json[key] else filetools.join(path, json[key]) if '/' in json[
                key] else get_thumb(json[key])
        elif key == 'fanart':
            ret.fanart = json[key] if ':/' in json[key] else filetools.join(path, json[key])
        elif key in ['url', 'link']:
            ret.url = json[key] if ':/' in json[key] or type(json[key]) in (dict, OrderedDict) else filetools.join(path, json[key])
        elif key == 'seasons_list':
            ret.url = {}
            ret.url['seasons_list'] = json['seasons_list']
        elif key == 'episodes_list':
            ret.url = {}
            ret.url['episodes_list'] = json['episodes_list']
        elif key in ['links', 'find_links']:
            ret.url = {}
            ret.url[key] = json[key]
            ret.url['videolibrary'] = json.get('videolibrary', True)
            ret.url['autoplay'] = json.get('autoplay', False)
        elif key == 'filter':
            filterkey = [k for k in json[key].keys()][0]
            ret.filter = json[key][filterkey]
            ret.filterkey = filterkey
        elif key == 'description':
            ret.description = json[key]
        elif key == 'info':
            ret.info = json[key]
        elif key == 'subtitle':
            ret.subtitle = json[key]

    if not ret.thumb:
        if 'get_search_menu' in inspect.stack(0)[1][3]:
            ret.thumb = get_thumb('search.png')
        else:
            ret.thumb = item.thumbnail
    if not ret.fanart:
        ret.fanart = item.fanart
    if not ret.plot:
        ret.plot = item.plot

    logger.debug(ret.url)
    return ret


# format titles
def set_title(title, language='', quality='', info=''):
    logger.debug()

    t = support.match(title, patron=r'\{([^\}]+)\}').match
    if 'bold' not in t: t += ' bold'
    title = re.sub(r'(\{[^\}]+\})', '', title)
    title = support.typo(title, t)

    if quality:
        title += support.typo(quality, '_ [] color kod bold')
    if language:
        if not isinstance(language, list):
            title += support.typo(language.upper(), '_ [] color kod bold')
        else:
            for lang in language:
                title += support.typo(language.upper(), '_ [] color kod bold')
    if info:
        title += support.typo(info.upper(), '_ [] color kod bold')

    return title


# for relative path
def relative(key, json, path):
    logger.debug()
    ret = ''
    if key in json:
        if key in ['thumbnail', 'poster']:
            ret = json[key] if ':/' in json[key] else filetools.join(path, json[key]) if '/' in json[
                key] else get_thumb(json[key]) if json[key] else ''
        else:
            ret = json[key] if ':/' in json[key] else filetools.join(path, json[key]) if '/' in json[key] else ''

    return ret


def pagination(item, itemlist=[]):
    logger.debug()
    itlist = []

    if not itemlist:
        itemlist = []
        for it in item.itemlist:
            itemlist.append(Item().fromurl(it))
    encoded_itemlist = []
    for it in itemlist:
        encoded_itemlist.append(it.tourl())
    if inspect.stack(0)[1][3] not in ['add_tvshow', 'get_episodes', 'update', 'find_episodes', 'search']:
        Pagination = int(defp) if defp.isdigit() else ''
    else:
        Pagination = ''
    pag = item.page if item.page else 1

    for i, item in enumerate(itemlist):
        if Pagination and (pag - 1) * Pagination > i: continue  # pagination
        if Pagination and i >= pag * Pagination: break  # pagination

        itlist.append(item)

    if Pagination and len(itemlist) >= Pagination:
        if inspect.stack(0)[1][3] != 'get_newest':
            itlist.append(
                Item(channel=item.channel,
                     action='pagination',
                     contentType=item.contentType,
                     title=support.typo(config.get_localized_string(30992), 'color kod bold'),
                     fulltitle=item.fulltitle,
                     show=item.show,
                     url=item.url,
                     args=item.args,
                     page=pag + 1,
                     path=item.path,
                     media_type=item.media_type,
                     thumbnail=support.thumb(),
                     itemlist=encoded_itemlist))
    return itlist


def add_channel(item):
    logger.debug()
    channel_to_add = {}
    json_file = ''
    result = platformtools.dialog_select(config.get_localized_string(70676),
                                         [config.get_localized_string(70678), config.get_localized_string(70679)])
    if result == -1:
        return
    if result == 0:
        file_path = xbmcgui.Dialog().browseSingle(1, config.get_localized_string(70680), 'files')
        try:
            channel_to_add['path'] = file_path
            channel_to_add['url'] = file_path
            json_file = jsontools.load(open(file_path, "r").read())
            channel_to_add['channel_name'] = json_file['channel_name']
        except:
            pass

    elif result == 1:
        url = platformtools.dialog_input("", config.get_localized_string(70681), False)
        try:
            if url[:4] != 'http':
                url = 'http://' + url
            channel_to_add['path'] = url
            json_file = jsontools.load(httptools.downloadpage(url).data)
        except:
            pass

    if len(json_file) == 0:
        return
    if "episodes_list" in json_file:
        platformtools.dialog_ok(config.get_localized_string(20000), config.get_localized_string(70682))
        return
    channel_to_add['channel_name'] = json_file['channel_name']
    if 'thumbnail' in json_file: channel_to_add['thumbnail'] = json_file['thumbnail']
    if 'fanart' in json_file: channel_to_add['fanart'] = json_file['fanart']
    path = filetools.join(config.get_data_path(), 'community_channels.json')

    community_json = open(path, "r")
    community_json = jsontools.load(community_json.read())
    id = 1
    while str(id) in community_json['channels']:
        id += 1
    community_json['channels'][str(id)] = (channel_to_add)

    with open(path, "w") as file:
        file.write(jsontools.dump(community_json))
    file.close()

    platformtools.dialog_notification(config.get_localized_string(20000),
                                      config.get_localized_string(70683) % json_file['channel_name'])
    import xbmc
    xbmc.sleep(1000)
    platformtools.itemlist_refresh()
    return


def remove_channel(item):
    logger.debug()

    path = filetools.join(config.get_data_path(), 'community_channels.json')

    community_json = open(path, "r")
    community_json = jsontools.load(community_json.read())

    id = item.channel_id
    to_delete = community_json['channels'][id]['channel_name']
    del community_json['channels'][id]
    with open(path, "w") as file:
        file.write(jsontools.dump(community_json))
    file.close()

    platformtools.dialog_notification(config.get_localized_string(20000),
                                      config.get_localized_string(70684) % to_delete)
    platformtools.itemlist_refresh()
    return

# -*- coding: utf-8 -*-
# -*- Channel Community -*-

import re, os, inspect, requests, xbmc, xbmcaddon

from core import httptools, scrapertoolsV2, servertools, jsontools, tmdb, support
from core.item import Item
from core.support import typo
from channelselector import get_thumb
from platformcode import  config, platformtools
from specials import autoplay

addon = xbmcaddon.Addon('metadata.themoviedb.org')
lang = addon.getSetting('language')

defpage = ["", "20", "40", "60", "80", "100"]
defp = defpage[config.get_setting('pagination','community')]
show_seasons = config.get_setting('show_seasons','community')

list_data = {}

list_servers = ['directo', 'akvideo', 'verystream', 'openload']
list_quality = ['SD', '720', '1080', '4k']

tmdb_api = 'a1ab8b8669da03637a4b98fa39c39228'


def mainlist(item):
    support.log()

    path = os.path.join(config.get_data_path(), 'community_channels.json')
    if not os.path.exists(path):
        with open(path, "w") as file:
            file.write('{"channels":{}}')
            file.close()
    autoplay.init(item.channel, list_servers, list_quality)

    return show_channels(item)


def show_channels(item):
    support.log()
    itemlist = []

    context = [{"title": config.get_localized_string(50005),
                "action": "remove_channel",
                "channel": "community"}]

    path = os.path.join(config.get_data_path(), 'community_channels.json')
    file = open(path, "r")
    json = jsontools.load(file.read())

    itemlist.append(Item(channel=item.channel,
                         title=typo(config.get_localized_string(70676),'bold color kod'),
                         action='add_channel',
                         thumbnail=get_thumb('add.png')))

    for key, channel in json['channels'].items():
        # Find File Path
        if 'http' in channel['path']: file_path = httptools.downloadpage(channel['path'],follow_redirects=True).url
        else: file_path = channel['path']

        # make relative path
        path = os.path.dirname(os.path.abspath(file_path))
        if 'http' in path: path = path[path.find('http'):].replace('\\','/').replace(':/','://')
        if file_path.startswith('http'): file_url = httptools.downloadpage(file_path, follow_redirects=True).data
        else: file_url = open(file_path, "r").read()

        # load json
        json_url = jsontools.load(file_url)

        thumbnail = relative('thumbnail', json_url, path)
        fanart = relative('fanart', json_url, path)
        plot = json_url['plot'] if json_url.has_key('plot') else ''

        itemlist.append(Item(channel=item.channel,
                             title=typo(channel['channel_name'],'bold'),
                             url=file_path,
                             thumbnail=thumbnail,
                             fanart=fanart,
                             plot=plot,
                             action='show_menu',
                             channel_id = key,
                             context=context,
                             path=path))

    autoplay.show_option(item.channel, itemlist)
    support.channel_config(item, itemlist)
    return itemlist


def show_menu(item):
    global list_data
    itemlist = []
    support.log()

    # If Second Level Menu
    if item.menu:
        menu = item.menu
        item.menu = None
        itemlist.append(item)
        for key in menu:
            if key != 'search':
                if type(menu[key]) == dict:
                    title = menu[key]['title'] if menu[key].has_key('title') else item.title
                    thumbnail = relative('thumbnail', menu[key], item.path)
                    plot = menu[key]['plot'] if menu[key].has_key('plot') else ''
                else:
                    title = menu[key]
                    thumbnail = item.thumbnail
                    plot = ''

                itemlist.append(Item(channel=item.channel,
                                    title=typo(title,'submenu'),
                                    url=item.url,
                                    path=item.path,
                                    thumbnail=thumbnail,
                                    plot=plot,
                                    action='submenu',
                                    filterkey=key))

        if menu.has_key('search'):
            itemlist.append(Item(channel=item.channel,
                                    title=typo('Cerca ' + item.fulltitle +'...','color kod bold'),
                                    thumbnail=get_thumb('search.png'),
                                    action='search',
                                    url=item.url,
                                    path=item.path))
        return itemlist

    else:
        json_data = load_json(item)

        if "menu" in json_data:
            for option in json_data['menu']:
                thumbnail = relative('thumbnail', option, item.path)
                fanart = relative('fanart', option, item.path)
                plot = option['plot'] if option.has_key('plot') else item.plot
                url = relative('link', option, item.path)
                submenu = option['submenu'] if option.has_key('submenu') else []
                level2 = option['level2'] if option.has_key('level2') else []
                itemlist.append(Item(channel=item.channel,
                                     title=format_title(option['title']),
                                     fulltitle=option['title'],
                                     thumbnail=thumbnail,
                                     fanart=fanart,
                                     plot=plot,
                                     action='show_menu',
                                     url=url,
                                     path=item.path,
                                     menu=level2))

                if submenu:
                    for key in submenu:
                        if key != 'search':
                            if type(submenu[key]) == dict:
                                title = submenu[key]['title'] if submenu[key].has_key('title') else item.title
                                thumbnail = relative('thumbnail', submenu[key], item.path)
                                plot = submenu[key]['plot'] if submenu[key].has_key('plot') else ''
                            else:
                                title = submenu[key]
                                thumbnail = item.thumbnail
                                plot = ''

                            itemlist.append(Item(channel=item.channel,
                                                title=typo(title,'submenu'),
                                                url=url,
                                                path=item.path,
                                                thumbnail=thumbnail,
                                                plot=plot,
                                                action='submenu',
                                                filterkey=key))
                    if submenu.has_key('search'):
                        itemlist.append(Item(channel=item.channel,
                                            title=typo('Cerca ' + option['title'] +'...','color kod bold'),
                                            thumbnail=get_thumb('search.png'),
                                            action='search',
                                            url=url,
                                            path=item.path))
            # add Search
            itemlist.append(Item(channel=item.channel,
                                title=typo('Cerca nel Canale...','color kod bold'),
                                thumbnail=get_thumb('search.png'),
                                action='search',
                                url=item.url,
                                path=item.path))

            return itemlist

        # select type of list
        if json_data.has_key("movies_list"):
            item.media_type = 'movies_list'
            item.contentType = 'movie'
        elif json_data.has_key("tvshows_list"):
            item.media_type = 'tvshows_list'
            item.contentType = 'tvshow'
        elif json_data.has_key("episodes_list"):
            item.media_type = 'episodes_list'
            item.contentType = 'episode'
        elif json_data.has_key("generic_list"):
            item.media_type= 'generic_list'

    return list_all(item)


def submenu(item):
    support.log()

    itemlist = []
    filter_list = []
    plot = item.plot

    json_data = load_json(item)
    if json_data.has_key("movies_list"): item.media_type= 'movies_list'
    elif json_data.has_key("tvshows_list"): item.media_type = 'tvshows_list'
    elif json_data.has_key("episodes_list"): item.media_type = 'episodes_list'
    elif json_data.has_key("generic_list"): item.media_type= 'generic_list'
    media_type = item.media_type

    for media in json_data[media_type]:
        if media.has_key(item.filterkey):
            if type(media[item.filterkey]) == str and media[item.filterkey] not in filter_list:
                filter_list.append(media[item.filterkey])
            elif type(media[item.filterkey]) == list:
                for f in media[item.filterkey]:
                    if f not in filter_list:
                        filter_list.append(f)
    filter_list.sort()

    for filter in filter_list:
        if item.filterkey in ['director','actors']:
            load_info = load_json('http://api.themoviedb.org/3/search/person/?api_key=' + tmdb_api + '&language=' + lang + '&query=' + filter)
            if load_info:
                id = str(load_info['results'][0]['id'])
            if id:
                info = load_json('http://api.themoviedb.org/3/person/'+ id + '?api_key=' + tmdb_api + '&language=' + lang)
            if not info['biography']:
                bio = load_json('http://api.themoviedb.org/3/person/'+ id + '?api_key=' + tmdb_api + '&language=en')['biography']
            thumbnail = 'https://image.tmdb.org/t/p/w600_and_h900_bestv2' + info['profile_path'] if info['profile_path'] else item.thumbnail
            plot += info['biography'] if info['biography'] else bio if bio else ''

        itemlist.append(Item(channel=item.channel,
                             title=typo(filter, 'bold'),
                             url=item.url,
                             media_type=item.media_type,
                             action='list_filtered',
                             thumbnail=thumbnail,
                             plot=plot,
                             filterkey=item.filterkey,
                             filter=filter))
    return itemlist


def list_all(item):
    support.log('CONTENT TYPE ', item.contentType)

    if inspect.stack()[1][3] not in ['add_tvshow', 'get_episodes', 'update', 'find_episodes']:
        pagination = int(defp) if defp.isdigit() else ''
    else: pagination = ''
    pag = item.page if item.page else 1

    itemlist = []
    media_type = item.media_type
    json_data = load_json(item)
    contentTitle = contentSerieName = ''
    infoLabels = item.infoLabels if item.infoLabels else {}

    if json_data:
        for i, media in enumerate(json_data[media_type]):
            if pagination and (pag - 1) * pagination > i: continue  # pagination
            if pagination and i >= pag * pagination: break          # pagination

            quality, language, plot, poster = set_extra_values(media, item.path)

            fulltitle = media['title']
            title = set_title(fulltitle, language, quality)

            infoLabels['year'] = media['year'] if media.has_key('year')else ''
            infoLabels['tmdb_id'] = media['tmdb_id'] if media.has_key('tmdb_id') else ''

            if 'movies_list' in json_data or 'generic_list' in json_data:
                url= media
                contentTitle = fulltitle
                contentType = 'movie'
                action='findvideos'

            else:
                contentSerieName = fulltitle
                contentType = 'tvshow'
                if media.has_key('seasons_list'):
                    url = media['seasons_list']
                    action = 'get_seasons'
                else:
                    url = relative('link', media, item.path)
                    action = 'episodios'

            itemlist.append(Item(channel=item.channel,
                                 contentType=contentType,
                                 title=format_title(title),
                                 fulltitle=fulltitle,
                                 show=fulltitle,
                                 quality=quality,
                                 language=language,
                                 plot=plot,
                                 personal_plot=plot,
                                 thumbnail=poster,
                                 path=item.path,
                                 url=url,
                                 contentTitle=contentTitle,
                                 contentSerieName=contentSerieName,
                                 infoLabels=infoLabels,
                                 action=action))
        if pagination and len(json_data[media_type]) >= pag * pagination:
            if inspect.stack()[1][3] != 'get_newest':
                itemlist.append(
                    Item(channel=item.channel,
                            action = item.action,
                            contentType=contentType,
                            title=typo(config.get_localized_string(30992), 'color kod bold'),
                            fulltitle= item.fulltitle,
                            show= item.show,
                            url=item.url,
                            args=item.args,
                            page=pag + 1,
                            thumbnail=support.thumb()))

        if not 'generic_list' in json_data:
            tmdb.set_infoLabels(itemlist, seekTmdb=True)
            for item in itemlist:
                if item.personal_plot != item.plot and item.personal_plot:
                    item.plot = '\n\n' + typo('','submenu') + '\n' + item.personal_plot + '\n' + typo('','submenu') + '\n\n' + item.plot
        return itemlist


def list_filtered(item):
    support.log()

    if inspect.stack()[1][3] not in ['add_tvshow', 'get_episodes', 'update', 'find_episodes']:
        pagination = int(defp) if defp.isdigit() else ''
    else: pagination = ''
    pag = item.page if item.page else 1

    itemlist = []
    media_type = item.media_type
    json_data = load_json(item)
    contentTitle = contentSerieName = ''
    infoLabels = item.infoLabels if item.infoLabels else {}

    if json_data:
        for i, media in enumerate(json_data[media_type]):
            if pagination and (pag - 1) * pagination > i: continue  # pagination
            if pagination and i >= pag * pagination: break          # pagination
            if media.has_key(item.filterkey):
                filter_keys = [it.lower() for it in media[item.filterkey]] if type(media[item.filterkey]) == list else media[item.filterkey].lower()
                if item.filter.lower() in filter_keys:

                    quality, language, plot, poster = set_extra_values(media, item.path)

                    fulltitle = media['title']
                    title = set_title(fulltitle, language, quality)

                    infoLabels['year'] = media['year'] if media.has_key('year')else ''
                    infoLabels['tmdb_id'] = media['tmdb_id'] if media.has_key('tmdb_id') else ''

                    if 'movies_list' in json_data or 'generic_list' in json_data:
                        url= media
                        contentTitle = fulltitle
                        contentType = 'movie'
                        action='findvideos'

                    else:
                        contentSerieName = fulltitle
                        contentType = 'tvshow'
                        if media.has_key('seasons_list'):
                            url = media['seasons_list']
                            action = 'get_seasons'
                        else:
                            url = relative('link', media, item.path)
                            action = 'episodios'

                    itemlist.append(Item(channel=item.channel,
                                        contentType=contentType,
                                        title=format_title(title),
                                        fulltitle=fulltitle,
                                        show=fulltitle,
                                        quality=quality,
                                        language=language,
                                        plot=plot,
                                        personal_plot=plot,
                                        thumbnail=poster,
                                        path=item.path,
                                        url=url,
                                        contentTitle=contentTitle,
                                        contentSerieName=contentSerieName,
                                        infoLabels=infoLabels,
                                        action=action))

        if pagination and len(json_data[media_type]) >= pag * pagination and len(itemlist) >= pag * pagination:
            if inspect.stack()[1][3] != 'get_newest':
                itemlist.append(
                    Item(channel=item.channel,
                            action = item.action,
                            contentType=contentType,
                            title=typo(config.get_localized_string(30992), 'color kod bold'),
                            fulltitle= item.fulltitle,
                            show= item.show,
                            url=item.url,
                            args=item.args,
                            page=pag + 1,
                            thumbnail=support.thumb()))

        if not 'generic_list' in json_data:
            tmdb.set_infoLabels(itemlist, seekTmdb=True)
        for item in itemlist:
            if item.personal_plot != item.plot and item.personal_plot:
                item.plot = '\n\n' + typo('','submenu') + '\n' + item.personal_plot + '\n' + typo('','submenu') + '\n\n' + item.plot
    return itemlist


def get_seasons(item):
    itm = item
    support.log()
    itemlist = []
    infoLabels = item.infoLabels if item.infolabels else {}
    list_seasons = item.url

    for season in list_seasons:
        infoLabels['season'] = season['season']
        title = config.get_localized_string(60027) % season['season']
        url = relative('link', season, item.path)

        itemlist.append(Item(channel=item.channel,
                             title=format_title(title),
                             fulltitle=item.fulltitle,
                             show=item.show,
                             thumbnails=item.thumbnails,
                             url=url,
                             action='episodios',
                             contentSeason=season['season'],
                             infoLabels=infoLabels,
                             contentType='tvshow'))


    if inspect.stack()[1][3] in ['add_tvshow', "get_seasons"] or show_seasons == False:
        it = []
        for item in itemlist:
            if os.path.isfile(item.url): it += episodios(item)
        itemlist = it

        if inspect.stack()[1][3] not in ['add_tvshow', 'get_episodes', 'update', 'find_episodes', 'get_newest']:
            pagination = int(defp) if defp.isdigit() else ''
            pag = itm.page if itm.page else 1
            it = []
            for i, item in enumerate(itemlist):
                if pagination and (pag - 1) * pagination > i: continue  # pagination
                if pagination and i >= pag * pagination: break          # pagination
                it.append(item)

            if pagination and len(itemlist) >= pag * pagination:
                itm.page = pag + 1
                itm.title=typo(config.get_localized_string(30992), 'color kod bold')
                itm.thumbnail=support.thumb()
                it.append(itm)
            itemlist = it
    else:
        tmdb.set_infoLabels(itemlist, seekTmdb=True)
        itemlist = sorted(itemlist, key=lambda i: i.title)
        support.videolibrary(itemlist,item)

    return itemlist


def episodios(item):
    # support.dbg()
    support.log()
    itm = item

    if inspect.stack()[1][3] not in ['add_tvshow', 'get_episodes', 'update', 'find_episodes']:
        pagination = int(defp) if defp.isdigit() else ''
    else: pagination = ''
    pag = item.page if item.page else 1

    itemlist = []
    json_data = load_json(item)
    infoLabels = item.infoLabels
    ep = 1
    season = infoLabels['season'] if infoLabels.has_key('season') else item.contentSeason if item.contentSeason else 1

    for i, episode in enumerate(json_data['episodes_list']):
        if pagination and (pag - 1) * pagination > i: continue  # pagination
        if pagination and i >= pag * pagination: break          # pagination
        match = []
        if episode.has_key('number'):
            match = support.match(episode['number'], r'(?P<season>\d+)x(?P<episode>\d+)')[0]
            if match:
                match = match[0]
        if not match and episode.has_key('title'):
            match = support.match(episode['title'], r'(?P<season>\d+)x(?P<episode>\d+)')[0]
            if match: match = match[0]
        if match:
            episode_number = match[1]
            ep = int(match[1]) + 1
            season_number = match[0]
        else:
            season_number = episode['season'] if episode.has_key('season') else season if season else 1
            episode_number = episode['number'] if episode.has_key('number') else ''
            if not episode_number.isdigit():
                episode_number = support.match(episode['title'], r'(?P<episode>\d+)')[0][0]
            ep = int(episode_number) if episode_number else ep
            if not episode_number:
                episode_number = str(ep).zfill(2)
                ep += 1

        infoLabels['season'] = season_number
        infoLabels['episode'] = episode_number

        plot = episode['plot'] if episode.has_key('plot') else item.plot
        thumbnail = episode['poster'] if episode.has_key('poster') else episode['thumbnail'] if episode.has_key('thumbnail') else item.thumbnail

        title = ' - ' + episode['title'] if episode.has_key('title') else ''
        title = '%sx%s%s' % (season_number, episode_number, title)
        if season_number == item.filter or not item.filterseason:
            itemlist.append(Item(channel= item.channel,
                                title= format_title(title),
                                fulltitle = item.fulltitle,
                                show = item.show,
                                url= episode,
                                action= 'findvideos',
                                plot= plot,
                                thumbnail= thumbnail,
                                contentSeason= season_number,
                                contentEpisode= episode_number,
                                infoLabels= infoLabels,
                                contentType= 'episode'))


    if show_seasons == True and inspect.stack()[1][3] not in ['add_tvshow', 'get_episodes', 'update', 'find_episodes'] and not item.filterseason:
        itm.contentType='season'
        season_list = []
        for item in itemlist:
            if item.contentSeason not in season_list:
                season_list.append(item.contentSeason)
        itemlist = []
        for season in season_list:
            itemlist.append(Item(channel=item.channel,
                                 title=format_title(config.get_localized_string(60027) % season),
                                 fulltitle=itm.fulltitle,
                                 show=itm.show,
                                 thumbnails=itm.thumbnails,
                                 url=itm.url,
                                 action='episodios',
                                 contentSeason=season,
                                 infoLabels=infoLabels,
                                 filterseason=season))

    elif pagination and len(json_data['episodes_list']) >= pag * pagination:
        if inspect.stack()[1][3] != 'get_newest':
            itemlist.append(
                Item(channel=item.channel,
                     action = item.action,
                     contentType='episode',
                     title=typo(config.get_localized_string(30992), 'color kod bold'),
                     fulltitle= item.fulltitle,
                     show= item.show,
                     url=item.url,
                     args=item.args,
                     page=pag + 1,
                     thumbnail=support.thumb()))

    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    return itemlist


def findvideos(item):
    support.log()
    itemlist = []
    if 'links' in item.url:
        for url in item.url['links']:
            quality, language, plot, poster = set_extra_values(url, item.path)
            title = ''
            title = set_title(title, language, quality)

            itemlist.append(Item(channel=item.channel, title=format_title('%s'+title), url=url['url'], action='play', quality=quality,
                                language=language, infoLabels = item.infoLabels))

        itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())

        if inspect.stack()[2][3] != 'start_download':
            autoplay.start(itemlist, item)

        return itemlist


def add_channel(item):
    support.log()
    import xbmc
    import xbmcgui
    channel_to_add = {}
    json_file = ''
    result = platformtools.dialog_select(config.get_localized_string(70676), [config.get_localized_string(70678), config.get_localized_string(70679)])
    if result == -1:
        return
    if result==0:
        file_path = xbmcgui.Dialog().browseSingle(1, config.get_localized_string(70680), 'files')
        try:
            channel_to_add['path'] = file_path
            json_file = jsontools.load(open(file_path, "r").read())
            channel_to_add['channel_name'] = json_file['channel_name']
        except:
            pass

    elif result==1:
        url = platformtools.dialog_input("", config.get_localized_string(70681), False)
        try:
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
    
    if json_file.has_key('thumbnail'):
        channel_to_add['thumbnail'] = json_file['thumbnail']
    else:
        channel_to_add['thumbnail'] = ''

    if json_file.has_key('fanart'):
        channel_to_add['fanart'] = json_file['fanart']
    else:
        channel_to_add['fanart'] = ''
    
    path = os.path.join(config.get_data_path(), 'community_channels.json')

    community_json = open(path, "r")
    community_json = jsontools.load(community_json.read())
    id = len(community_json['channels']) + 1
    community_json['channels'][id]=(channel_to_add)

    with open(path, "w") as file:
         file.write(jsontools.dump(community_json))
    file.close()

    platformtools.dialog_notification(config.get_localized_string(20000), config.get_localized_string(70683) % json_file['channel_name'])
    return


def remove_channel(item):
    support.log()
    import xbmc
    import xbmcgui
    path = os.path.join(config.get_data_path(), 'community_channels.json')

    community_json = open(path, "r")
    community_json = jsontools.load(community_json.read())

    id = item.channel_id
    to_delete = community_json['channels'][id]['channel_name']
    del community_json['channels'][id]
    with open(path, "w") as file:
         file.write(jsontools.dump(community_json))
    file.close()

    platformtools.dialog_notification(config.get_localized_string(20000), config.get_localized_string(70684) % to_delete)
    platformtools.itemlist_refresh()
    return


def set_extra_values(dict, path):
    support.log()
    quality = ''
    language = ''
    plot = ''
    poster = ''

    if 'quality' in dict and dict['quality'] != '':
        quality = dict['quality'].upper()
    if 'language' in dict and dict['language'] != '':
        language = dict['language'].upper()
    if 'plot' in dict and dict['plot'] != '':
        plot = dict['plot']
    if 'poster' in dict and dict['poster'] != '':
        poster = dict['poster']if ':/' in dict['poster'] else path + dict['poster'] if '/' in dict['poster'] else ''
    elif 'thumbnail' in dict and dict['thumbnail'] != '':
        poster = dict['thumbnail']if ':/' in dict['thumbnail'] else path + dict['thumbnail'] if '/' in dict['thumbnail'] else ''

    return quality, language, plot, poster

def set_title(title, language, quality):
    support.log()

    if not config.get_setting('unify'):
        if quality != '':
            title += typo(quality, '_ [] color kod')
        if language != '':
            if not isinstance(language, list):
                title += typo(language.upper(), '_ [] color kod')
            else:
                for lang in language:
                    title += typo(lang.upper(), '_ [] color kod')

    return title


def format_title(title):
    t = scrapertoolsV2.find_single_match(title, r'\{([^\}]+)\}')
    if 'bold' not in t: t += ' bold'
    title = re.sub(r'(\{[^\}]+\})','',title)
    return typo(title,t)


def search(item, text):
    support.log('Search ', text)
    itemlist = []
    json_data = load_json(item)

    return load_links(item, itemlist, json_data, text)


def load_links(item, itemlist, json_data, text):
    support.log()

    def links(item, itemlist, json_data, text):
        support.log()
        if "movies_list" in json_data: media_type= 'movies_list'
        elif "tvshows_list" in json_data: media_type = 'tvshows_list'
        elif "episodes_list" in json_data: media_type = 'episodes_list'
        if "generic_list" in json_data: media_type= 'generic_list'

        if json_data:
            for media in json_data[media_type]:
                if text.lower() in media['title'].lower():
                    quality, language, plot, poster = set_extra_values(media, item.path)

                    title = media['title']
                    title = set_title(title, language, quality)

                    new_item = Item(channel=item.channel, title=format_title(title), quality=quality,
                                    language=language, plot=plot, personal_plot=plot, thumbnail=poster, path=item.path)

                    new_item.infoLabels['year'] = media['year'] if 'year' in media else ''
                    new_item.infoLabels['tmdb_id'] = media['tmdb_id'] if 'tmdb_id' in media else ''

                    if 'movies_list' in json_data or 'generic_list' in json_data:
                        new_item.url = media
                        new_item.contentTitle = media['title']
                        new_item.action = 'findvideos'
                    else:
                        new_item.url = media['seasons_list']
                        new_item.contentSerieName = media['title']
                        new_item.action = 'seasons'

                    itemlist.append(new_item)

                    if not 'generic_list' in json_data:
                        tmdb.set_infoLabels(itemlist, seekTmdb=True)
                        for item in itemlist:
                            if item.personal_plot != item.plot and item.personal_plot:
                                item.plot = '\n\n' + typo('','submenu') + '\n' + item.personal_plot + '\n' + typo('','submenu') + '\n\n' + item.plot

    if json_data.has_key('menu'):
        for option in json_data['menu']:
            json_data = load_json(option['link'] if option['link'].startswith('http') else item.path+option['link'])
            load_links(item, itemlist, json_data, text)
    else:
        links(item, itemlist, json_data, text)

    return itemlist


def relative(key, json, path):
    if json.has_key(key):
        if key == 'thumbnail':
            ret = json[key] if ':/' in json[key] else path + json[key] if '/' in json[key] else get_thumb(json[key]) if json[key] else ''
        else:
            ret = json[key] if ':/' in json[key] else path + json[key] if '/' in json[key]  else ''
    else:
        ret = ''
    return ret


def load_json(item):
    support.log()
    url= item if type(item) == str else item.url
    try:
        if url.startswith('http'):
            json_file = httptools.downloadpage(url).data
        else:
            json_file = open(url, "r").read()

        json_data = jsontools.load(json_file)

    except:
        json_data = {}

    return json_data

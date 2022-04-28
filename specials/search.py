# -*- coding: utf-8 -*-
# -*- Channel New Search -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

from __future__ import division
from builtins import range
from past.utils import old_div
#from builtins import str
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import os, json, time, inspect, channelselector

if PY3:
    from concurrent import futures
else:
    from concurrent_py2 import futures
from core.item import Item
from core import tmdb, scrapertools, channeltools, filetools, jsontools, servertools
from channelselector import get_thumb
from platformcode import logger, config, platformtools, unify
from core.support import typo, thumb
import xbmcgui
import xbmc
from threading import Thread
from core.support import dbg

info_language = ["de", "en", "es", "fr", "it", "pt"] # from videolibrary.json
def_lang = info_language[config.get_setting("info_language", "videolibrary")]


def mainlist(item):
    logger.debug()

    if platformtools.get_window() not in ('WINDOW_SETTINGS_MENU', 'WINDOW_SETTINGS_INTERFACE', 'WINDOW_SKIN_SETTINGS')\
            and xbmc.getInfoLabel('System.CurrentWindow') in ('Home', '') and config.get_setting('new_search'):
        itemlist = [Item(channel='globalsearch', title=config.get_localized_string(70276), action='Search', mode='all', thumbnail=get_thumb("search.png"), folder=False),
                    Item(channel='globalsearch', title=config.get_localized_string(70741) % config.get_localized_string(30122), action='Search', mode='movie', type='movie', thumbnail=get_thumb("search_movie.png"),folder=False),
                    Item(channel='globalsearch', title=config.get_localized_string(70741) % config.get_localized_string(30123), action='Search', mode='tvshow', type='tvshow',thumbnail=get_thumb("search_tvshow.png"), folder=False),
                    Item(channel='globalsearch', title=config.get_localized_string(70741) % config.get_localized_string(70314), action='Search', page=1, mode='person', thumbnail=get_thumb("search_star.png"), folder=False)]
    else:
        itemlist = [Item(channel=item.channel, title=config.get_localized_string(70276), action='new_search', mode='all', thumbnail=get_thumb("search.png")),
                    Item(channel=item.channel, title=config.get_localized_string(70741) % config.get_localized_string(30122), action='new_search', mode='movie', thumbnail=get_thumb("search_movie.png")),
                    Item(channel=item.channel, title=config.get_localized_string(70741) % config.get_localized_string(30123), action='new_search', mode='tvshow', thumbnail=get_thumb("search_tvshow.png")),
                    Item(channel=item.channel, title=config.get_localized_string(70741) % config.get_localized_string(70314), action='new_search', page=1, mode='person', thumbnail=get_thumb("search_star.png"))]

    itemlist += [Item(channel=item.channel, title=config.get_localized_string(59995), action='saved_search', thumbnail=get_thumb('search.png')),
                Item(channel=item.channel, title=config.get_localized_string(60420), action='sub_menu', thumbnail=get_thumb('search.png')),
                Item(channel="tvmoviedb", title=config.get_localized_string(70274), action="mainlist", thumbnail=get_thumb("search.png")),
                Item(channel=item.channel, title=typo(config.get_localized_string(59994), 'color kod bold'), action='setting_channel_new', thumbnail=get_thumb('setting_0.png'),folder=False),
                Item(channel='shortcuts', title=typo(config.get_localized_string(70286), 'color kod bold'), action='SettingOnPosition', category=5, setting=1, thumbnail=get_thumb('setting_0.png'),folder=False)]

    itemlist = set_context(itemlist)
    return itemlist


def sub_menu(item):
    logger.debug()

    itemlist = [Item(channel=item.channel, action='genres_menu', title=config.get_localized_string(70306), mode='movie', thumbnail=get_thumb("movie_genre.png")),
                Item(channel=item.channel, action='years_menu', title=config.get_localized_string(70742), mode='movie', thumbnail=get_thumb("movie_year.png")),
                Item(channel=item.channel, action='discover_list', title=config.get_localized_string(70307), search_type='list', list_type='movie/popular', mode='movie', thumbnail=get_thumb("movie_popular.png")),
                Item(channel=item.channel, action='discover_list', title=config.get_localized_string(70308), search_type='list', list_type='movie/top_rated', mode='movie', thumbnail=get_thumb("movie_top.png")),
                Item(channel=item.channel, action='discover_list', title=config.get_localized_string(70309), search_type='list', list_type='movie/now_playing', mode='movie', thumbnail=get_thumb("movie_now_playing.png")),
                Item(channel=item.channel, action='genres_menu', title=config.get_localized_string(70310), mode='tvshow', thumbnail=get_thumb("tvshow_genre.png")),
                Item(channel=item.channel, action='years_menu', title=config.get_localized_string(70743), mode='tvshow', thumbnail=get_thumb("tvshow_year.png")),
                Item(channel=item.channel, action='discover_list', title=config.get_localized_string(70311), search_type='list', list_type='tv/popular', mode='tvshow', thumbnail=get_thumb("popular.png")),
                Item(channel=item.channel, action='discover_list', title=config.get_localized_string(70312), search_type='list', list_type='tv/on_the_air', mode='tvshow', thumbnail=get_thumb("tvshow_on_the_air.png")),
                Item(channel=item.channel, action='discover_list', title=config.get_localized_string(70313), search_type='list', list_type='tv/top_rated', mode='tvshow', thumbnail=get_thumb("tvshow_top.png")),]

    itemlist = set_context(itemlist)
    return itemlist


def saved_search(item):
    logger.debug()

    itemlist = get_saved_searches()

    if len(itemlist) > 0:
        itemlist.append(
            Item(channel=item.channel,
                 action="clear_saved_searches",
                 title=typo(config.get_localized_string(60417), 'color kod bold'),
                 thumbnail=get_thumb('search.png')))

    itemlist = set_context(itemlist)
    return itemlist


def new_search(item):
    logger.debug()

    temp_search_file = config.get_temp_file('temp-search')
    if filetools.isfile(temp_search_file):
        filetools.remove(temp_search_file)

    itemlist = []
    if config.get_setting('last_search'):
        last_search = channeltools.get_channel_setting('Last_searched', 'search', '')
    else:
        last_search = ''

    if item.search_text:
        searched_text = item.search_text
    else:
        searched_text = platformtools.dialog_input(default=last_search, heading='')

    save_search(searched_text)
    if not searched_text:
        return

    channeltools.set_channel_setting('Last_searched', searched_text, 'search')
    searched_text = searched_text.replace("+", " ")

    if item.mode == 'person':
        item.searched_text = searched_text
        return actor_list(item)

    if item.mode != 'all':
        tmdb_info = tmdb.Tmdb(searched_text=searched_text, search_type=item.mode.replace('show', ''))
        results = tmdb_info.results
        for result in results:
            result = tmdb_info.get_infoLabels(result, origen=result)
            if item.mode == 'movie':
                title = result['title']
            else:
                title = result['name']
                item.mode = 'tvshow'

            thumbnail = result.get('thumbnail', '')
            fanart = result.get('fanart', '')

            new_item = Item(channel=item.channel,
                            action='channel_search',
                            title=title,
                            text=searched_text,
                            thumbnail=thumbnail,
                            fanart=fanart,
                            mode=item.mode,
                            contentType=item.mode,
                            infoLabels=result)

            if item.mode == 'movie':
                new_item.contentTitle = result['title']
            else:
                new_item.contentSerieName = result['name']

            itemlist.append(new_item)

    if item.mode == 'all' or not itemlist:
        return channel_search(Item(channel=item.channel,
                                   title=searched_text,
                                   text=searched_text,
                                   mode='all',
                                   infoLabels={}))

    return itemlist


def channel_search(item):
    logger.debug(item)

    start = time.time()
    searching = list()
    searching_titles = list()
    results = list()
    valid = list()
    ch_list = dict()
    mode = item.mode

    if item.infoLabels['tvshowtitle']:
        item.text = item.infoLabels['tvshowtitle'].split(' - ')[0]
        item.title = item.text
    elif item.infoLabels['title']:
        item.text = item.infoLabels['title'].split(' - ')[0]
        item.title = item.text

    temp_search_file = config.get_temp_file('temp-search')
    if filetools.isfile(temp_search_file):
        itemlist = []
        f = filetools.read(temp_search_file)
        if f.startswith(item.text):
            for it in f.split(','):
                if it and it != item.text:
                    itemlist.append(Item().fromurl(it))
            return itemlist
        else:
            filetools.remove(temp_search_file)

    searched_id = item.infoLabels['tmdb_id']

    channel_list, channel_titles = get_channels(item)

    searching += channel_list
    searching_titles += channel_titles
    cnt = 0
    progress = platformtools.dialog_progress(config.get_localized_string(30993) % item.title, config.get_localized_string(70744) % len(channel_list) + '\n' + ', '.join(searching_titles))
    config.set_setting('tmdb_active', False)
    search_action_list = []
    module_dict = {}
    for ch in channel_list:
        try:
            module = __import__('channels.%s' % ch, fromlist=["channels.%s" % ch])
            mainlist = getattr(module, 'mainlist')(Item(channel=ch, global_search=True))

            module_dict[ch] = module
            search_action_list.extend([elem for elem in mainlist if
                             elem.action == "search" and (mode == 'all' or elem.contentType in [mode, 'undefined'])])
            if progress.iscanceled():
                return []
        except:
            import traceback
            logger.error('error importing/getting search items of ' + ch)
            logger.error(traceback.format_exc())

    total_search_actions = len(search_action_list)
    with futures.ThreadPoolExecutor(max_workers=set_workers()) as executor:
        c_results = []
        for search_action in search_action_list:
            c_results.append(executor.submit(get_channel_results, item, module_dict, search_action))
            if progress.iscanceled():
                break

        for res in futures.as_completed(c_results):
            search_action = res.result()[0]
            channel = search_action.channel
            if res.result()[1]:
                if channel not in ch_list:
                    ch_list[channel] = []
                ch_list[channel].extend(res.result()[1])
            if res.result()[2]:
                valid.extend(res.result()[2])

            if progress.iscanceled():
                break

            search_action_list.remove(search_action)
            # if no action of this channel remains
            for it in search_action_list:
                if it.channel == channel:
                    break
            else:
                cnt += 1
                searching_titles.remove(searching_titles[searching.index(channel)])
                searching.remove(channel)
                progress.update(old_div(((total_search_actions - len(search_action_list)) * 100), total_search_actions), config.get_localized_string(70744) % str(len(channel_list) - cnt) + '\n' + ', '.join(searching_titles))

    progress.close()

    cnt = 0
    progress = platformtools.dialog_progress(config.get_localized_string(30993) % item.title, config.get_localized_string(60295) + '\n' + config.get_localized_string(60293))

    config.set_setting('tmdb_active', True)
    # res_count = 0
    for key, value in ch_list.items():
        ch_name = channel_titles[channel_list.index(key)]
        grouped = list()
        cnt += 1
        progress.update(old_div((cnt * 100), len(ch_list)), config.get_localized_string(60295))

        for it in value:
            if it.channel == item.channel:
                it.channel = key
            if it in valid:
                continue
            if mode == 'all' or (it.contentType and mode == it.contentType):
                if config.get_setting('result_mode') != 0:
                    if config.get_localized_string(30992) not in it.title:
                        it.title += typo(ch_name,'_ [] color kod bold')
                        results.append(it)
                else:
                    grouped.append(it)
            elif (mode == 'movie' and it.contentTitle) or (mode == 'tvshow' and (it.contentSerieName or it.show)):
                grouped.append(it)
            else:
                continue

        if not grouped:
            continue
        # to_temp[key] = grouped
        if config.get_setting('result_mode') == 0:
            if not config.get_setting('unify'):
                title = typo(ch_name,'bold') + typo(str(len(grouped)), '_ [] color kod bold')
            else:
                title = typo('%s %s' % (len(grouped), config.get_localized_string(70695)), 'bold')
            # res_count += len(grouped)
            plot=''

            for it in grouped:
                plot += it.title +'\n'
            ch_thumb = channeltools.get_channel_parameters(key)['thumbnail']
            results.append(Item(channel='search', title=title,
                                action='get_from_temp', thumbnail=ch_thumb, itemlist=[ris.tourl() for ris in grouped], plot=plot, page=1))

    progress.close()
    # "All Together" and movie mode -> search servers
    if config.get_setting('result_mode') == 1 and mode == 'movie':
        progress = platformtools.dialog_progress(config.get_localized_string(30993) % item.title, config.get_localized_string(60683))
        valid_servers = []
        with futures.ThreadPoolExecutor(max_workers=set_workers()) as executor:
            c_results = [executor.submit(get_servers, v, module_dict) for v in valid]
            completed = 0

            for res in futures.as_completed(c_results):
                if progress.iscanceled():
                    break
                if res.result():
                    completed += 1
                    valid_servers.extend(res.result())
                    progress.update(old_div(completed * 100, len(valid)))
        valid = valid_servers
        progress.close()

    # send_to_temp(to_temp)

    results = sorted(results, key=lambda it: it.title)
    results_statistic = config.get_localized_string(59972) % (item.title, time.time() - start)
    if mode == 'all':
        results.insert(0, Item(title=typo(results_statistic, 'color kod bold'), thumbnail=get_thumb('search.png')))
    else:
        if not valid:
            valid.append(Item(title=config.get_localized_string(60347), thumbnail=get_thumb('nofolder.png')))

        valid.insert(0, Item(title=typo(results_statistic, 'color kod bold'), thumbnail=get_thumb('search.png')))
        results.insert(0, Item(title=typo(config.get_localized_string(30025), 'color kod bold'), thumbnail=get_thumb('search.png')))
    # logger.debug(results_statistic)

    itlist = valid + results
    writelist = item.text
    for it in itlist:
        writelist += ',' + it.tourl()
    filetools.write(temp_search_file, writelist)

    return itlist


def get_channel_results(item, module_dict, search_action):
    ch = search_action.channel
    results = list()
    valid = list()
    module = module_dict[ch]
    searched_id = item.infoLabels['tmdb_id']

    try:
        results.extend(module.search(search_action, item.text))
        if len(results) == 1:
            if not results[0].action or config.get_localized_string(70006).lower() in results[0].title.lower():
                results.clear()
        if item.mode != 'all':
            for elem in results:
                if not elem.infoLabels.get('year', ""):
                    elem.infoLabels['year'] = '-'
                tmdb.set_infoLabels_item(elem)
                if elem.infoLabels['tmdb_id'] == searched_id:
                    elem.from_channel = ch
                    if not config.get_setting('unify'):
                        elem.title += ' [%s]' % ch
                    valid.append(elem)

        # if len(results) < 0 and len(results) < max_results and item.mode != 'all':
        #
        #     if len(results) == 1:
        #         if not results[0].action or config.get_localized_string(30992).lower() in results[0].title.lower():
        #             return [ch, []]
        #
        #     results = get_info(results)

        return [search_action, results, valid]
    except:
        return [search_action, results, valid]


def get_servers(item, module_dict):
    item.global_search = True
    ch = item.channel
    results = list()
    module = module_dict[ch]
    try:
        results = getattr(module, item.action)(item)
    except:
        import traceback
        logger.error(traceback.format_exc())
    return [r.clone(title=r.title + typo(item.channel, '_ [] color kod')) for r in results if r.action == 'play']


def get_info(itemlist):
    logger.debug()
    tmdb.set_infoLabels_itemlist(itemlist, True, forced=True)

    return itemlist


def get_channels(item):
    logger.debug()

    channels_list = list()
    title_list = list()
    all_channels = channelselector.filterchannels('all')

    for ch in all_channels:
        channel = ch.channel
        ch_param = channeltools.get_channel_parameters(channel)
        if not ch_param.get("active", False):
            continue
        list_cat = ch_param.get("categories", [])

        if not ch_param.get("include_in_global_search", False):
            continue

        if 'anime' in list_cat:
            n = list_cat.index('anime')
            list_cat[n] = 'tvshow'

        if item.mode == 'all' or (item.mode in list_cat):
            if config.get_setting("include_in_global_search", channel) and ch_param.get("active", False):
                channels_list.append(channel)
                title_list.append(ch_param.get('title', channel))

    return channels_list, title_list


def settings(item):
    return platformtools.show_channel_settings(caption=config.get_localized_string(59993))


def set_workers():
    workers = config.get_setting('thread_number') if config.get_setting('thread_number') > 0 else None
    return workers


def setting_channel_new(item):
    import xbmcgui

    # Load list of options (active user channels that allow global search)
    lista = []
    ids = []
    lista_lang = []
    lista_ctgs = []
    channels_list = channelselector.filterchannels('all')
    for channel in channels_list:
        if channel.action == '':
            continue

        channel_parameters = channeltools.get_channel_parameters(channel.channel)

        # Do not include if "include_in_global_search" does not exist in the channel configuration
        if not channel_parameters['include_in_global_search']:
            continue

        lbl = '%s' % channel_parameters['language']
        lbl += ' %s' % ', '.join(config.get_localized_category(categ) for categ in channel_parameters['categories'])

        it = xbmcgui.ListItem(channel.title, lbl)
        it.setArt({'thumb': channel.thumbnail, 'fanart': channel.fanart})
        lista.append(it)
        ids.append(channel.channel)
        lista_lang.append(channel_parameters['language'])
        lista_ctgs.append(channel_parameters['categories'])

    # Pre-select dialog
    preselecciones = [
        config.get_localized_string(70570),
        config.get_localized_string(70571),
        # 'Modificar partiendo de Recomendados',
        # 'Modificar partiendo de Frecuentes',
        config.get_localized_string(70572),
        config.get_localized_string(70573),
        # 'Modificar partiendo de Castellano',
        # 'Modificar partiendo de Latino'
    ]
    # presel_values = ['skip', 'actual', 'recom', 'freq', 'all', 'none', 'cast', 'lat']
    presel_values = ['skip', 'actual', 'all', 'none']

    categs = ['movie', 'tvshow', 'documentary', 'anime', 'vos', 'direct', 'torrent']
    for c in categs:
        preselecciones.append(config.get_localized_string(70577) + config.get_localized_category(c))
        presel_values.append(c)

    if item.action == 'setting_channel':  # Configuración de los canales incluídos en la búsqueda
        del preselecciones[0]
        del presel_values[0]
    # else: # Call from "search on other channels" (you can skip the selection and go directly to the search)

    ret = platformtools.dialog_select(config.get_localized_string(59994), preselecciones)
    if ret == -1:
        return False  # order cancel
    if presel_values[ret] == 'skip':
        return True  # continue unmodified
    elif presel_values[ret] == 'none':
        preselect = []
    elif presel_values[ret] == 'all':
        preselect = list(range(len(ids)))
    elif presel_values[ret] in ['cast', 'lat']:
        preselect = []
        for i, lg in enumerate(lista_lang):
            if presel_values[ret] in lg or '*' in lg:
                preselect.append(i)
    elif presel_values[ret] == 'actual':
        preselect = []
        for i, canal in enumerate(ids):
            channel_status = config.get_setting('include_in_global_search', canal)
            if channel_status:
                preselect.append(i)

    elif presel_values[ret] == 'recom':
        preselect = []
        for i, canal in enumerate(ids):
            _not, set_canal_list = channeltools.get_channel_controls_settings(canal)
            if set_canal_list.get('include_in_global_search', False):
                preselect.append(i)

    elif presel_values[ret] == 'freq':
        preselect = []
        for i, canal in enumerate(ids):
            frequency = channeltools.get_channel_setting('frequency', canal, 0)
            if frequency > 0:
                preselect.append(i)
    else:
        preselect = []
        for i, ctgs in enumerate(lista_ctgs):
            if presel_values[ret] in ctgs:
                preselect.append(i)

    # Dialog to select
    ret = platformtools.dialog_multiselect(config.get_localized_string(59994), lista, preselect=preselect, useDetails=True)

    if ret == None: return False  # order cancel
    seleccionados = [ids[i] for i in ret]

    # Save changes to search channels
    for canal in ids:
        channel_status = config.get_setting('include_in_global_search', canal)
        # if not channel_status:
        #     channel_status = True

        if channel_status and canal not in seleccionados:
            config.set_setting('include_in_global_search', False, canal)
        elif not channel_status and canal in seleccionados:
            config.set_setting('include_in_global_search', True, canal)

    return True


def genres_menu(item):
    itemlist = []
    mode = item.mode.replace('show', '')

    genres = tmdb.get_dic_genres(mode)
    for key, value in list(genres[mode].items()):
        discovery = {'url': 'discover/%s' % mode, 'with_genres': key,
                     'language': def_lang, 'page': '1'}

        itemlist.append(Item(channel=item.channel, title=typo(value, 'bold'), page=1,
                             action='discover_list', discovery=discovery,
                             mode=item.mode))
    from core import support
    support.thumb(itemlist)
    return sorted(itemlist, key=lambda it: it.title)


def years_menu(item):
    import datetime
    itemlist = []

    mode = item.mode.replace('show', '')

    par_year = 'primary_release_year'
    thumb = channelselector.get_thumb('movie_year.png')

    if mode != 'movie':
        par_year = 'first_air_date_year'
        thumb = channelselector.get_thumb('tvshow_year.png')

    c_year = datetime.datetime.now().year + 1
    l_year = c_year - 31

    for year in range(l_year, c_year):
        discovery = {'url': 'discover/%s' % mode, 'page': '1',
                     '%s' % par_year: '%s' % year,
                     'sort_by': 'popularity.desc', 'language': def_lang}

        itemlist.append(Item(channel=item.channel, title=typo(str(year), 'bold'), action='discover_list',
                             discovery=discovery, mode=item.mode, year_=str(year), thumbnail=thumb))
    itemlist.reverse()
    itemlist.append(Item(channel=item.channel, title=typo(config.get_localized_string(70745),'color kod bold'), url='',
                         action="year_cus", mode=item.mode, par_year=par_year))

    return itemlist


def year_cus(item):
    mode = item.mode.replace('show', '')

    heading = config.get_localized_string(70042)
    year = platformtools.dialog_numeric(0, heading, default="")
    item.discovery = {'url': 'discover/%s' % mode, 'page': '1',
                      '%s' % item.par_year: '%s' % year,
                      'sort_by': 'popularity.desc', 'language': def_lang}
    item.action = "discover_list"
    if year and len(year) == 4:
        return discover_list(item)


def actor_list(item):
    itemlist = []

    dict_ = {'url': 'search/person', 'language': def_lang, 'query': item.searched_text, 'page': item.page}

    prof = {'Acting': 'Actor', 'Directing': 'Director', 'Production': 'Productor'}
    plot = ''
    item.search_type = 'person'

    tmdb_inf = tmdb.discovery(item, dict_=dict_)
    results = tmdb_inf.results

    if not results:
        return results

    for elem in results:
        name = elem.get('name', '')
        if not name:
            continue

        rol = elem.get('known_for_department', '')
        rol = prof.get(rol, rol)
        # genero = elem.get('gender', 0)
        # if genero == 1 and rol in prof:
        #     rol += 'a'
        #     rol = rol.replace('Actora', 'Actriz')

        know_for = elem.get('known_for', '')
        cast_id = elem.get('id', '')
        if know_for:
            t_k = know_for[0].get('title', '')
            if t_k:
                plot = '%s in %s' % (rol, t_k)

        thumbnail = 'https://image.tmdb.org/t/p/original%s' % elem.get('profile_path', '')
        title = typo(name,'bold')+typo(rol,'_ [] color kod bold')

        discovery = {'url': 'person/%s/combined_credits' % cast_id, 'page': '1',
                     'sort_by': 'primary_release_date.desc', 'language': def_lang}

        itemlist.append(Item(channel=item.channel, title=title, action='discover_list', cast_='cast',
                             discovery=discovery, thumbnail=thumbnail, plot=plot, page=1))

    if len(results) > 19:
        next_ = item.page + 1
        itemlist.append(Item(channel=item.channel, title=typo(config.get_localized_string(30992),'bold color kod'), action='actor_list',
                             page=next_, thumbnail=thumbnail,
                             searched_text=item.searched_text))
    return itemlist


def discover_list(item):
    import datetime
    itemlist = []

    year = 0
    tmdb_inf = tmdb.discovery(item, dict_=item.discovery, cast=item.cast_)
    result = tmdb_inf.results
    tvshow = False

    for elem in result:
        elem = tmdb_inf.get_infoLabels(elem, origen=elem)
        if 'title' in elem:
            title = unify.normalize(elem['title']).capitalize()
        else:
            title = unify.normalize(elem['name']).capitalize()
            tvshow = True
        elem['tmdb_id'] = elem['id']

        mode = item.mode or elem['mediatype']
        thumbnail = elem.get('thumbnail', '')
        fanart = elem.get('fanart', '')

        if item.cast_:
            release = elem.get('release_date', '0000') or elem.get('first_air_date', '0000')
            year = scrapertools.find_single_match(release, r'(\d{4})')

        if not item.cast_ or (item.cast_ and (int(year) <= int(datetime.datetime.today().year))):
            if config.get_setting('new_search'):
                new_item = Item(channel='globalsearch', title=typo(title, 'bold'), infoLabels=elem,
                                action='Search', text=title,
                                thumbnail=thumbnail, fanart=fanart,
                                context='', mode='search', type = mode, contentType=mode,
                                release_date=year, folder = False)
            else:
                new_item = Item(channel='search', title=typo(title, 'bold'), infoLabels=elem,
                                action='channel_search', text=title,
                                thumbnail=thumbnail, fanart=fanart,
                                context='', mode=mode, contentType=mode,
                                release_date=year)

            if tvshow:
                new_item.contentSerieName = title
            else:
                new_item.contentTitle = title

            itemlist.append(new_item)

    itemlist = set_context(itemlist)

    if item.cast_:
        itemlist.sort(key=lambda it: int(it.release_date), reverse=True)
        return itemlist

    elif len(result) > 19 and item.discovery:
        item.discovery['page'] = str(int(item.discovery['page']) + 1)
        itemlist.append(item.clone(channel=item.channel, action='discover_list', nextPage=True,
                             title=typo(config.get_localized_string(30992), 'color kod bold'),
                             list_type=item.list_type, discovery=item.discovery, thumbnail=thumb(), page=item.discovery['page']))
    elif len(result) > 19:
        next_page = str(int(item.page) + 1)

        itemlist.append(item.clone(channel=item.channel, action='discover_list', nextPage=True,
                             title=typo(config.get_localized_string(30992), 'color kod bold'),
                             list_type=item.list_type, search_type=item.search_type, mode=item.mode, page=next_page, thumbnail=thumb()))

    return itemlist


def from_context(item):
    logger.debug()

    select = setting_channel_new(item)

    if not select:
        return

    if 'infoLabels' in item and 'mediatype' in item.infoLabels:
        item.mode = item.infoLabels['mediatype']
    else:
        return

    if config.get_setting('new_search'):
        from specials import globalsearch
        if item.infoLabels['tmdb_id']:
            item.type = item.mode
            item.mode = 'search'
        return globalsearch.Search(item)

    if 'list_type' not in item:
        if 'text' in item:
            item.title = item.text
        return channel_search(item)

    return discover_list(item)


def set_context(itemlist):
    logger.debug()

    for elem in itemlist:
        elem.context = [{"title": config.get_localized_string(60412),
                         "action": "setting_channel_new",
                         "channel": "search"},
                        {"title": config.get_localized_string(60415),
                         "action": "settings",
                         "channel": "search"},
                        {"title": config.get_localized_string(60416),
                         "action": "clear_saved_searches",
                         "channel": "search"}]

    return itemlist


def get_from_temp(item):
    logger.debug()

    n = 30
    nTotal = len(item.itemlist)
    nextp = n * item.page
    prevp = n * (item.page - 1)

    results = [Item().fromurl(elem) for elem in item.itemlist[prevp:nextp]]

    if nextp < nTotal:
        results.append(Item(channel='search', title=typo(config.get_localized_string(30992), 'bold color kod'),
                            action='get_from_temp', itemlist=item.itemlist, page=item.page + 1, nextPage=True))

    tmdb.set_infoLabels_itemlist(results, True)
    for elem in results:
        if not elem.infoLabels.get('year', ""):
            elem.infoLabels['year'] = '-'
            tmdb.set_infoLabels_item(elem, True)

    return results


def save_search(text):
    if text:
        saved_searches_limit = config.get_setting("saved_searches_limit")

        saved_searches_list = config.get_setting("saved_searches_list", "search")
        if not saved_searches_list:
            saved_searches_list = []

        if text in saved_searches_list:
            saved_searches_list.remove(text)

        saved_searches_list.insert(0, text)

        config.set_setting("saved_searches_list", saved_searches_list[:saved_searches_limit], "search")


def clear_saved_searches(item):
    config.set_setting("saved_searches_list", list(), "search")
    platformtools.dialog_ok(config.get_localized_string(60423), config.get_localized_string(60424))
    platformtools.itemlist_refresh()


def get_saved_searches():
    current_saved_searches_list = config.get_setting("saved_searches_list", "search")
    if not current_saved_searches_list:
        current_saved_searches_list = []
    saved_searches_list = []
    for saved_search_item in current_saved_searches_list:
        if type(saved_search_item) == str:
            saved_searches_list.append(
                Item(channel='search' if not config.get_setting('new_search') else 'globalsearch',
                     action="new_search" if not config.get_setting('new_search') else 'Search',
                     title=typo(saved_search_item.split('{}')[0], 'bold'),
                     search_text=saved_search_item.split('{}')[0],
                     text=saved_search_item.split('{}')[0],
                     mode='all',
                     thumbnail=get_thumb('search.png')))
        else:
            saved_searches_list.append(Item().fromjson(json.dumps(saved_search_item)))

    return saved_searches_list

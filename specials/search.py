# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Search Entry Point
# ------------------------------------------------------------

import xbmc
from core.item import Item
from core.support import typo, thumb
from platformcode import logger, config, platformtools

def mainlist(item):
    logger.debug()
    action = 'new_search'
    channel = 'classicsearch'
    folder = True
    if platformtools.get_window() not in ('WINDOW_SETTINGS_MENU', 'WINDOW_SETTINGS_INTERFACE', 'WINDOW_SKIN_SETTINGS')\
            and xbmc.getInfoLabel('System.CurrentWindow') in ('Home', '') and config.get_setting('new_search'):
                channel = 'globalsearch'
                folder = False

    itemlist = [Item(channel=channel, title=config.get_localized_string(70276), action=action, mode='all', folder=folder),
                Item(channel=channel, title=config.get_localized_string(70741) % config.get_localized_string(30122), action=action, mode='movie', folder=folder),
                Item(channel=channel, title=config.get_localized_string(70741) % config.get_localized_string(30123), action=action, mode='tvshow', folder=folder),
                Item(channel=channel, title=config.get_localized_string(70741) % config.get_localized_string(70314), action=action, page=1, mode='person', folder=folder),

                Item(channel=item.channel, title=config.get_localized_string(59995), action='saved_search', thumbnail=thumb('search')),
                Item(channel=item.channel, title=config.get_localized_string(60420), action='sub_menu', thumbnail=thumb('search')),
                Item(channel="tvmoviedb", title=config.get_localized_string(70274), action="mainlist", thumbnail=thumb('search')),
                Item(channel=item.channel, title=typo(config.get_localized_string(59994), 'bold'), action='channel_selections', folder=False),
                Item(channel='shortcuts', title=typo(config.get_localized_string(70286), 'bold'), action='SettingOnPosition', category=5, setting=1, folder=False)]

    thumb(itemlist)
    return itemlist


def sub_menu(item):
    logger.debug()
    channel = 'classicsearch'
    itemlist = [Item(channel=channel, action='genres_menu', title=config.get_localized_string(70306), mode='movie'),
                Item(channel=channel, action='years_menu', title=config.get_localized_string(70742), mode='movie'),
                Item(channel=channel, action='discover_list', title=config.get_localized_string(70307), search_type='list', list_type='movie/popular', mode='movie'),
                Item(channel=channel, action='discover_list', title=config.get_localized_string(70308), search_type='list', list_type='movie/top_rated', mode='movie'),
                Item(channel=channel, action='discover_list', title=config.get_localized_string(70309), search_type='list', list_type='movie/now_playing', mode='movie'),
                Item(channel=channel, action='genres_menu', title=config.get_localized_string(70310), mode='tvshow'),
                Item(channel=channel, action='years_menu', title=config.get_localized_string(70743), mode='tvshow'),
                Item(channel=channel, action='discover_list', title=config.get_localized_string(70311), search_type='list', list_type='tv/popular', mode='tvshow'),
                Item(channel=channel, action='discover_list', title=config.get_localized_string(70312), search_type='list', list_type='tv/on_the_air', mode='tvshow'),
                Item(channel=channel, action='discover_list', title=config.get_localized_string(70313), search_type='list', list_type='tv/top_rated', mode='tvshow')]

    itemlist = set_context(itemlist)
    thumb(itemlist)
    return itemlist


def set_context(itemlist):
    logger.debug()
    channel = 'classicsearch'
    for elem in itemlist:
        elem.context = [{"title": config.get_localized_string(60412),
                         "action": "channel_selections",
                         "channel": channel},
                        {"title": config.get_localized_string(60415),
                         "action": "settings",
                         "channel": channel},
                        {"title": config.get_localized_string(60416),
                         "action": "clear_saved_searches",
                         "channel": channel}]
    return itemlist


def channel_selections(item):
    import xbmcgui, channelselector
    from core import channeltools

    # Load list of options (active user channels that allow global search)
    channel_list = []
    ids = []
    lang_list = []
    cat_list = []
    channels_list = channelselector.filterchannels('all')
    for channel in channels_list:
        if channel.action == '':
            continue

        channel_parameters = channeltools.get_channel_parameters(channel.channel)

        # Do not include if "include_in_global_search" does not exist in the channel configuration
        if not channel_parameters['include_in_global_search']:
            continue
        label_cat = ', '.join(config.get_localized_category(c) for c in channel_parameters['categories'])
        label_lang = ', '.join(config.get_localized_language(l) for l in channel_parameters['language'])
        label = '{} [{}]'.format(label_cat, label_lang)

        it = xbmcgui.ListItem(channel.title, label)
        it.setArt({'thumb': channel.thumbnail, 'fanart': channel.fanart})
        channel_list.append(it)
        ids.append(channel.channel)
        lang_list.append(channel_parameters['language'])
        cat_list.append(channel_parameters['categories'])

    # Pre-select dialog
    preselections = [
        config.get_localized_string(70570),
        config.get_localized_string(70571),
        config.get_localized_string(70572),
        config.get_localized_string(70573),
    ]
    preselections_values = ['skip', 'actual', 'all', 'none']

    categories = ['movie', 'tvshow', 'documentary', 'anime', 'sub', 'live', 'torrent']
    for c in categories:
        preselections.append(config.get_localized_string(70577) + config.get_localized_category(c))
        preselections_values.append(c)

    if item.action == 'setting_channel':  # Configure channels included in search
        del preselections[0]
        del preselections_values[0]

    ret = platformtools.dialog_select(config.get_localized_string(59994), preselections)
    if ret == -1:
        return False  # order cancel
    if preselections_values[ret] == 'skip':
        return True  # continue unmodified
    elif preselections_values[ret] == 'none':
        preselect = []
    elif preselections_values[ret] == 'all':
        preselect = list(range(len(ids)))
    elif preselections_values[ret] == 'actual':
        preselect = []
        for i, channel in enumerate(ids):
            channel_status = config.get_setting('include_in_global_search', channel)
            if channel_status:
                preselect.append(i)
    else:
        preselect = []
        for i, ctgs in enumerate(cat_list):
            if preselections_values[ret] in ctgs:
                preselect.append(i)

    # Selection Dialog
    ret = platformtools.dialog_multiselect(config.get_localized_string(59994), channel_list, preselect=preselect, useDetails=True)

    if ret == None: return False  # order cancel
    selected = [ids[i] for i in ret]

    # Save changes to search channels
    for channel in ids:
        channel_status = config.get_setting('include_in_global_search', channel)

        if channel_status and channel not in selected:
            config.set_setting('include_in_global_search', False, channel)
        elif not channel_status and channel in selected:
            config.set_setting('include_in_global_search', True, channel)

    return True

def save_search(text):
    if text:
        saved_searches_limit = config.get_setting("saved_searches_limit")

        current_saved_searches_list = config.get_setting("saved_searches_list", "search")
        if current_saved_searches_list is None:
            saved_searches_list = []
        else:
            saved_searches_list = list(current_saved_searches_list)

        if text in saved_searches_list:
            saved_searches_list.remove(text)

        saved_searches_list.insert(0, text)

        config.set_setting("saved_searches_list", saved_searches_list[:saved_searches_limit], "search")

def clear_saved_searches(item):
    config.set_setting("saved_searches_list", list(), "search")
    platformtools.dialog_ok(config.get_localized_string(60423), config.get_localized_string(60424))

def saved_search(item):
    logger.debug()

    itemlist = list()
    saved_searches_list = get_saved_searches()


    for saved_search_text in saved_searches_list:
        itemlist.append(
            Item(channel=item.channel if not config.get_setting('new_search') else 'globalsearch',
                 action="new_search" if not config.get_setting('new_search') else 'Search',
                 title=typo(saved_search_text.split('{}')[0], 'bold'),
                 search_text=saved_search_text.split('{}')[0],
                 text=saved_search_text.split('{}')[0],
                 mode='all',
                 thumbnail=thumb('search')))

    if len(saved_searches_list) > 0:
        itemlist.append(
            Item(channel=item.channel,
                 action="clear_saved_searches",
                 title=typo(config.get_localized_string(60417), 'color kod bold'),
                 thumbnail=thumb('search')))

    itemlist = set_context(itemlist)
    return itemlist

def get_saved_searches():
    current_saved_searches_list = config.get_setting("saved_searches_list", "search")
    if current_saved_searches_list is None:
        saved_searches_list = []
    else:
        saved_searches_list = list(current_saved_searches_list)

    return saved_searches_list
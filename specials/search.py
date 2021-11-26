# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Search Entry Point
# ------------------------------------------------------------

import xbmc, json
from core.item import Item
from core.support import typo, thumb
from platformcode import logger, config, platformtools

def mainlist(item):
    logger.debug()
    action = 'new_search'
    channel = 'classicsearch'
    folder = True
    if platformtools.getWindow() not in ('WINDOW_SETTINGS_MENU', 'WINDOW_SETTINGS_INTERFACE', 'WINDOW_SKIN_SETTINGS')\
            and xbmc.getInfoLabel('System.CurrentWindow') in ('Home', '') and config.getSetting('new_search'):
                channel = 'globalsearch'
                folder = False

    itemlist = [Item(channel=channel, title=config.getLocalizedString(70276), action=action, mode='all', folder=folder),
                Item(channel=channel, title=config.getLocalizedString(70741) % config.getLocalizedString(30122), action=action, mode='movie', folder=folder),
                Item(channel=channel, title=config.getLocalizedString(70741) % config.getLocalizedString(30123), action=action, mode='tvshow', folder=folder),
                Item(channel=channel, title=config.getLocalizedString(70741) % config.getLocalizedString(70314), action=action, page=1, mode='person', folder=folder),

                Item(channel=item.channel, title=config.getLocalizedString(59995), action='saved_search', thumbnail=thumb('search')),
                Item(channel=item.channel, title=config.getLocalizedString(60420), action='sub_menu', thumbnail=thumb('search')),
                Item(channel="tvmoviedb", title=config.getLocalizedString(70274), action="mainlist", thumbnail=thumb('search')),
                Item(channel=item.channel, title=typo(config.getLocalizedString(59994), 'bold'), action='channel_selections', folder=False),
                Item(channel='shortcuts', title=typo(config.getLocalizedString(70286), 'bold'), action='SettingOnPosition', category=5, setting=1, folder=False)]

    thumb(itemlist)
    return itemlist


def sub_menu(item):
    logger.debug()
    channel = 'classicsearch'
    itemlist = [Item(channel=channel, action='genres_menu', title=config.getLocalizedString(70306), mode='movie'),
                Item(channel=channel, action='years_menu', title=config.getLocalizedString(70742), mode='movie'),
                Item(channel=channel, action='discover_list', title=config.getLocalizedString(70307), search_type='list', list_type='movie/popular', mode='movie'),
                Item(channel=channel, action='discover_list', title=config.getLocalizedString(70308), search_type='list', list_type='movie/top_rated', mode='movie'),
                Item(channel=channel, action='discover_list', title=config.getLocalizedString(70309), search_type='list', list_type='movie/now_playing', mode='movie'),
                Item(channel=channel, action='genres_menu', title=config.getLocalizedString(70310), mode='tvshow'),
                Item(channel=channel, action='years_menu', title=config.getLocalizedString(70743), mode='tvshow'),
                Item(channel=channel, action='discover_list', title=config.getLocalizedString(70311), search_type='list', list_type='tv/popular', mode='tvshow'),
                Item(channel=channel, action='discover_list', title=config.getLocalizedString(70312), search_type='list', list_type='tv/on_the_air', mode='tvshow'),
                Item(channel=channel, action='discover_list', title=config.getLocalizedString(70313), search_type='list', list_type='tv/top_rated', mode='tvshow')]

    itemlist = set_context(itemlist)
    thumb(itemlist)
    return itemlist


def set_context(itemlist):
    logger.debug()
    channel = 'classicsearch'
    for elem in itemlist:
        elem.context = [{"title": config.getLocalizedString(60412),
                         "action": "channel_selections",
                         "channel": channel},
                        {"title": config.getLocalizedString(60415),
                         "action": "settings",
                         "channel": channel},
                        {"title": config.getLocalizedString(60416),
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
        label_cat = ', '.join(config.getLocalizedCategory(c) for c in channel_parameters['categories'])
        label_lang = ', '.join(config.getLocalizedLanguage(l) for l in channel_parameters['language'])
        label = '{} [{}]'.format(label_cat, label_lang)

        it = xbmcgui.ListItem(channel.title, label)
        it.setArt({'thumb': channel.thumbnail, 'fanart': channel.fanart})
        channel_list.append(it)
        ids.append(channel.channel)
        lang_list.append(channel_parameters['language'])
        cat_list.append(channel_parameters['categories'])

    # Pre-select dialog
    preselections = [
        config.getLocalizedString(70570),
        config.getLocalizedString(70571),
        config.getLocalizedString(70572),
        config.getLocalizedString(70573),
    ]
    preselections_values = ['skip', 'actual', 'all', 'none']

    categories = ['movie', 'tvshow', 'documentary', 'anime', 'sub', 'live', 'torrent']
    for c in categories:
        preselections.append(config.getLocalizedString(70577) + config.getLocalizedCategory(c))
        preselections_values.append(c)

    if item.action == 'setting_channel':  # Configure channels included in search
        del preselections[0]
        del preselections_values[0]

    ret = platformtools.dialogSelect(config.getLocalizedString(59994), preselections)
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
            channel_status = config.getSetting('include_in_global_search', channel)
            if channel_status:
                preselect.append(i)
    else:
        preselect = []
        for i, ctgs in enumerate(cat_list):
            if preselections_values[ret] in ctgs:
                preselect.append(i)

    # Selection Dialog
    ret = platformtools.dialogMultiselect(config.getLocalizedString(59994), channel_list, preselect=preselect, useDetails=True)

    if ret == None: return False  # order cancel
    selected = [ids[i] for i in ret]

    # Save changes to search channels
    for channel in ids:
        channel_status = config.getSetting('include_in_global_search', channel)

        if channel_status and channel not in selected:
            config.setSetting('include_in_global_search', False, channel)
        elif not channel_status and channel in selected:
            config.setSetting('include_in_global_search', True, channel)

    return True

def save_search(text):
    if text:
        saved_searches_limit = config.getSetting("saved_searches_limit")

        current_saved_searches_list = config.getSetting("saved_searches_list", "search")
        if current_saved_searches_list is None:
            saved_searches_list = []
        else:
            saved_searches_list = list(current_saved_searches_list)

        if text in saved_searches_list:
            saved_searches_list.remove(text)

        saved_searches_list.insert(0, text)

        config.setSetting("saved_searches_list", saved_searches_list[:saved_searches_limit], "search")

def clear_saved_searches(item):
    config.setSetting("saved_searches_list", list(), "search")
    platformtools.dialogOk(config.getLocalizedString(60423), config.getLocalizedString(60424))

def saved_search(item):
    logger.debug()

    itemlist = get_saved_searches()

    if len(itemlist) > 0:
        itemlist.append(
            Item(channel=item.channel,
                 action="clear_saved_searches",
                 title=typo(config.getLocalizedString(60417), 'color kod bold'),
                 thumbnail=thumb('search')))

    itemlist = set_context(itemlist)
    return itemlist

def get_saved_searches():
    current_saved_searches_list = config.getSetting("saved_searches_list", "search")
    if not current_saved_searches_list:
        current_saved_searches_list = []
    saved_searches_list = []
    for saved_search_item in current_saved_searches_list:
        if type(saved_search_item) == str:
            text = saved_search_item.split('{}')[0]
            saved_searches_list.append(
                Item(channel='globalsearch' if config.getSetting('new_search') else 'classicsearch',
                     folder=False if config.getSetting('new_search') else True,
                     action="new_search",
                     title=text,
                     search_text=text,
                     text=text,
                     mode= 'all',
                     thumbnail=thumb('search')))
        else:
            item = Item().fromjson(json.dumps(saved_search_item))
            if item.action == 'Search':
                item.action = 'new_search'
                if item.type: item.mode = 'search/'+item.type
            saved_searches_list.append(item)

    return saved_searches_list

def from_context(item):
    logger.debug()
    from specials import globalsearch, classicsearch

    select = channel_selections(item)

    if not select:
        return

    if 'infoLabels' in item and 'mediatype' in item.infoLabels:
        item.mode = item.infoLabels['mediatype']
    else:
        return

    if config.getSetting('new_search') and not item.page:
        if item.infoLabels['tmdb_id']:
            item.mode = 'search/' + item.mode
        return globalsearch.new_search(item)

    if 'list_type' not in item:
        if 'wanted' in item:
            item.title = item.wanted
        return classicsearch.channel_search(item)

    return classicsearch.discover_list(item)
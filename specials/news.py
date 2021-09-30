# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Channel for recent videos on several channels
# ------------------------------------------------------------
import sys, channelselector
from platformcode import config, logger, platformtools
from channelselector import auto_filter
from core.item import Item
from core import support, filetools, channeltools, tmdb

if sys.version_info[0] >= 3:
    from concurrent import futures
else:
    from concurrent_py2 import futures

progress = None
mode = config.get_setting('result_mode', 'news')

def mainlist(item):
    logger.debug()

    itemlist = []
    # list_canales, any_active = get_channels_list()
    channel_language = config.get_setting("channel_language", default="auto")
    if channel_language == 'auto':
        channel_language = auto_filter()

    itemlist = [item.clone(action="news", extra="movie", title=config.get_localized_string(30122) + ' {news}'),
                item.clone(action="news", extra="tvshow", title=config.get_localized_string(60511) + ' {news}'),
                item.clone(action="news", extra="anime", title=config.get_localized_string(60512) + ' {news}')]

    set_category_context(itemlist)

    itemlist.append(Item(channel='shortcuts', action="SettingOnPosition", category=7, setting=1,
                         title=support.typo(config.get_localized_string(70285), 'bold color kod')))

    support.thumb(itemlist)
    set_category_context(itemlist)

    return itemlist


def set_category_context(itemlist):
    for item in itemlist:
        if item.extra:
            item.context = [{"title": config.get_localized_string(60514) % item.title,
                            "extra": item.extra,
                            "action": "setting_channel",
                            "channel": item.channel}]
            item.category = config.get_localized_string(60679) % item.title


def get_channels(category='all'):
    logger.debug()
    # logger.dbg()
    channels = []

    all_channels = channelselector.filterchannels(category)

    for ch in all_channels:
        channel = ch.channel
        ch_param = channeltools.get_channel_parameters(channel)
        if not ch_param.get("active", False):
            continue

        if not config.get_setting("include_in_newest_" + category, channel):
            continue

        channels.append([ch_param.get('title'), channel])
    return channels


def news(item):

    if item.itemlist:
        itemlist = support.itemlistdb()

    else:
        itemlist = []
        results = cache()
        if not results:

            global progress
            progress = platformtools.dialog_progress(item.category, config.get_localized_string(60519))
            channels = get_channels(item.extra)

            with futures.ThreadPoolExecutor() as executor:
                itlist = [executor.submit(get_newest, i, channel, item.extra, len(channels)) for i, channel in enumerate(channels)]
                for res in futures.as_completed(itlist):
                    if res.result():
                        results.append(res.result())
            if progress:
                progress.close()

            cache(results)

        if mode in [2]:
            for res in results:
                _name, _id, _list = res
                for it in _list:
                    it.title += ' [{}]'.format(_name)
                itemlist.extend(_list)

        elif mode in [1]:
            for res in results:
                plot = ''
                items = []
                for it in res[2]:
                    plot += '\n{}'.format(it.title)
                    items.append(it.tourl())
                if items:
                    itemlist.append(Item(title='{} [{}]'.format(res[0], len(items)),
                                         plot=plot,
                                         channel='news',
                                         action='movies',
                                         thumbnail=channeltools.get_channel_parameters(res[1])["thumbnail"],
                                         items=items))
            itemlist.sort(key=lambda it: it.title)
        elif mode in [0]:

            items = {}
            for res in results:
                _name, _id, _list = res
                for it in _list:
                    if it.fulltitle not in items:
                        items[it.fulltitle] = []

                    items[it.fulltitle].append(it.tourl())

            itemlist = [Item(title='{} [{}]'.format(k, len(items)), infoLabels=Item().fromurl(v[0]).infoLabels, channel='news', action='movies', items = v) for k, v in items.items()]

    if mode in [0, 2]:
        itemlist = support.pagination(itemlist, item, 'news')
        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def get_newest(i, channel, category, total):
    global progress
    cat = {'movie':'movies', 'tvshow':'shows', 'anime':'anime'}
    name = channel[0]
    _id = channel[1]

    module = platformtools.channel_import(_id)
    logger.debug('channel_id=', _id, 'category=', category)
    if progress: progress.update(int(i + 1 / total), name)
    list_newest = []
    try:
        if not module:
            return []

        list_newest = module.newest(category)
        for item in list_newest:
            item.channel = _id

    except:
        logger.error("No se pueden recuperar novedades de: " + name)
        import traceback
        logger.error(traceback.format_exc())

    return name, _id, list_newest


def movies(item):
    itemlist = [Item().fromurl(url=it) for it in item.items]
    if mode == 1: tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def cache(results=None):
    from core import db
    from time import time
    news = db['news']

    if results != None:
        news['time'] = time()
        news['results'] = results
        db['news'] = news

    elif news.get('time', 0) + 60 < time() :
        results = []
    else:
        results = news.get('results', [])
    db.close()
    return results

def settings(item):
    return platformtools.show_channel_settings(caption=config.get_localized_string(60532))


def setting_channel(item):
    import os, glob
    channels_path = os.path.join(config.get_runtime_path(), "channels", '*.json')
    channel_language = config.get_setting("channel_language", default="auto")
    if channel_language == 'auto':
        channel_language = auto_filter()


    list_controls = []
    for infile in sorted(glob.glob(channels_path)):
        channel_id = filetools.basename(infile)[:-5]
        channel_parameters = channeltools.get_channel_parameters(channel_id)

        # Do not include if it is an inactive channel
        if not channel_parameters["active"]:
            continue

        # Do not include if the channel is in a filtered language
        if channel_language != "all" and channel_language not in str(channel_parameters["language"]) and "*" not in channel_parameters["language"]:
            continue

        # Do not include if the channel does not exist 'include_in_newest' in your configuration
        include_in_newest = config.get_setting("include_in_newest_" + item.extra, channel_id)
        if include_in_newest is None or item.extra not in channel_parameters['categories']:
            continue

        control = {'id': channel_id,
                   'type': "bool",
                   'label': channel_parameters["title"],
                   'default': include_in_newest,
                   'enabled': True,
                   'visible': True}

        list_controls.append(control)

    caption = config.get_localized_string(60533) + item.title.replace(config.get_localized_string(60525), "- ").strip()
    if config.get_setting("custom_button_value_news", item.channel):
        custom_button_label = config.get_localized_string(59992)
    else:
        custom_button_label = config.get_localized_string(59991)

    return platformtools.show_channel_settings(list_controls=list_controls,
                                               caption=caption,
                                               callback="save_settings", item=item,
                                               custom_button={'visible': True,
                                                              'function': "cb_custom_button",
                                                              'close': False,
                                                              'label': custom_button_label})


def save_settings(item, dict_values):
    cache([])
    for v in dict_values:
        config.set_setting("include_in_newest_" + item.extra, dict_values[v], v)


def cb_custom_button(item, dict_values):
    value = config.get_setting("custom_button_value_news", item.channel)
    if value == "":
        value = False

    for v in list(dict_values.keys()):
        dict_values[v] = not value

    if config.set_setting("custom_button_value_news", not value, item.channel) == True:
        return {"label": config.get_localized_string(59992)}
    else:
        return {"label": config.get_localized_string(59991)}


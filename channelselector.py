# -*- coding: utf-8 -*-

import glob, os

from core.item import Item
from platformcode import config, logger
from core.support import thumb
addon = config.__settings__
downloadenabled = addon.getSetting('downloadenabled')


def getmainlist(view="thumb_"):
    logger.debug()
    itemlist = list()

    # Main Menu Channels
    if addon.getSetting('enable_news_menu') == "true":
        itemlist.append(Item(title=config.getLocalizedString(30130), channel="news", action="mainlist",
                             thumbnail=thumb("news"), category=config.getLocalizedString(30119), viewmode="thumbnails",
                             context=[{"title": config.getLocalizedString(70285), "channel": "shortcuts", "action": "SettingOnPosition", "category":7, "setting":1}]))

    if addon.getSetting('enable_channels_menu') == "true":
        itemlist.append(Item(title=config.getLocalizedString(30118), channel="channelselector", action="getchanneltypes",
                             thumbnail=thumb("channels"), view=view, category=config.getLocalizedString(30119), viewmode="thumbnails"))

    if addon.getSetting('enable_search_menu') == "true":
        itemlist.append(Item(title=config.getLocalizedString(30103), channel="search", path='special', action="mainlist",
                             thumbnail=thumb("search"), category=config.getLocalizedString(30119), viewmode="list",
                             context = [{"title": config.getLocalizedString(60412), "action": "channels_selections", "channel": "search"},
                                       {"title": config.getLocalizedString(70286), "channel": "shortcuts", "action": "SettingOnPosition", "category":5 , "setting":1}]))

    if addon.getSetting('enable_onair_menu') == "true":
        itemlist.append(Item(channel="filmontv", action="mainlist", title=config.getLocalizedString(50001),
                             thumbnail=thumb("live"), viewmode="thumbnails"))

    if addon.getSetting('enable_link_menu') == "true":
        itemlist.append(Item(title=config.getLocalizedString(70527), channel="kodfavorites", action="mainlist", thumbnail=thumb("mylink"),
                             view=view, category=config.getLocalizedString(70527), viewmode="thumbnails"))

    if addon.getSetting('enable_fav_menu') == "true":
        itemlist.append(Item(title=config.getLocalizedString(30102), channel="favorites", action="mainlist",
                            thumbnail=thumb("favorites"), category=config.getLocalizedString(30102), viewmode="thumbnails"))

    if config.get_videolibrary_support() and addon.getSetting('enable_library_menu') == "true":
        itemlist.append(Item(title=config.getLocalizedString(30131), channel="videolibrary", action="mainlist",
                             thumbnail=thumb("videolibrary"), category=config.getLocalizedString(30119), viewmode="thumbnails",
                             context=[{"title": config.getLocalizedString(70287), "channel": "shortcuts", "action": "SettingOnPosition", "category":2, "setting":1},
                                      {"title": config.getLocalizedString(60568), "channel": "videolibrary", "action": "update_videolibrary"}]))
    if downloadenabled != "false":
        itemlist.append(Item(title=config.getLocalizedString(30101), channel="downloads", action="mainlist", thumbnail=thumb("download"), viewmode="list",
                             context=[{"title": config.getLocalizedString(70288), "channel": "shortcuts", "action": "SettingOnPosition", "category":6}]))


    itemlist.append(Item(title=config.getLocalizedString(30100), channel="setting", action="settings",
                         thumbnail=thumb('setting'), category=config.getLocalizedString(30100), viewmode="list", folder=False))
    itemlist.append(Item(title=config.getLocalizedString(30104) + " (v" + config.getAddonVersion(with_fix=True) + ")", channel="help", action="mainlist",
                         thumbnail=thumb("help"), category=config.getLocalizedString(30104), viewmode="list"))
    return itemlist


def getchanneltypes(view="thumb_"):
    logger.debug()

    # Category List
    channel_types = ["movie", "tvshow", "anime", "documentary", "sub", "live", "torrent",  "music"] #, "direct"

    # Channel Language
    channel_language = auto_filter()
    logger.debug("channel_language=%s" % channel_language)

    # Build Itemlist
    itemlist = list()
    title = config.getLocalizedString(30121)
    itemlist.append(Item(title=title, channel="channelselector", action="filterchannels", view=view,
                         category=title, channel_type="all", thumbnail=thumb("all"),
                         viewmode="thumbnails"))

    for channel_type in channel_types:
        title = config.getLocalizedCategory(channel_type)
        itemlist.append(Item(title=title, channel="channelselector", action="filterchannels", category=title,
                             channel_type=channel_type, viewmode="thumbnails",
                             thumbnail=thumb(channel_type)))

    itemlist.append(Item(title=config.getLocalizedString(70685), channel="community", action="mainlist", view=view,
                         category=config.getLocalizedString(70685), channel_type="all", thumbnail=thumb("community"),
                         viewmode="thumbnails"))
    return itemlist


def filterchannels(category, view="thumb_"):
    from core import channeltools
    logger.debug('Filter Channels ' + category)

    channelslist = []

    # If category = "allchannelstatus" is that we are activating / deactivating channels
    appenddisabledchannels = False
    if category == "allchannelstatus":
        category = "all"
        appenddisabledchannels = True

    channel_path = os.path.join(config.getRuntimePath(), 'channels', '*.json')
    logger.debug("channel_path = %s" % channel_path)

    channel_files = glob.glob(channel_path)
    logger.debug("channel_files found %s" % (len(channel_files)))

    # Channel Language
    channel_language = auto_filter()
    logger.debug("channel_language=%s" % channel_language)

    for channel_path in channel_files:
        logger.debug("channel in for = %s" % channel_path)

        channel = os.path.basename(channel_path).replace(".json", "")

        try:
            channel_parameters = channeltools.get_channel_parameters(channel)

            if channel_parameters["channel"] == 'community':
                continue

            # If it's not a channel we skip it
            if not channel_parameters["channel"]:
                continue
            logger.debug("channel_parameters=%s" % repr(channel_parameters))

            # If you prefer the banner and the channel has it, now change your mind
            # if view == "banner_" and "banner" in channel_parameters:
            #     channel_parameters["thumbnail"] = channel_parameters["banner"]

            # if the channel is deactivated the channel is not shown in the list
            if not channel_parameters["active"]:
                continue

            # The channel is skipped if it is not active and we are not activating / deactivating the channels
            channel_status = config.getSetting("enabled", channel_parameters["channel"])

            if channel_status is None:
                # if channel_status does not exist, there is NO value in _data.json.
                # as we got here (the channel is active in channel.json), True is returned
                channel_status = True

            if not channel_status:
                # if we get the list of channels from "activate / deactivate channels", and the channel is deactivated
                # we show it, if we are listing all the channels from the general list and it is deactivated, it is not shown
                if not appenddisabledchannels:
                    continue

            if channel_language != "all" and "*" not in channel_parameters["language"] \
                 and channel_language not in str(channel_parameters["language"]):
                continue

            # The channel is skipped if it is in a filtered category
            if category != "all" and category not in channel_parameters["categories"]:
                continue

            # If you have configuration we add an item in the context
            context = []
            if channel_parameters["has_settings"]:
                context.append({"title": config.getLocalizedString(70525), "channel": "setting", "action": "channel_config",
                                "config": channel_parameters["channel"]})

            channel_info = set_channel_info(channel_parameters)
            # If it has come this far, add it
            channelslist.append(Item(title=channel_parameters["title"], channel=channel_parameters["channel"],
                                     action="mainlist", thumbnail=channel_parameters["thumbnail"],
                                     fanart=channel_parameters["fanart"], plot=channel_info, category=channel_parameters["title"],
                                     language=channel_parameters["language"], viewmode="list", context=context))

        except:
            logger.error("An error occurred while reading the channel data '%s'" % channel)
            import traceback
            logger.error(traceback.format_exc())

    channelslist.sort(key=lambda item: item.title.lower().strip())

    if not config.getSetting("only_channel_icons"):
        from core.support import thumb

        if category == "all":
            channel_parameters = channeltools.get_channel_parameters('url')
            # If you prefer the banner and the channel has it, now change your mind
            # if view == "banner_" and "banner" in channel_parameters:
            #     channel_parameters["thumbnail"] = channel_parameters["banner"]

            channelslist.insert(0, Item(title=config.getLocalizedString(60088), action="mainlist", channel="url",
                                        thumbnail=channel_parameters["thumbnail"], type="generic", viewmode="list"))
        # Special Category
        if category in ['movie', 'tvshow']:
            ch_list = []
            titles = [config.getLocalizedString(70028), config.getLocalizedString(30985), config.getLocalizedString(70559), config.getLocalizedString(60264), config.getLocalizedString(70560)]
            ids = ['popular', 'top_rated', 'now_playing', 'on_the_air']
            for x in range(0,3):
                if x == 2 and category != 'movie':
                    title=titles[x+1] + '{tv}'
                    id = ids[x+1]
                else:
                    title=titles[x]  + '{movie}'
                    id = ids[x]
                ch_list.insert(x,
                    Item(channel='classicsearch', action='discover_list', title=title, search_type='list',
                         list_type='%s/%s' % (category.replace('show',''), id), mode=category))


            ch_list.insert(3, Item(channel='classicsearch', action='genres_menu', title=config.getLocalizedString(30987) + '{' + category.replace('show','') + '}',
                                        type=category.replace('show',''), mode=category))
            channelslist = thumb(ch_list) + channelslist

    return channelslist


# def get_thumb(thumb_name, view="thumb_"):
#     from core import filetools
#     if thumb_name.startswith('http'):
#         return thumb_name
#     elif config.getSetting('enable_custom_theme') and config.getSetting('custom_theme') and filetools.isfile(config.getSetting('custom_theme') + view + thumb_name):
#         media_path = config.getSetting('custom_theme')
#     else:
#         icon_pack_name = config.getSetting('icon_set', default="default")
#         media_path = filetools.join("https://raw.githubusercontent.com/kodiondemand/media/master/themes/new", icon_pack_name)
#     return filetools.join(media_path, thumb_name)


def set_channel_info(parameters):
    logger.debug()

    info = ''
    language = ''
    content = ''
    langs = parameters['language']
    lang_dict = {'ita':'Italiano',
                 'sub-ita':'Sottotitolato in Italiano',
                 '*':'Italiano, Sottotitolato in Italiano'}

    for lang in langs:

        if lang in lang_dict:
            if language != '' and language != '*':
                language = '%s, %s' % (language, lang_dict[lang])
            else:
                language = lang_dict[lang]
        if lang == '*':
            break

    categories = parameters['categories']
    for cat in categories:
        if content != '':
            content = '%s, %s' % (content, config.getLocalizedCategory(cat))
        else:
            content = config.getLocalizedCategory(cat)

    info = '[B]' + config.getLocalizedString(70567) + ' [/B]' + content + '\n\n'
    info += '[B]' + config.getLocalizedString(70568) + ' [/B] ' + language
    return info


def auto_filter(auto_lang=False):
    list_lang = ['ita', 'vos', 'sub-ita']
    if config.getSetting("channel_language") == 'auto' or auto_lang == True:
        lang = config.getLocalizedString(20001)

    else:
        lang = config.getSetting("channel_language", default="all")

    if lang not in list_lang:
        lang = 'all'

    return lang

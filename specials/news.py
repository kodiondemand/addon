# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Channel for recent videos on several channels
# ------------------------------------------------------------

#from builtins import str
import sys

from core.support import typo

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import glob, os, re, time
from threading import Thread

from channelselector import get_thumb, auto_filter
from core import channeltools, jsontools, scrapertools, support, tmdb
from core.item import Item
from platformcode import config, logger, platformtools

THUMBNAILS = {'0': 'posters', '1': 'banners', '2': 'squares'}

__perfil__ = config.get_setting('perfil', "news")

# Set color profile
perfil = [['0xFF0B7B92', '0xFF89FDFB', '0xFFACD5D4'],
          ['0xFFB31313', '0xFFFF9000', '0xFFFFEE82'],
          ['0xFF891180', '0xFFCB22D7', '0xFFEEA1EB'],
          ['0xFFA5DEE5', '0xFFE0F9B5', '0xFFFEFDCA'],
          ['0xFFF23557', '0xFF22B2DA', '0xFFF0D43A']]

color1, color2, color3 = ["red", "0xFF65B3DA", "yellow"]
# color1, color2, color3 = perfil[__perfil__]

list_newest = []
list_newest_tourl = []
channels_id_name = {}

menu_cache_path = os.path.join(config.get_data_path(), "settings_channels", 'menu_cache_data.json')
menu_settings_path = os.path.join(config.get_data_path(), "settings_channels", 'menu_settings_data.json')


def mainlist(item):
    logger.debug()

    itemlist = []
    # list_canales, any_active = get_channels_list()
    channel_language = config.get_setting("channel_language", default="auto")
    if channel_language == 'auto':
        channel_language = auto_filter()

    #if list_canales['peliculas']:
    thumbnail = get_thumb("movie.png")
    new_item = Item(channel=item.channel, action="novedades", contentType='movie', extra="peliculas", title=config.get_localized_string(30122),
                    thumbnail=thumbnail)

    set_category_context(new_item)
    itemlist.append(new_item)

    # thumbnail = get_thumb("movie_4k.png")
    # new_item = Item(channel=item.channel, action="novedades", extra="4k", title=config.get_localized_string(70208), thumbnail=thumbnail)
    #
    # set_category_context(new_item)
    # itemlist.append(new_item)

    #if list_canales['terror']:
    # thumbnail = get_thumb("channels_horror.png")
    # new_item = Item(channel=item.channel, action="novedades", extra="terror", title=config.get_localized_string(70209),
    #                 thumbnail=thumbnail)
    # set_category_context(new_item)
    # itemlist.append(new_item)

    #if list_canales['infantiles']:
    # thumbnail = get_thumb("children.png")
    # new_item = Item(channel=item.channel, action="novedades", extra="infantiles", title=config.get_localized_string(60510),
    #                 thumbnail=thumbnail)
    # set_category_context(new_item)
    # itemlist.append(new_item)

    #if list_canales['series']:
    thumbnail = get_thumb("tvshow.png")
    new_item = Item(channel=item.channel, action="novedades", contentType='tvshow', extra="series", title=config.get_localized_string(60511),
                    thumbnail=thumbnail)
    set_category_context(new_item)
    itemlist.append(new_item)

    #if list_canales['anime']:
    thumbnail = get_thumb("anime.png")
    new_item = Item(channel=item.channel, action="novedades", contentType='tvshow', extra="anime", title=config.get_localized_string(60512),
                    thumbnail=thumbnail)
    set_category_context(new_item)
    itemlist.append(new_item)

    # if channel_language == "all":
    #     # if list_canales['Italiano']:
    #     thumbnail = get_thumb("italian.png")
    #     new_item = Item(channel=item.channel, action="novedades", extra="italiano", title=config.get_localized_string(70563),
    #                     thumbnail=thumbnail)
    #     set_category_context(new_item)
    #     itemlist.append(new_item)

    # if list_canales['Torrent']:
    # thumbnail = get_thumb("channels_torrent.png")
    # new_item = Item(channel=item.channel, action="novedades", extra="torrent", title=config.get_localized_string(70171), thumbnail=thumbnail)
    # set_category_context(new_item)
    # itemlist.append(new_item)

    #if list_canales['documentales']:
    # thumbnail = get_thumb("documentary.png")
    # new_item = Item(channel=item.channel, action="novedades", extra="documentales", title=config.get_localized_string(60513),
    #                 thumbnail=thumbnail)
    # set_category_context(new_item)
    # itemlist.append(new_item)
    thumbnail = get_thumb("setting_0.png")
    itemlist.append(Item(channel='shortcuts', action="SettingOnPosition", category=7, setting=1,
                         title=typo(config.get_localized_string(70285), 'bold color kod'), thumbnail=thumbnail))

    return itemlist


def set_category_context(item):
    item.context = [{"title": config.get_localized_string(60514) % item.title,
                     "extra": item.extra,
                     "action": "setting_channel",
                     "channel": item.channel}]
    item.category = config.get_localized_string(60679) % re.sub('\[[^\]]+\]','',item.title).strip()


def get_channels_list():
    logger.debug()
##    import web_pdb; web_pdb.set_trace()
##    list_canales = {'peliculas': [], '4k': [], 'terror': [], 'infantiles': [], 'series': [], 'anime': [],
##                    'castellano': [], 'latino':[], 'italiano':[], 'torrent':[], 'documentales': []}
    list_canales = {'peliculas': [], 'series': [], 'anime': [], 'documentales': []}

    any_active = False
    # Fill available channel lists
    channels_path = os.path.join(config.get_runtime_path(), "channels", '*.json')
    channel_language = config.get_setting("channel_language", default="all")
    if channel_language =="auto":
        channel_language = auto_filter()

    for infile in sorted(glob.glob(channels_path)):
        channel_id = os.path.basename(infile)[:-5]
        channel_parameters = channeltools.get_channel_parameters(channel_id)

        # Do not include if it is an inactive channel
        if not channel_parameters["active"]:
            continue

        # Do not include if the channel is in a filtered language
        if channel_language != "all" and channel_language not in str(channel_parameters["language"]) \
                and "*" not in channel_parameters["language"]:
            continue

        # Include in each category, if in your configuration the channel is activated to show news

        for categoria in list_canales:
            include_in_newest = config.get_setting("include_in_newest_" + categoria, channel_id)
            if include_in_newest:
                channels_id_name[channel_id] = channel_parameters["title"]
                list_canales[categoria].append((channel_id, channel_parameters["title"]))
                any_active = True

    return list_canales, any_active

def set_cache(item):
    logger.debug()
    item.mode = 'set_cache'
    t = Thread(target=novedades, args=[item])
    t.start()
    #t.join()

def get_from_cache(item):
    logger.debug()
    itemlist=[]
    cache_node = jsontools.get_node_from_file('menu_cache_data.json', 'cached')
    first=item.last
    last = first+40
    #if last >=len(cache_node[item.extra]):
    #    last = len(cache_node[item.extra])

    for cached_item in cache_node[item.extra][first:last]:
        new_item= Item()
        new_item = new_item.fromurl(cached_item)
        itemlist.append(new_item)
    if item.mode == 'silent':
        set_cache(item)
    if last >= len(cache_node[item.extra]):
        item.mode='finish'
        itemlist = add_menu_items(item, itemlist)
    else:
        item.mode='get_cached'
        item.last =last
        itemlist = add_menu_items(item, itemlist)

    return itemlist

def add_menu_items(item, itemlist):
    logger.debug()

    menu_icon = get_thumb('menu.png')
    menu = Item(channel="channelselector", action="getmainlist", viewmode="movie", thumbnail=menu_icon, title='Menu')
    itemlist.insert(0, menu)
    if item.mode != 'finish':
        if item.mode == 'get_cached':
            last=item.last
        else:
            last = len(itemlist)
        refresh_icon = get_thumb('more.png')
        refresh = item.clone(thumbnail=refresh_icon, mode='get_cached',title='Mas', last=last)
        itemlist.insert(len(itemlist), refresh)

    return itemlist

def novedades(item):
    logger.debug()

    global list_newest
    threads = []
    list_newest = []
    start_time = time.time()

    mode = item.mode
    if mode == '':
        mode = 'normal'

    if mode=='get_cached':
        if os.path.exists(menu_cache_path):
            return get_from_cache(item)

    multithread = config.get_setting("multithread", "news")
    logger.debug("multithread= " + str(multithread))

    if not multithread:
        if platformtools.dialog_yesno(config.get_localized_string(60515),
                                      config.get_localized_string(60516) + '\n' +
                                      config.get_localized_string(60517) + '\n' +
                                      config.get_localized_string(60518)):
            if config.set_setting("multithread", True, "news"):
                multithread = True

    if mode == 'normal':
        progreso = platformtools.dialog_progress(item.category, config.get_localized_string(60519))

    list_canales, any_active = get_channels_list()

    # if config.is_xbmc():
    #     from platformcode import side_menu
    #     if mode=='silent' and any_active and len(list_canales[item.extra]) > 0:
    #         side_menu.set_menu_settings(item)
    #         aux_list=[]
    #         for canal in list_canales[item.extra]:
    #             if len(aux_list)<2:
    #                 aux_list.append(canal)
    #         list_canales[item.extra]=aux_list

    if mode == 'set_cache':
        list_canales[item.extra] = list_canales[item.extra][2:]

    if any_active and len(list_canales[item.extra])>0:
        import math
        # fix float because division is done poorly in python 2.x
        number_of_channels = float(100) / len(list_canales[item.extra])

        for index, channel in enumerate(list_canales[item.extra]):
            channel_id, channel_title = channel
            percentage = int(math.ceil((index + 1) * number_of_channels))

            # if progreso.iscanceled():
            #     progreso.close()
            #     logger.debug("Búsqueda cancelada")
            #     return itemlist

            # Modo Multi Thread
            if multithread:
                t = Thread(target=get_newest, args=[channel_id, item.extra], name=channel_title)
                t.start()
                threads.append(t)
                if mode == 'normal':
                    progreso.update(percentage, config.get_localized_string(60520) % channel_title)

            # Modo single Thread
            else:
                if mode == 'normal':
                    logger.debug("Obteniendo novedades de channel_id=" + channel_id)
                    progreso.update(percentage, config.get_localized_string(60520) % channel_title)
                get_newest(channel_id, item.extra)

        # Multi Thread mode: wait for all threads to finish
        if multithread:
            pendent = [a for a in threads if a.is_alive()]
            t = float(100) / len(pendent)
            while pendent:
                index = (len(threads) - len(pendent)) + 1
                percentage = int(math.ceil(index * t))

                list_pendent_names = [a.getName() for a in pendent]
                if mode == 'normal':
                    mensaje = config.get_localized_string(30994) % (", ".join(list_pendent_names))
                    progreso.update(percentage, config.get_localized_string(60521) % (len(threads) - len(pendent), len(threads)) + '\n' +
                                mensaje)
                    logger.debug(mensaje)

                    if progreso.iscanceled():
                        logger.debug("Busqueda de novedades cancelada")
                        break

                time.sleep(0.5)
                pendent = [a for a in threads if a.is_alive()]
        if mode == 'normal':
            mensaje = config.get_localized_string(60522) % (len(list_newest), time.time() - start_time)
            progreso.update(100, mensaje)
            logger.debug(mensaje)
            start_time = time.time()
            # logger.debug(start_time)

        result_mode = config.get_setting("result_mode", "news")
        if mode != 'normal':
            result_mode=0
        if config.get_setting("tmdb", "news"):
            progreso.update(100, config.get_localized_string(70835))
            tmdb.set_infoLabels_itemlist(list_newest, seekTmdb=True)

        if result_mode == 0:  # Grouped by content
            ret = group_by_content(list_newest)
        elif result_mode == 1:  # Grouped by channels
            ret = group_by_channel(list_newest)
        else:  # Ungrouped
            ret = no_group(list_newest)

        while time.time() - start_time < 2:
            # show progress chart with time spent for at least 2 seconds
            time.sleep(0.5)
        if mode == 'normal':
            progreso.close()
        if mode == 'silent':
            set_cache(item)
            item.mode = 'set_cache'
            ret = add_menu_items(item, ret)
        if mode != 'set_cache':
            return ret
    else:
        if mode != 'set_cache':
            no_channels = platformtools.dialog_ok(config.get_localized_string(30130) + ' - ' + item.extra + '\n' + config.get_localized_string(70661) + '\n' + config.get_localized_string(70662))
        return


def get_newest(channel_id, categoria):
    logger.debug("channel_id=" + channel_id + ", categoria=" + categoria)

    global list_newest
    global list_newest_tourl

    # We request the news of the category (item.extra) searched in the channel channel
    # If there are no news for that category in the channel, it returns an empty list
    try:

        puede = True
        try:
            modulo = __import__('channels.%s' % channel_id, fromlist=["channels.%s" % channel_id])
        except:
            try:
                exec("import channels." + channel_id + " as modulo")
            except:
                puede = False

        if not puede:
            return

        logger.debug("running channel " + modulo.__name__ + " " + modulo.__file__)
        list_result = modulo.newest(categoria)
        logger.debug("canal= %s %d resultados" % (channel_id, len(list_result)))
        exist=False
        if os.path.exists(menu_cache_path):
            cache_node = jsontools.get_node_from_file('menu_cache_data.json', 'cached')
            exist=True
        else:
            cache_node = {}
        # logger.debug('cache node: %s' % cache_node)
        for item in list_result:
            # logger.debug("item="+item.tostring())
            item.channel = channel_id
            list_newest.append(item)
            list_newest_tourl.append(item.tourl())

        cache_node[categoria] = list_newest_tourl

        jsontools.update_node(cache_node, 'menu_cache_data.json', "cached")

    except:
        logger.error("No se pueden recuperar novedades de: " + channel_id)
        import traceback
        logger.error(traceback.format_exc())


def get_title(item):
    # support.info("ITEM NEWEST ->", item)
    # item.contentSerieName c'è anche se è un film
    if item.contentSerieName and item.contentType != 'movie':  # Si es una serie
        title = item.contentSerieName
        # title = re.compile("\[.*?\]", re.DOTALL).sub("", item.contentSerieName)
        if not scrapertools.get_season_and_episode(title) and item.contentEpisodeNumber:
            # contentSeason non c'è in support
            if item.contentSeason:
                title = '{}x{:02d}. {}'.format(item.contentSeason, item.contentEpisodeNumber, title)
            else:
                title = '{:02d}. {}'.format(item.contentEpisodeNumber, title)
        else:
            seas = scrapertools.get_season_and_episode(item.title)
            if seas:
                title = "{}. {}".format(seas, title)

    elif item.contentTitle:  # If it is a movie with the adapted channel
        title = item.contentTitle
    elif item.contentTitle:  # If the channel is not adapted
        title = item.contentTitle
    else:  # As a last resort
        title = item.title

    # We clean the title of previous format labels
    title = re.compile("\[/*COLO.*?\]", re.DOTALL).sub("", title)
    title = re.compile("\[/*B\]", re.DOTALL).sub("", title)
    title = re.compile("\[/*I\]", re.DOTALL).sub("", title)


    title = '[B]'+title+'[/B]'

    if item.contentLanguage == '':
        pass
    elif type(item.contentLanguage) == list and len(item.contentLanguage) ==1:
        title += support.typo(item.contentLanguage[0], '_ [] color kod')
    elif type(item.contentLanguage) != '':
          title += support.typo(item.contentLanguage, '_ [] color kod')
    elif type(item.contentLanguage) == list:
        title += item.contentLanguage

    if item.quality:
        title += support.typo(item.quality, '_ [] color kod')

    # season_ = support.typo(config.get_localized_string(70736), '_ [] color white bold') if (type(item.args) != bool and 'season_completed' in item.news and not item.episode) else ''
    # if season_:
    #     title += season_
    return title


def no_group(list_result_canal):
    itemlist = []
    global channels_id_name

    for i in list_result_canal:
        # support.info("NO GROUP i -> ", i)
        canale = channels_id_name[i.channel]
        canale = canale # to differentiate it from the color of the other items
        i.title = get_title(i) + " [" + canale + "]"
#        i.text_color = color3

        itemlist.append(i.clone())
    if config.get_setting('order','news') == 1:
        itemlist = sorted(itemlist, key=lambda it: it.title.lower())
    return itemlist


def group_by_channel(list_result_canal):
    global channels_id_name
    dict_canales = {}
    itemlist = []

    for i in list_result_canal:
        if i.channel not in dict_canales:
            dict_canales[i.channel] = []
        # Format title
        i.title = get_title(i)
        # We add the content to the list of each channel
        dict_canales[i.channel].append(i)

    # We add the content found in the list_result list
    for c in sorted(dict_canales):
        channel_params = channeltools.get_channel_parameters(c)
        itemlist.append(Item(channel="news", title=support.typo(channel_params['title'],'bullet bold color kod'), thumbnail=channel_params['thumbnail']))

        for i in dict_canales[c]:
            itemlist.append(i.clone())

    return itemlist


def group_by_content(list_result_canal):
    global channels_id_name
    dict_contenidos = {}
    list_result = []

    for i in list_result_canal:
        # Format title
        i.title = get_title(i)

        # Remove tildes and other special characters for the key
        import unicodedata
        try:
            new_key = i.title.lower().strip().decode("UTF-8")
            new_key = ''.join((c for c in unicodedata.normalize('NFD', new_key) if unicodedata.category(c) != 'Mn'))

        except:
            new_key = i.title

        if new_key in dict_contenidos:
            #If the content was already in the dictionary add it to the list of options ...
            dict_contenidos[new_key].append(i)
        else:  # ...but add it to the dictionary
            dict_contenidos[new_key] = [i]

    # We add the content found in the list_result list
    for v in list(dict_contenidos.values()):
        title = v[0].title
        if len(v) > 1:
            # Remove duplicate q's from the channel names list
            canales_no_duplicados = []
            for i in v:
                if i.channel not in canales_no_duplicados:
                    canales_no_duplicados.append(channels_id_name[i.channel])

            if len(canales_no_duplicados) > 1:
                canales = ', '.join([i for i in canales_no_duplicados[:-1]])
                title += config.get_localized_string(70210) % (canales, canales_no_duplicados[-1])
            else:
                title += config.get_localized_string(70211) % (', '.join([i for i in canales_no_duplicados]))

            new_item = v[0].clone(channel="news", title=title, action="show_channels", sub_list=[i.tourl() for i in v], extra=channels_id_name)
        else:
            new_item = v[0].clone(title=title)

        list_result.append(new_item)

    return sorted(list_result, key=lambda it: it.title.lower())


def show_channels(item):
    logger.debug()
    global channels_id_name
    channels_id_name = item.extra
    itemlist = []

    for i in item.sub_list:
        new_item = Item()
        new_item = new_item.fromurl(i)
        # logger.debug(new_item.tostring())
##        if new_item.contentQuality:
##            new_item.title += ' (%s)' % new_item.contentQuality
##        if new_item.language:
##            new_item.title += ' [%s]' % new_item.language
##        new_item.title += ' (%s)' % channels_id_name[new_item.channel]
        new_item.text_color = color1
        new_item.title += typo(new_item.channel, '[]')

        itemlist.append(new_item.clone())

    return itemlist


def menu_opciones(item):
    itemlist = list()
    itemlist.append(Item(channel=item.channel, title=config.get_localized_string(60525),
                         text_bold = True, thumbnail=get_thumb("setting_0.png"),
                         folder=False))
    itemlist.append(Item(channel=item.channel, action="setting_channel", extra="peliculas", title=config.get_localized_string(60526),
                         thumbnail=get_thumb("movie.png"),
                         folder=False))
    # itemlist.append(Item(channel=item.channel, action="setting_channel", extra="4K", title=config.get_localized_string(70207),
    #                      thumbnail=get_thumb("movie.png"), folder=False))
    # itemlist.append(Item(channel=item.channel, action="setting_channel", extra="infantiles", title=config.get_localized_string(60527),
    #                      thumbnail=get_thumb("children.png"),
    #                      folder=False))
    itemlist.append(Item(channel=item.channel, action="setting_channel", extra="series",
                         title=config.get_localized_string(60528),
                         thumbnail=get_thumb("tvshow.png"),
                         folder=False))
    itemlist.append(Item(channel=item.channel, action="setting_channel", extra="anime",
                         title=config.get_localized_string(60529),
                         thumbnail=get_thumb("anime.png"),
                         folder=False))
    # itemlist.append(
    #     Item(channel=item.channel, action="setting_channel", extra="castellano", title=config.get_localized_string(70212),
    #          thumbnail=get_thumb("documentary.png"), folder=False))

    # itemlist.append(Item(channel=item.channel, action="setting_channel", extra="latino", title=config.get_localized_string(70213),
    #                      thumbnail=get_thumb("documentary.png"), folder=False))

    # itemlist.append(Item(channel=item.channel, action="setting_channel", extra="torrent", title=config.get_localized_string(70214),
    #                      thumbnail=get_thumb("documentary.png"), folder=False))

    itemlist.append(Item(channel=item.channel, action="setting_channel", extra="documentales",
                         title=config.get_localized_string(60530),
                         thumbnail=get_thumb("documentary.png"),
                         folder=False))
    itemlist.append(Item(channel=item.channel, action="settings", title=config.get_localized_string(60531),
                         thumbnail=get_thumb("setting_0.png"),
                         folder=False))
    return itemlist


def settings(item):
    return platformtools.show_channel_settings(caption=config.get_localized_string(60532))


def setting_channel(item):
    channels_path = os.path.join(config.get_runtime_path(), "channels", '*.json')
    channel_language = config.get_setting("channel_language", default="auto")
    if channel_language == 'auto':
        channel_language = auto_filter()


    list_controls = []
    for infile in sorted(glob.glob(channels_path)):
        channel_id = os.path.basename(infile)[:-5]
        channel_parameters = channeltools.get_channel_parameters(channel_id)

        # Do not include if it is an inactive channel
        if not channel_parameters["active"]:
            continue

        # Do not include if the channel is in a filtered language
        if channel_language != "all" and channel_language not in str(channel_parameters["language"]) \
                and "*" not in channel_parameters["language"]:
            continue

        # Do not include if the channel does not exist 'include_in_newest' in your configuration
        include_in_newest = config.get_setting("include_in_newest_" + item.extra, channel_id)
        if include_in_newest is None:
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


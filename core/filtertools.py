# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# filtertools - is responsible for filtering results
# ------------------------------------------------------------

from builtins import object

from core import jsontools
from core.item import Item
from platformcode import config, logger
from platformcode import platformtools
from core import channeltools

TAG_TVSHOW_FILTER = "TVSHOW_FILTER"
TAG_NAME = "name"
TAG_ACTIVE = "active"
TAG_LANGUAGE = "language"
TAG_QUALITY_ALLOWED = "quality_allowed"

COLOR = {"parent_item": "yellow", "error": "red", "striped_even_active": "blue",
         "striped_even_inactive": "0xff00bfff", "striped_odd_active": "0xff008000",
         "striped_odd_inactive": "0xff00fa9a", "selected": "blue"
         }

filter_global = None

__channel__ = "filtertools"


# TODO take a look at https://pyformat.info/, you can format the style and make references directly to elements


class ResultFilter(object):
    def __init__(self, dict_filter):
        self.active = dict_filter[TAG_ACTIVE]
        self.language = dict_filter[TAG_LANGUAGE]
        self.quality_allowed = dict_filter[TAG_QUALITY_ALLOWED]

    def __str__(self):
        return "{active: '%s', language: '%s', quality_allowed: '%s'}" % (self.active, self.language, self.quality_allowed)


class Filter(object):
    def __init__(self, item, global_filter_lang_id):
        self.result = None
        self.__get_data(item, global_filter_lang_id)

    def __get_data(self, item, global_filter_lang_id):

        dict_filtered_shows = jsontools.get_node_from_file(item.channel, TAG_TVSHOW_FILTER)
        tvshow = item.show.lower().strip()

        global_filter_language = config.get_setting(global_filter_lang_id, item.channel)

        if tvshow in list(dict_filtered_shows.keys()):

            self.result = ResultFilter({TAG_ACTIVE: dict_filtered_shows[tvshow][TAG_ACTIVE],
                                        TAG_LANGUAGE: dict_filtered_shows[tvshow][TAG_LANGUAGE],
                                        TAG_QUALITY_ALLOWED: dict_filtered_shows[tvshow][TAG_QUALITY_ALLOWED]})

        # general option "do not filter"
        elif global_filter_language != 0:
            from core import channeltools
            list_controls, dict_settings = channeltools.get_channel_controls_settings(item.channel)

            for control in list_controls:
                if control["id"] == global_filter_lang_id:

                    try:
                        language = control["lvalues"][global_filter_language]
                        # logger.debug("language %s" % language)
                    except:
                        logger.error("The value associated with the code was not found '%s': %s" % (global_filter_lang_id, global_filter_language))
                        break

                    self.result = ResultFilter({TAG_ACTIVE: True, TAG_LANGUAGE: language, TAG_QUALITY_ALLOWED: []})
                    break

    def __str__(self):
        return "{'%s'}" % self.result


def access():
    """
    Returns whether or not filtertools can be used
    """
    allow = False

    if config.is_xbmc() or config.get_platform() == "mediaserver":
        allow = True

    return allow


def context(item, list_language=None, list_quality=None, exist=False):
    """
    For xbmc / kodi and mediaserver since they can show the contextual menu, a filter option is added to the configuration menu, only if it is for series.
    Depending on the place and if there is a filter, more options will be added to show.
    The context -is shown only for series-.

    @param item: eelement to get the information and see what context to add
    @type item: item
    param list_language: list of possible languages
    @type list_language: list[str]
    @param list_quality: list of possible qualities
    @type list_quality: list[str]
    @param exist: if the filter exists
    @type exist: bool
    @return: list of options to display in the context menu
    @rtype: list
    """

    # Depending on how the context is, we save it and add the filtertools options.
    if isinstance(item.context, str):
        _context = item.context.split("|")
    elif isinstance(item.context, list):
        _context = item.context
    else:
        _context = []

    if access():
        dict_data = {"title": config.get_localized_string(60426), "action": "config_item", "channel": "filtertools"}
        if list_language:
            dict_data["list_language"] = list_language
        if list_quality:
            dict_data["list_quality"] = list_quality

        added = False
        if isinstance(_context, list):
            for x in _context:
                if x and isinstance(x, dict):
                    if x["channel"] == "filtertools":
                        added = True
                        break

        if not added:
            _context.append(dict_data)

        if item.action == "play":
            if not exist:
                _context.append({"title": config.get_localized_string(60427) % item.language, "action": "save_from_context",
                                 "channel": "filtertools", "from_channel": item.channel})
            else:
                _context.append({"title": config.get_localized_string(60428) % item.language, "action": "delete_from_context",
                                 "channel": "filtertools", "from_channel": item.channel})

    return _context


def show_option(itemlist, channel, list_language, list_quality):
    if access():
        itemlist.append(Item(channel=__channel__, title=config.get_localized_string(60429) % COLOR.get("parent_item", "auto"), action="load",
                             list_language=list_language, list_quality=list_quality, from_channel=channel))

    return itemlist


def load(item):
    return mainlist(channel=item.from_channel, list_language=item.list_language, list_quality=item.list_quality)


def check_conditions(_filter, list_item, item, list_language, list_quality, quality_count=0, language_count=0):
    is_language_valid = True

    if _filter.language:
        # logger.debug("title es %s" % item.title)
        # 2nd lang

        from platformcode import unify
        _filter.language = unify.set_lang(_filter.language).upper()

        # comes from episodes
        if isinstance(item.language, list):
            # 2nd lang
            for n, lang in enumerate(item.language):
                item.language[n] = unify.set_lang(lang).upper()

            if _filter.language in item.language:
                language_count += 1
            else:
                is_language_valid = False
        # comes from findvideos
        else:
            # 2nd lang
            item.language = unify.set_lang(item.language).upper()

            if item.language.lower() == _filter.language.lower():
                language_count += 1
            else:
                is_language_valid = False

        is_quality_valid = True
        quality = ""

        if _filter.quality_allowed and item.quality != "":
            # if hasattr (item, 'quality'): # this validation is not necessary because the empty attribute is ALWAYS returned
            if item.quality.lower() in _filter.quality_allowed:
                quality = item.quality.lower()
                quality_count += 1
            else:
                is_quality_valid = False

        if is_language_valid and is_quality_valid:
            #TODO 2nd lang: we should see if it is convenient to unify the language here or not
            item.list_language = list_language
            if list_quality:
                item.list_quality = list_quality
            item.context = context(item, exist=True)
            list_item.append(item)
            # logger.debug("{0} | context: {1}".format(item.title, item.context))
            # logger.debug(" -Enlace añadido")
        elif not item.language:
            list_item.append(item)
        logger.debug(" idioma valido?: %s, item.language: %s, filter.language: %s" % (is_language_valid, item.language, _filter.language))
        logger.debug(" calidad valida?: %s, item.quality: %s, filter.quality_allowed: %s" % (is_quality_valid, quality, _filter.quality_allowed))

    return list_item, quality_count, language_count, _filter.language


def get_link(list_item, item, list_language, list_quality=None, global_filter_lang_id="filter_languages"):
    """
    Returns a list of links, if the item is correctly filtered it is added to the received list.

    @param list_item: list of links
    @type list_item: list[Item]
    @param item: element to filter
    @type item: Item
    @param list_language: list of possible languages
    @type list_language: list[str]
    @param list_quality: list of possible qualities
    @type list_quality: list[str]
    @param global_filter_lang_id: id of the filtering variable by language that is in settings
    @type global_filter_lang_id: str
    @return: Item list
    @rtype: list[Item]
    """
    logger.debug()

    # if the required fields are None we leave
    if list_item is None or item is None:
        return []

    logger.debug("total de items : %s" % len(list_item))

    global filter_global

    if not filter_global:
        filter_global = Filter(item, global_filter_lang_id).result
    logger.debug("filter: '%s' datos: '%s'" % (item.show, filter_global))

    if filter_global and filter_global.active:
        list_item, quality_count, language_count = check_conditions(filter_global, list_item, item, list_language, list_quality)[:3]
    else:
        item.context = context(item)
        list_item.append(item)

    return list_item


def get_links(list_item, item, list_language, list_quality=None, global_filter_lang_id="filter_languages"):
    """
    Returns a list of filtered links.

    @param list_item: list of links
    @type list_item: list[Item]
    @param item: element to filter
    @type item: item
    @param list_language: list of possible languages
    @type list_language: list[str]
    @param list_quality: list of possible qualities
    @type list_quality: list[str]
    @param global_filter_lang_id: id of the filtering variable by language that is in settings
    @type global_filter_lang_id: str
    @return: lista de Item
    @rtype: list[Item]
    """
    logger.debug()


    # if the required fields are None we leave
    if list_item is None or item is None:
        return []

    # if list_item is empty we go back, no platform validation is added so Plex can do global filter
    if len(list_item) == 0:
        return list_item


    second_lang = config.get_setting('second_language')

    logger.debug("total de items : %s" % len(list_item))

    new_itemlist = []
    quality_count = 0
    language_count = 0

    _filter = Filter(item, global_filter_lang_id).result
    logger.debug("filter: '%s' datos: '%s'" % (item.show, _filter))


    if _filter and _filter.active:

        for item in list_item:
            new_itemlist, quality_count, language_count, first_lang = check_conditions(_filter, new_itemlist, item, list_language, list_quality, quality_count, language_count)

        #2nd lang
        if second_lang and second_lang != 'No' and first_lang.lower() != second_lang.lower() :
            second_list= []
            _filter2 = _filter
            _filter2.language = second_lang
            for it in new_itemlist:
                if isinstance(it.language, list):
                    if not second_lang in it.language:
                        second_list.append(it)
                else:
                    second_list = new_itemlist
                    break
            for item in list_item:
                new_itemlist, quality_count, language_count, second_lang = check_conditions(_filter2, second_list, item, list_language, list_quality, quality_count, language_count)


        logger.debug("FILTERED ITEMS: %s/%s, language [%s]: %s, allowed quality %s: %s" % (len(new_itemlist), len(list_item), _filter.language, language_count, _filter.quality_allowed, quality_count))

        if len(new_itemlist) == 0:
            list_item_all = []
            for i in list_item:
                list_item_all.append(i.tourl())

            _context = [{"title": config.get_localized_string(60430) % _filter.language, "action": "delete_from_context", "channel": "filtertools", "to_channel": item.channel}]

            if _filter.quality_allowed:
                msg_quality_allowed = " y calidad %s" % _filter.quality_allowed
            else:
                msg_quality_allowed = ""

            msg_lang = ' %s' % first_lang.upper()
            if second_lang and second_lang != 'No':
                msg_lang = 's %s ni %s' % (first_lang.upper(), second_lang.upper())

            new_itemlist.append(Item(channel=__channel__, action="no_filter", list_item_all=list_item_all,
                                     show=item.show,
                                     title=config.get_localized_string(60432) % (_filter.language, msg_quality_allowed),
                                     context=_context))

    else:
        for item in list_item:
            item.list_language = list_language
            if list_quality:
                item.list_quality = list_quality
            item.context = context(item)
        new_itemlist = list_item

    return new_itemlist


def no_filter(item):
    """
    Muestra los enlaces sin filtrar

    @param item: item
    @type item: Item
    @return: lista de enlaces
    @rtype: list[Item]
    """
    logger.debug()

    itemlist = []
    for i in item.list_item_all:
        itemlist.append(Item().fromurl(i))

    return itemlist


def mainlist(channel, list_language, list_quality):
    """
    Shows a list of the leaked series

    @param channel: channel name to get filtered series
    @type channel: str
    @param list_language: channel language list
    @type list_language: list[str]
    @param list_quality: channel quality list
    @type list_quality: list[str]
    @return: Item list
    @rtype: list[Item]
    """
    logger.debug()
    itemlist = []
    dict_series = jsontools.get_node_from_file(channel, TAG_TVSHOW_FILTER)

    idx = 0
    for tvshow in sorted(dict_series):

        if idx % 2 == 0:
            if dict_series[tvshow][TAG_ACTIVE]:
                tag_color = COLOR.get("striped_even_active", "auto")
            else:
                tag_color = COLOR.get("striped_even_inactive", "auto")
        else:
            if dict_series[tvshow][TAG_ACTIVE]:
                tag_color = COLOR.get("striped_odd_active", "auto")
            else:
                tag_color = COLOR.get("striped_odd_inactive", "auto")

        idx += 1
        name = dict_series.get(tvshow, {}).get(TAG_NAME, tvshow)
        activo = config.get_localized_string(60433)
        if dict_series[tvshow][TAG_ACTIVE]:
            activo = ""
        title = config.get_localized_string(60434) % (tag_color, name, activo)

        itemlist.append(Item(channel=__channel__, action="config_item", title=title, show=name,
                             list_language=list_language, list_quality=list_quality, from_channel=channel))

    if len(itemlist) == 0:
        itemlist.append(Item(channel=channel, action="mainlist", title=config.get_localized_string(60435)))

    return itemlist


def config_item(item):
    """
    displays a filtered series for your setup

    @param item: item
    @type item: Item
    """
    logger.debug()
    logger.debug("item %s" % item.tostring())

    # WE GET THE JSON DATA
    dict_series = jsontools.get_node_from_file(item.from_channel, TAG_TVSHOW_FILTER)

    tvshow = item.show.lower().strip()
    default_lang = ''

    channel_parameters = channeltools.get_channel_parameters(item.from_channel)
    list_language = channel_parameters["filter_languages"]
    try:
        if channel_parameters["filter_languages"] != '' and len(list_language) > 0:
            default_lang = list_language[1]
    except:
        pass

    if default_lang == '':
        platformtools.dialog_notification("FilterTools", "There are no defined languages")
        return
    else:
        lang_selected = dict_series.get(tvshow, {}).get(TAG_LANGUAGE, default_lang)
        list_quality = dict_series.get(tvshow, {}).get(TAG_QUALITY_ALLOWED, [x.lower() for x in item.list_quality])
        # logger.debug("lang selected {}".format(lang_selected))
        # logger.debug("list quality {}".format(list_quality))

        active = True
        custom_button = {'visible': False}
        allow_option = False
        if item.show.lower().strip() in dict_series:
            allow_option = True
            active = dict_series.get(item.show.lower().strip(), {}).get(TAG_ACTIVE, False)
            custom_button = {'label': config.get_localized_string(60437), 'function': 'delete', 'visible': True, 'close': True}

        list_controls = []

        if allow_option:
            active_control = {
                "id": "active",
                "type": "bool",
                "label": config.get_localized_string(60438),
                "color": "",
                "default": active,
                "enabled": allow_option,
                "visible": allow_option,
            }
            list_controls.append(active_control)

        language_option = {
            "id": "language",
            "type": "list",
            "label": config.get_localized_string(60439),
            # "color": "0xFFee66CC",
            "default": item.list_language.index(lang_selected),
            "enabled": True,
            "visible": True,
            "lvalues": item.list_language
        }
        list_controls.append(language_option)

        if item.list_quality:
            list_controls_calidad = [
                {
                    "id": "textoCalidad",
                    "type": "label",
                    "label": "Calidad permitida",
                    "color": "0xffC6C384",
                    "enabled": True,
                    "visible": True,
                },
            ]
            for element in sorted(item.list_quality, key=str.lower):
                list_controls_calidad.append({
                    "id": element,
                    "type": "bool",
                    "label": element,
                    "default": (False, True)[element.lower() in list_quality],
                    "enabled": True,
                    "visible": True,
                })

            # we concatenate list_controls with list_controls_quality
            list_controls.extend(list_controls_calidad)

        title = config.get_localized_string(60441) % (COLOR.get("selected", "auto"), item.show)

        platformtools.show_channel_settings(list_controls=list_controls, callback='save', item=item,
                                            caption=title, custom_button=custom_button)


def delete(item, dict_values):
    logger.debug()

    if item:
        dict_series = jsontools.get_node_from_file(item.from_channel, TAG_TVSHOW_FILTER)
        tvshow = item.show.strip().lower()

        heading = config.get_localized_string(60442)
        line1 = config.get_localized_string(60443) % (COLOR.get("selected", "auto"), item.show.strip())

        if platformtools.dialog_yesno(heading, line1) == 1:
            lang_selected = dict_series.get(tvshow, {}).get(TAG_LANGUAGE, "")
            dict_series.pop(tvshow, None)

            result, json_data = jsontools.update_node(dict_series, item.from_channel, TAG_TVSHOW_FILTER)

            sound = False
            if result:
                message = config.get_localized_string(60444)
            else:
                message = config.get_localized_string(60445)
                sound = True

            heading = "%s [%s]" % (item.show.strip(), lang_selected)
            platformtools.dialog_notification(heading, message, sound=sound)

            if item.action in ["findvideos", "play"]:
                platformtools.itemlist_refresh()


def save(item, dict_data_saved):
    """
    Save the configured values ​​in the window

    @param item: item
    @type item: Item
    @param dict_data_saved: dictionary with saved data
    @type dict_data_saved: dict
    """
    logger.debug()

    if item and dict_data_saved:
        logger.debug('item: %s\ndatos: %s' % (item.tostring(), dict_data_saved))

        if item.from_channel == "videolibrary":
            item.from_channel = item.contentChannel
        dict_series = jsontools.get_node_from_file(item.from_channel, TAG_TVSHOW_FILTER)
        tvshow = item.show.strip().lower()

        logger.debug("Data is updated")

        list_quality = []
        for _id, value in list(dict_data_saved.items()):
            if _id in item.list_quality and value:
                list_quality.append(_id.lower())

        lang_selected = item.list_language[dict_data_saved[TAG_LANGUAGE]]
        dict_filter = {TAG_NAME: item.show, TAG_ACTIVE: dict_data_saved.get(TAG_ACTIVE, True),
                       TAG_LANGUAGE: lang_selected, TAG_QUALITY_ALLOWED: list_quality}
        dict_series[tvshow] = dict_filter

        result, json_data = jsontools.update_node(dict_series, item.from_channel, TAG_TVSHOW_FILTER)

        sound = False
        if result:
            message = config.get_localized_string(60446)
        else:
            message = config.get_localized_string(70593)
            sound = True

        heading = "%s [%s]" % (item.show.strip(), lang_selected)
        platformtools.dialog_notification(heading, message, sound=sound)

        if item.from_action in ["findvideos", "play"]:
            platformtools.itemlist_refresh()


def save_from_context(item):
    """
    Save the filter through the context menu

    @param item: item
    @type item: item
    """
    logger.debug()

    dict_series = jsontools.get_node_from_file(item.from_channel, TAG_TVSHOW_FILTER)
    tvshow = item.show.strip().lower()

    dict_filter = {TAG_NAME: item.show, TAG_ACTIVE: True, TAG_LANGUAGE: item.language, TAG_QUALITY_ALLOWED: []}
    dict_series[tvshow] = dict_filter

    result, json_data = jsontools.update_node(dict_series, item.from_channel, TAG_TVSHOW_FILTER)

    sound = False
    if result:
        message = "SAVED FILTER"
    else:
        message = "Error saving to disk"
        sound = True

    heading = "%s [%s]" % (item.show.strip(), item.language)
    platformtools.dialog_notification(heading, message, sound=sound)

    if item.from_action in ["findvideos", "play"]:
        platformtools.itemlist_refresh()


def delete_from_context(item):
    """
    Delete the filter through the context menu

    @param item: item
    @type item: item
    """
    logger.debug()

    # We come from get_links and no result has been obtained, in context menu and we delete
    if item.to_channel != "":
        item.from_channel = item.to_channel

    dict_series = jsontools.get_node_from_file(item.from_channel, TAG_TVSHOW_FILTER)
    tvshow = item.show.strip().lower()

    lang_selected = dict_series.get(tvshow, {}).get(TAG_LANGUAGE, "")
    dict_series.pop(tvshow, None)

    result, json_data = jsontools.update_node(dict_series, item.from_channel, TAG_TVSHOW_FILTER)

    sound = False
    if result:
        message = "FILTER REMOVED"
    else:
        message = "Error saving to disk"
        sound = True

    heading = "%s [%s]" % (item.show.strip(), lang_selected)
    platformtools.dialog_notification(heading, message, sound=sound)

    if item.from_action in ["findvideos", "play", "no_filter"]:  # 'no_filter' es el mismo caso que L#601
        platformtools.itemlist_refresh()

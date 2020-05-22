# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# platformtools
# ------------------------------------------------------------
# Tools responsible for adapting the different dialog boxes to a specific platform.
# version 2.0
# ------------------------------------------------------------

from __future__ import division
from __future__ import absolute_import
from past.utils import old_div
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urllib
else:
    import urllib

import os, xbmc, xbmcgui, xbmcplugin

from channelselector import get_thumb
from core import channeltools
from core import trakt_tools, scrapertools
from core.item import Item
from platformcode import logger, config, unify

addon = config.__settings__
addon_icon = os.path.join( addon.getAddonInfo( "path" ), "logo.png" )

class XBMCPlayer(xbmc.Player):

    def __init__(self, *args):
        pass


xbmc_player = XBMCPlayer()

def makeMessage(line1, line2, line3):
    message = line1
    if line2:
        message += '\n' + line2
    if line3:
        message += '\n' + line3
    return message

def dialog_ok(heading, line1, line2="", line3=""):
    dialog = xbmcgui.Dialog()
    return dialog.ok(heading, makeMessage(line1, line2, line3))


def dialog_notification(heading, message, icon=3, time=5000, sound=True):
    dialog = xbmcgui.Dialog()
    try:
        l_icono = xbmcgui.NOTIFICATION_INFO, xbmcgui.NOTIFICATION_WARNING, xbmcgui.NOTIFICATION_ERROR, addon_icon
        dialog.notification(heading, message, l_icono[icon], time, sound)
    except:
        dialog_ok(heading, message)


def dialog_yesno(heading, line1, line2="", line3="", nolabel="No", yeslabel="Si", autoclose=0, customlabel=None):
    # customlabel only on kodi 19
    dialog = xbmcgui.Dialog()
    if config.get_platform() == 'kodi-matrix':
        if autoclose:
            return dialog.yesno(heading, makeMessage(line1, line2, line3), nolabel=nolabel, yeslabel=yeslabel, customlabel=customlabel, autoclose=autoclose)
        else:
            return dialog.yesno(heading, makeMessage(line1, line2, line3), nolabel=nolabel, yeslabel=yeslabel, customlabel=customlabel)
    else:
        if autoclose:
            return dialog.yesno(heading, makeMessage(line1, line2, line3), nolabel=nolabel, yeslabel=yeslabel, autoclose=autoclose)
        else:
            return dialog.yesno(heading, makeMessage(line1, line2, line3), nolabel=nolabel, yeslabel=yeslabel)


def dialog_select(heading, _list, preselect=0):
    return xbmcgui.Dialog().select(heading, _list, preselect=preselect)


def dialog_multiselect(heading, _list, autoclose=0, preselect=[], useDetails=False):
    return xbmcgui.Dialog().multiselect(heading, _list, autoclose=autoclose, preselect=preselect, useDetails=useDetails)


def dialog_progress(heading, line1, line2=" ", line3=" "):
    dialog = xbmcgui.DialogProgress()
    dialog.create(heading, makeMessage(line1, line2, line3))
    return dialog


def dialog_progress_bg(heading, message=""):
    try:
        dialog = xbmcgui.DialogProgressBG()
        dialog.create(heading, message)
        return dialog
    except:
        return dialog_progress(heading, message)


def dialog_input(default="", heading="", hidden=False):
    keyboard = xbmc.Keyboard(default, heading, hidden)
    keyboard.doModal()
    if keyboard.isConfirmed():
        return keyboard.getText()
    else:
        return None


def dialog_numeric(_type, heading, default=""):
    dialog = xbmcgui.Dialog()
    d = dialog.numeric(_type, heading, default)
    return d


def dialog_textviewer(heading, text):  # available from kodi 16
    return xbmcgui.Dialog().textviewer(heading, text)


def dialog_browse(_type, heading, default=""):
    dialog = xbmcgui.Dialog()
    d = dialog.browse(_type, heading, 'files')
    return d


def itemlist_refresh():
    pos = Item().fromurl(xbmc.getInfoLabel('ListItem.FileNameAndPath')).itemlistPosition
    logger.info('Current position: ' + str(pos))
    xbmc.executebuiltin("Container.Refresh")

    while Item().fromurl(xbmc.getInfoLabel('ListItem.FileNameAndPath')).itemlistPosition != pos:
        win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
        cid = win.getFocusId()
        ctl = win.getControl(cid)
        ctl.selectItem(pos)


def itemlist_update(item, replace=False):
    if replace:  # reset the path history
        xbmc.executebuiltin("Container.Update(" + sys.argv[0] + "?" + item.tourl() + ", replace)")
    else:
        xbmc.executebuiltin("Container.Update(" + sys.argv[0] + "?" + item.tourl() + ")")


def render_items(itemlist, parent_item):
    """
    Function used to render itemlist on kodi
    """
    logger.info('START render_items')
    thumb_type = config.get_setting('video_thumbnail_type')
    from specials import shortcuts
    from core import httptools
    _handle = int(sys.argv[1])
    default_fanart = config.get_fanart()
    def_context_commands = shortcuts.context()

    # for adding extendedinfo to contextual menu, if it's used
    has_extendedinfo = xbmc.getCondVisibility('System.HasAddon(script.extendedinfo)')
    # for adding superfavourites to contextual menu, if it's used
    sf_file_path = xbmc.translatePath("special://home/addons/plugin.program.super.favourites/LaunchSFMenu.py")
    check_sf = os.path.exists(sf_file_path)
    superfavourites = check_sf and xbmc.getCondVisibility('System.HasAddon("plugin.program.super.favourites")')

    # if it's not a list, do nothing
    if not isinstance(itemlist, list):
        return
    # if there's no item, add "no elements" item
    if not len(itemlist):
        itemlist.append(Item(title=config.get_localized_string(60347), thumbnail=get_thumb('nofolder.png')))

    dirItems = []
    for n, item in enumerate(itemlist):
        item.itemlistPosition = n + 1
        item_url = item.tourl()

        if item.category == "":
            item.category = parent_item.category
        if not item.title:
            item.title = ''
        # If there is no action or it is findvideos / play, folder = False because no listing will be returned
        if item.action in ['play', '']:
            item.folder = False
        if item.fanart == "":
            item.fanart = parent_item.fanart
        if item.action == 'play' and thumb_type == 1 and not item.forcethumb:
            item.thumbnail = "https://github.com/kodiondemand/media/raw/master/resources/servers/" + item.server.lower() + '.png'

        # if cloudflare and cloudscraper is used, cookies are needed to display images taken from site
        # before checking domain (time consuming), checking if tmdb failed (so, images scraped from website are used)
        if item.action in ['findvideos'] and not item.infoLabels['tmdb_id']:
            # faster but ugly way of checking
            for d in httptools.FORCE_CLOUDSCRAPER_LIST:
                if d + '/' in item.url:
                    item.thumbnail = httptools.get_url_headers(item.thumbnail)
                    item.fanart = httptools.get_url_headers(item.fanart)
                    break

        icon_image = "DefaultFolder.png" if item.folder else "DefaultVideo.png"
        listitem = xbmcgui.ListItem(item.title)
        listitem.setArt({'icon': icon_image, 'thumb': item.thumbnail, 'poster': item.thumbnail,
                         'fanart': item.fanart if item.fanart else default_fanart})

        if config.get_setting("player_mode") == 1 and item.action == "play":
            listitem.setProperty('IsPlayable', 'true')

        set_infolabels(listitem, item)

        # context menu
        if parent_item.channel != 'special':
            context_commands = def_context_commands + set_context_commands(item, item_url, parent_item, has_extendedinfo=has_extendedinfo, superfavourites=superfavourites)
        else:
            context_commands = def_context_commands
        listitem.addContextMenuItems(context_commands)

        dirItems.append(('%s?%s' % (sys.argv[0], item_url), listitem, item.folder))
    xbmcplugin.addDirectoryItems(_handle, dirItems)

    if parent_item.list_type == '':
        breadcrumb = parent_item.category.capitalize()
    else:
        if 'similar' in parent_item.list_type:
            if parent_item.contentTitle != '':
                breadcrumb = config.get_localized_string(70693) + parent_item.contentTitle
            else:
                breadcrumb = config.get_localized_string(70693) + parent_item.contentSerieName
        else:
            breadcrumb = config.get_localized_string(70693)

    xbmcplugin.setPluginCategory(handle=_handle, category=breadcrumb)

    set_view_mode(itemlist[0], parent_item)

    xbmcplugin.endOfDirectory(_handle)
    logger.info('END render_items')


def getCurrentView(item=None, parent_item=None):
    if not parent_item:
        info = xbmc.getInfoLabel('Container.FolderPath')
        if not info:
            return None, None
        parent_item = Item().fromurl(info)
    if not item:
        info = xbmc.getInfoLabel('Container.ListItem(1).FileNameAndPath')
        if not info:
            return None, None
        item = Item().fromurl(info) if info else Item()
    parent_actions = ['peliculas', 'novedades', 'search', 'get_from_temp', 'newest', 'discover_list', 'new_search', 'channel_search']

    if parent_item.action == 'findvideos' or (parent_item.action in ['channel_search', 'new_search'] and parent_item.infoLabels['tmdb_id']):
        return 'server', 'addons' if config.get_setting('touch_view') else ''

    elif parent_item.action == 'mainlist':
        return 'channel', 'addons' if config.get_setting('touch_view') else ''

    elif (item.contentType in ['movie'] and parent_item.action in parent_actions) \
            or (item.channel in ['videolibrary'] and parent_item.action in ['list_movies']) \
            or (parent_item.channel in ['favorites'] and parent_item.action in ['mainlist']) \
            or parent_item.action in ['now_on_tv', 'now_on_misc', 'now_on_misc_film', 'mostrar_perfil']:
        return 'movie', 'movies'

    elif (item.contentType in ['tvshow'] and parent_item.action in parent_actions) \
            or (item.channel in ['videolibrary'] and parent_item.action in ['list_tvshows']):
        return 'tvshow', 'tvshows'

    elif parent_item.action in ['get_seasons']:
        return 'season', 'tvshows'

    elif parent_item.action in ['episodios', 'get_episodes'] or item.contentType == 'episode':
        return 'episode', 'tvshows'

    else:
        return 'addon', 'addons' if config.get_setting('touch_view') else ''


def set_view_mode(item, parent_item):
    def reset_view_mode():
        for mode in ['addon','channel','movie','tvshow','season','episode','server']:
            config.set_setting('skin_name', xbmc.getSkinDir())
            config.set_setting('view_mode_%s' % mode, config.get_localized_string(70003) + ' , 0')

    if xbmc.getSkinDir() != config.get_setting('skin_name') or not config.get_setting('skin_name'):
        reset_view_mode()
        xbmcplugin.setContent(handle=int(sys.argv[1]), content='')
        xbmc.executebuiltin('Container.SetViewMode(%s)' % 55)

    content, Type = getCurrentView(item, parent_item)
    if content:
        mode = int(config.get_setting('view_mode_%s' % content).split(',')[-1])
        if mode == 0:
            logger.info('default mode')
            mode = 55
        xbmcplugin.setContent(handle=int(sys.argv[1]), content=Type)
        xbmc.executebuiltin('Container.SetViewMode(%s)' % mode)
        logger.info('TYPE: ' + Type + ' - ' + 'CONTENT: ' + content)


# def render_items_old(itemlist, parent_item):
#     """
#     Function responsible for displaying the itemlist in kodi, the itemlist and the item it comes from are passed as parameters
#     @type itemlist: list
#     @param itemlist: list of elements to show

#     @type parent_item: item
#     @param parent_item: parent element
#     """
#     logger.info('START render_items')
#     from core import httptools

#     # If the itemlist is not a list we leave
#     if not isinstance(itemlist, list):
#         return

#     if parent_item.start:
#         menu_icon = get_thumb('menu.png')
#         menu = Item(channel="channelselector", action="getmainlist", viewmode="movie", thumbnail=menu_icon, title='Menu')
#         itemlist.insert(0, menu)

#     # If there is no item, we show a notice
#     if not len(itemlist):
#         itemlist.append(Item(title=config.get_localized_string(60347), thumbnail=get_thumb('nofolder.png')))

#     genre = False
#     if 'nero' in parent_item.title:
#         genre = True
#         anime = False
#         if 'anime' in channeltools.get_channel_parameters(parent_item.channel)['categories']:
#             anime = True
#     # try:
#     #     force_unify = channeltools.get_channel_parameters(parent_item.channel)['force_unify']
#     # except:
#     force_unify = False

#     unify_enabled = False

#     has_extendedinfo = xbmc.getCondVisibility('System.HasAddon(script.extendedinfo)')

#     # Add SuperFavourites to context menu (1.0.53 or higher required)
#     sf_file_path = xbmc.translatePath("special://home/addons/plugin.program.super.favourites/LaunchSFMenu.py")
#     check_sf = os.path.exists(sf_file_path)
#     superfavourites = check_sf and xbmc.getCondVisibility('System.HasAddon("plugin.program.super.favourites")')
#     # try:
#     #     if channeltools.get_channel_parameters(parent_item.channel)['adult']:
#     #         unify_enabled = False
#     # except:
#     #     pass
#     # logger.debug('unify_enabled: %s' % unify_enabled)

#     # We go through the itemlist
#     for item in itemlist:
#         # logger.debug(item)
#         # If the item does not contain a category, we will add the parent item
#         item_url = item.tourl()
#         if item.category == "":
#             item.category = parent_item.category

#         # If title does not exist, we start it as str, to avoid "NoType" mistakes
#         if not item.title:
#             item.title = ''

#         # If there is no action or it is findvideos / play, folder = False because no listing will be returned
#         if item.action in ['play', '']:
#             item.folder = False

#         # If the item does not contain fanart, we put the one of the parent item
#         if item.fanart == "":
#             item.fanart = parent_item.fanart

#         if genre:
#             valid_genre = True
#             thumb = get_thumb(item.title, auto=True)
#             if thumb != '':
#                 item.thumbnail = thumb
#                 valid_genre = True
#             elif anime:
#                 valid_genre = True
#         elif (('siguiente' in item.title.lower() and '>' in item.title) or ('pagina:' in item.title.lower())):
#             item.thumbnail = get_thumb("next.png")
#         elif 'add' in item.action:
#             if 'pelicula' in item.action:
#                 item.thumbnail = get_thumb("add_to_videolibrary.png")
#             elif 'serie' in item.action:
#                 item.thumbnail = get_thumb("add_to_videolibrary.png")

#         if (unify_enabled or force_unify) and parent_item.channel not in ['kodfavourites']:
#             # Format title with unify
#             item = unify.title_format(item)
#         else:
#             # Format title method old school
#             if item.text_color:
#                 item.title = '[COLOR %s]%s[/COLOR]' % (item.text_color, item.title)
#             if item.text_bold:
#                 item.title = '[B]%s[/B]' % item.title
#             if item.text_italic:
#                 item.title = '[I]%s[/I]' % item.title

#         # Add headers to images if they are on a server with cloudflare
#         if item.action == 'play':
#             item.thumbnail = unify.thumbnail_type(item)
#         else:
#             item.thumbnail = httptools.get_url_headers(item.thumbnail)
#         item.fanart = httptools.get_url_headers(item.fanart)

#         # Icon Image for folder and video
#         if item.folder:
#             icon_image = "DefaultFolder.png"
#         else:
#             icon_image = "DefaultVideo.png"

#         # fanart
#         if item.fanart:
#             fanart = item.fanart
#         else:
#             fanart = config.get_fanart()

#         # Create listitem
#         listitem = xbmcgui.ListItem(item.title)

#         # values icon, thumb or poster are skin dependent.. so we set all to avoid problems
#         # if not exists thumb it's used icon value
#         if config.get_platform(True)['num_version'] >= 16.0:
#             listitem.setArt({'icon': icon_image, 'thumb': item.thumbnail, 'poster': item.thumbnail,
#                              'fanart': fanart})
#         else:
#             listitem.setIconImage(icon_image)
#             listitem.setThumbnailImage(item.thumbnail)
#             listitem.setProperty('fanart_image', fanart)

#         # No need it, use fanart instead
#         # xbmcplugin.setPluginFanart(int(sys.argv[1]), os.path.join(config.get_runtime_path(), "fanart.jpg"))

#         # This option is to be able to use the xbmcplugin.setResolvedUrl()
#         # if item.isPlayable == True or (config.get_setting("player_mode") == 1 and item.action == "play"):
#         if config.get_setting("player_mode") == 1 and item.action == "play":
#             listitem.setProperty('IsPlayable', 'true')

#         # Add infoLabels
#         set_infolabels(listitem, item)

#         # Do not drag plot if it is not a movie / series / season / episode
#         if item.plot and item.contentType not in ['movie', 'tvshow', 'season', 'episode']:
#             item.__dict__['infoLabels'].pop('plot')

#         # Mount context menu
#         if parent_item.channel != 'special':
#             context_commands = set_context_commands(item, item_url, parent_item, has_extendedinfo=has_extendedinfo, superfavourites=superfavourites)
#         else:
#             context_commands = []
#         # Add context menu
#         if config.get_platform(True)['num_version'] >= 17.0 and parent_item.list_type == '':
#             listitem.addContextMenuItems(context_commands)
#         elif parent_item.list_type == '':
#             listitem.addContextMenuItems(context_commands, replaceItems=True)

#         from specials import shortcuts
#         context_commands += shortcuts.context()

#         if not item.totalItems:
#             item.totalItems = 0
#         xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url='%s?%s' % (sys.argv[0], item_url),
#                                     listitem=listitem, isFolder=item.folder,
#                                     totalItems=item.totalItems)

#     # Set types of views ...
#     if config.get_setting("forceview"):                                         # ...force according to the viewcontent
#         xbmcplugin.setContent(int(sys.argv[1]), parent_item.viewcontent)

#     elif parent_item.channel not in ["channelselector", "", "kodfavourites"]:     # ... or according to the channel
#         xbmcplugin.setContent(int(sys.argv[1]), "movies")

#     elif parent_item.channel == "kodfavourites" and parent_item.action == 'mostrar_perfil':
#         xbmcplugin.setContent(int(sys.argv[1]), "movies")

#     # set "breadcrumb"
#     if parent_item.list_type == '':
#         breadcrumb = parent_item.category.capitalize()
#     else:
#         if 'similar' in parent_item.list_type:
#             if parent_item.contentTitle != '':
#                 breadcrumb = config.get_localized_string(70693) + parent_item.contentTitle
#             else:
#                 breadcrumb = config.get_localized_string(70693) + parent_item.contentSerieName
#         else:
#             breadcrumb = config.get_localized_string(70693)

#     xbmcplugin.setPluginCategory(handle=int(sys.argv[1]), category=breadcrumb)

#     # Do not sort items
#     xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_NONE)

#     # We close the directory
#     xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)

#     # Fix the view
#     # if config.get_setting("forceview"):
#     #     viewmode_id = get_viewmode_id(parent_item)
#     #     xbmc.executebuiltin("Container.SetViewMode(%s)" % viewmode_id)
#     # if parent_item.mode in ['silent', 'get_cached', 'set_cache', 'finish']:
#     #     xbmc.executebuiltin("Container.SetViewMode(500)")

#     logger.info('END render_items')


# def get_viewmode_id(parent_item):
#     # viewmode_json would have to save it in a file and create a method for the user to set their preferences in:
#     # user_files, user_movies, user_tvshows, user_season and user_episodes.
#     viewmode_json = {'skin.confluence': {'default_files': 50,
#                                          'default_movies': 515,
#                                          'default_tvshows': 508,
#                                          'default_seasons': 503,
#                                          'default_episodes': 504,
#                                          'view_list': 50,
#                                          'view_thumbnails': 500,
#                                          'view_movie_with_plot': 503},
#                      'skin.estuary': {'default_files': 50,
#                                       'default_movies': 54,
#                                       'default_tvshows': 502,
#                                       'default_seasons': 500,
#                                       'default_episodes': 53,
#                                       'view_list': 50,
#                                       'view_thumbnails': 500,
#                                       'view_movie_with_plot': 54}}

#     # If the parent_item had a viewmode set we use that view ...
#     if parent_item.viewmode == 'movie':
#         # We replace the old viewmode 'movie' with 'thumbnails'
#         parent_item.viewmode = 'thumbnails'

#     if parent_item.viewmode in ["list", "movie_with_plot", "thumbnails"]:
#         view_name = "view_" + parent_item.viewmode

#         '''elif isinstance(parent_item.viewmode, int):
#             # only for debug
#             viewName = parent_item.viewmode'''

#     # ...otherwise we put the default view according to the viewcontent
#     else:
#         view_name = "default_" + parent_item.viewcontent

#     skin_name = xbmc.getSkinDir()
#     if skin_name not in viewmode_json:
#         skin_name = 'skin.confluence'
#     view_skin = viewmode_json[skin_name]
#     return view_skin.get(view_name, 50)


def set_infolabels(listitem, item, player=False):
    """
    Method to pass the information to the listitem (see tmdb.set_InfoLabels())
    item.infoLabels is a dictionary with the key / value pairs described in:
    http://mirrors.xbmc.org/docs/python-docs/14.x-helix/xbmcgui.html#ListItem-setInfo
    https://kodi.wiki/view/InfoLabels
    @param listitem: xbmcgui.ListItem object
    @type listitem: xbmcgui.ListItem
    @param item: Item object that represents a movie, series or chapter
    @type item: item
    """

    infoLabels_dict = {'aired': 'aired', 'album': 'album', 'artist': 'artist', 'cast': 'cast',
                       'castandrole': 'castandrole', 'tmdb_id': 'code', 'code': 'code', 'country': 'country',
                       'credits': 'credits', 'release_date': 'dateadded', 'dateadded': 'dateadded', 'dbid': 'dbid',
                       'director': 'director', 'duration': 'duration', 'episode': 'episode',
                       'episodio_sinopsis': 'episodeguide', 'episodio_air_date': 'None', 'episodio_imagen': 'None',
                       'episodio_titulo': 'title', 'episodio_vote_average': 'rating', 'episodio_vote_count': 'votes',
                       'fanart': 'None', 'genre': 'genre', 'homepage': 'None', 'imdb_id': 'imdbnumber',
                       'imdbnumber': 'imdbnumber', 'in_production': 'None', 'last_air_date': 'lastplayed',
                       'mediatype': 'mediatype', 'mpaa': 'mpaa', 'number_of_episodes': 'None',
                       'number_of_seasons': 'None', 'original_language': 'None', 'originaltitle': 'originaltitle',
                       'overlay': 'overlay', 'poster_path': 'path', 'popularity': 'None', 'playcount': 'playcount',
                       'plot': 'plot', 'plotoutline': 'plotoutline', 'premiered': 'premiered', 'quality': 'None',
                       'rating': 'rating', 'season': 'season', 'set': 'set', 'setid': 'setid',
                       'setoverview': 'setoverview', 'showlink': 'showlink', 'sortepisode': 'sortepisode',
                       'sortseason': 'sortseason', 'sorttitle': 'sorttitle', 'status': 'status', 'studio': 'studio',
                       'tag': 'tag', 'tagline': 'tagline', 'temporada_air_date': 'None', 'temporada_nombre': 'None',
                       'temporada_num_episodios': 'None', 'temporada_poster': 'None', 'title': 'title',
                       'top250': 'top250', 'tracknumber': 'tracknumber', 'trailer': 'trailer', 'thumbnail': 'None',
                       'tvdb_id': 'None', 'tvshowtitle': 'tvshowtitle', 'type': 'None', 'userrating': 'userrating',
                       'url_scraper': 'None', 'votes': 'votes', 'writer': 'writer', 'year': 'year'}
    if item.infoLabels:
        try:
            infoLabels_kodi = {infoLabels_dict[label_tag]: item.infoLabels[label_tag] for label_tag, label_value in list(item.infoLabels.items()) if infoLabels_dict[label_tag] != 'None'}
            listitem.setInfo("video", infoLabels_kodi)
        except:
            listitem.setInfo("video", item.infoLabels)
            # logger.error(item.infoLabels)

    # if item.infoLabels:
    #     if 'mediatype' not in item.infoLabels:
    #         item.infoLabels['mediatype'] = item.contentType
    #
    #     try:
    #         for label_tag, label_value in list(item.infoLabels.items()):
    #             try:
    #                 # logger.debug(str(label_tag) + ': ' + str(infoLabels_dict[label_tag]))
    #                 if infoLabels_dict[label_tag] != 'None':
    #                     infoLabels_kodi.update({infoLabels_dict[label_tag]: item.infoLabels[label_tag]})
    #             except:
    #                 continue
    #
    #         listitem.setInfo("video", infoLabels_kodi)
    #
    #     except:
    #         listitem.setInfo("video", item.infoLabels)
    #         logger.error(item.infoLabels)
    #         logger.error(infoLabels_kodi)
    #
    # if player and not item.contentTitle:
    #     listitem.setInfo("video", {"Title": item.title})
    #
    # elif not player:
    #     listitem.setInfo("video", {"Title": item.title})


def set_context_commands(item, item_url, parent_item, **kwargs):
    """
    Function to generate context menus.
        1. Based on the data in item.context
            a. Old method item.context type str separating options by "|" (example: item.context = "1 | 2 | 3")
                (only predefined)
            b. List method: item.context is a list with the different menu options:
                - Predefined: A predefined option will be loaded with a name.
                    item.context = ["1", "2", "3"]

                - dict (): The current item will be loaded modifying the fields included in the dict () in case of
                    modify the channel and action fields these will be saved in from_channel and from_action.
                    item.context = [{"title": "Name of the menu", "action": "action of the menu", "channel": "menu channel"}, {...}]

        2. Adding options according to criteria
            Options can be added to the context menu to items that meet certain conditions.


        3. Adding options to all items
            Options can be added to the context menu for all items

        4. You can disable the context menu options by adding a command 'no_context' to the item.context.
            The options that Kodi, the skin or another added add to the contextual menu cannot be disabled.

    @param item: element that contains the contextual menus
    @type item: item
    @param parent_item:
    @type parent_item: item
    """
    context_commands = []
    # num_version_xbmc = config.get_platform(True)['num_version']

    # Create a list with the different options included in item.context
    if isinstance(item.context, str):
        context = item.context.split("|")
    elif isinstance(item.context, list):
        context = item.context
    else:
        context = []

    # Options according to item.context
    for command in context:
        # Predefined
        if isinstance(command, str):
            if command == "no_context":
                return []

        # Dict format
        if isinstance(command, dict):
            # The dict parameters are overwritten to the new context_item in case of overwriting "action" and
            # "channel", the original data is saved in "from_action" and "from_channel"
            if "action" in command:
                command["from_action"] = item.action
            if "channel" in command:
                command["from_channel"] = item.channel

            # If you are not inside Alphavorites and there are the contexts for Alphavorites, discard them.
            # (it happens when going to a link of alfavoritos, if this is cloned in the channel)
            if parent_item.channel != 'kodfavorites' and 'i_perfil' in command and 'i_enlace' in command:
                continue

            if "goto" in command:
                context_commands.append((command["title"], "XBMC.Container.Refresh (%s?%s)" % (sys.argv[0], item.clone(**command).tourl())))
            else:
                context_commands.append((command["title"], "XBMC.RunPlugin(%s?%s)" % (sys.argv[0], item.clone(**command).tourl())))
    # Do not add more predefined options if you are inside kodfavoritos
    if parent_item.channel == 'kodfavorites':
        return context_commands
        # Options according to criteria, only if the item is not a tag, nor is it "Add to the video library", etc...
    if item.action and item.action not in ["add_pelicula_to_library", "add_serie_to_library", "buscartrailer", "actualizar_titulos"]:
        # Show information: if the item has a plot, we assume that it is a series, season, chapter or movie
        # if item.infoLabels['plot'] and (num_version_xbmc < 17.0 or item.contentType == 'season'):
        #     context_commands.append((config.get_localized_string(60348), "XBMC.Action(Info)"))

        # ExtendedInfo: If the addon is installed and a series of conditions are met
        if kwargs.get('has_extendedinfo') \
                and config.get_setting("extended_info") == True:
            if item.contentType == "episode" and item.contentEpisodeNumber and item.contentSeason \
                    and (item.infoLabels['tmdb_id'] or item.contentSerieName):
                param = "tvshow_id =%s, tvshow=%s, season=%s, episode=%s" \
                        % (item.infoLabels['tmdb_id'], item.contentSerieName, item.contentSeason,
                           item.contentEpisodeNumber)
                context_commands.append(("ExtendedInfo", "XBMC.RunScript(script.extendedinfo,info=extendedepisodeinfo,%s)" % param))

            elif item.contentType == "season" and item.contentSeason \
                    and (item.infoLabels['tmdb_id'] or item.contentSerieName):
                param = "tvshow_id =%s,tvshow=%s, season=%s" \
                        % (item.infoLabels['tmdb_id'], item.contentSerieName, item.contentSeason)
                context_commands.append(("ExtendedInfo", "XBMC.RunScript(script.extendedinfo,info=seasoninfo,%s)" % param))

            elif item.contentType == "tvshow" and (item.infoLabels['tmdb_id'] or item.infoLabels['tvdb_id'] or item.infoLabels['imdb_id'] or item.contentSerieName):
                param = "id =%s,tvdb_id=%s,imdb_id=%s,name=%s" % (item.infoLabels['tmdb_id'], item.infoLabels['tvdb_id'], item.infoLabels['imdb_id'], item.contentSerieName)
                context_commands.append(("ExtendedInfo", "XBMC.RunScript(script.extendedinfo,info=extendedtvinfo,%s)" % param))

            elif item.contentType == "movie" and (item.infoLabels['tmdb_id'] or item.infoLabels['imdb_id'] or item.contentTitle):
                param = "id =%s,imdb_id=%s,name=%s" % (item.infoLabels['tmdb_id'], item.infoLabels['imdb_id'], item.contentTitle)

                context_commands.append(("ExtendedInfo", "XBMC.RunScript(script.extendedinfo,info=extendedinfo,%s)" % param))
                # InfoPlus
        if config.get_setting("infoplus"):
            #if item.infoLabels['tmdb_id'] or item.infoLabels['imdb_id'] or item.infoLabels['tvdb_id'] or \
            #        (item.contentTitle and item.infoLabels["year"]) or item.contentSerieName:
            if item.infoLabels['tmdb_id'] or item.infoLabels['imdb_id'] or item.infoLabels['tvdb_id']:
                context_commands.append(("InfoPlus", "XBMC.RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url,
                            'channel=infoplus&action=start&from_channel=' + item.channel)))

        # Go to the Main Menu (channel.mainlist)
        if parent_item.channel not in ["news", "channelselector", "downloads"] and item.action != "mainlist" and parent_item.action != "mainlist":
            context_commands.insert(0, (config.get_localized_string(60349), "XBMC.Container.Refresh (%s?%s)" % (sys.argv[0], Item(channel=item.channel, action="mainlist").tourl())))
            context_commands.insert(1, (config.get_localized_string(70739), "XBMC.Container.Update (%s?%s)" % (sys.argv[0], Item(action="open_browser", url=item.url).tourl())))

        # Add to Favorites
        # if num_version_xbmc < 17.0 and \
        #         ((item.channel not in ["favorites", "videolibrary", "help", ""]
        #           or item.action in ["update_videolibrary"]) and parent_item.channel != "favorites"):
        #     context_commands.append((config.get_localized_string(30155), "XBMC.RunPlugin(%s?%s&%s)" %
        #                              (sys.argv[0], item_url, 'channel=favorites&action=addFavourite&from_channel=' + item.channel + '&from_action=' + item.action)))

        # Add to kodfavoritos (My links)
        if item.channel not in ["favorites", "videolibrary", "help", ""] and parent_item.channel != "favorites":
            context_commands.append( (config.get_localized_string(70557), "XBMC.RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, urllib.urlencode({'channel': "kodfavorites", 'action': "addFavourite", 'from_channel': item.channel, 'from_action': item.action}))))
        # Search in other channels
        if item.contentType in ['movie', 'tvshow'] and item.channel != 'search' and item.action not in ['play'] and parent_item.action != 'mainlist':

            # Search in other channels
            if item.contentSerieName != '':
                item.wanted = item.contentSerieName
            else:
                item.wanted = item.contentTitle

            if item.contentType == 'tvshow':
                mediatype = 'tv'
            else:
                mediatype = item.contentType

            context_commands.append((config.get_localized_string(60350), "XBMC.Container.Update (%s?%s&%s)" % (sys.argv[0], item_url, urllib.urlencode({'channel': 'search', 'action': "from_context", 'from_channel': item.channel, 'contextual': True, 'text': item.wanted}))))

            context_commands.append( (config.get_localized_string(70561), "XBMC.Container.Update (%s?%s&%s)" % (sys.argv[0], item_url, 'channel=search&action=from_context&search_type=list&page=1&list_type=%s/%s/similar' % (mediatype, item.infoLabels['tmdb_id']))))
        # Set as Home Page
        if config.get_setting('start_page'):
            if item.action not in ['episodios', 'seasons', 'findvideos', 'play']:
                context_commands.insert(0, (config.get_localized_string(60351), "XBMC.RunPlugin(%s?%s)" % (sys.argv[0], Item(channel='side_menu', action="set_custom_start", parent=item.tourl()).tourl())))

        if item.channel != "videolibrary":
            # Add Series to the video library
            if item.action in ["episodios", "get_episodios", "get_seasons"] and item.contentSerieName:
                context_commands.append((config.get_localized_string(60352), "XBMC.RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, 'action=add_serie_to_library&from_action=' + item.action)))
            # Add Movie to Video Library
            elif item.action in ["detail", "findvideos"] and item.contentType == 'movie' and item.contentTitle:
                context_commands.append((config.get_localized_string(60353), "XBMC.RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, 'action=add_pelicula_to_library&from_action=' + item.action)))

        if not item.local and item.channel not in ["downloads", "filmontv"] and item.server != 'torrent' and parent_item.action != 'mainlist' and config.get_setting('downloadenabled'):
            # Download movie
            if item.contentType == "movie":
                context_commands.append((config.get_localized_string(60354), "XBMC.RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, 'channel=downloads&action=save_download&from_channel=' + item.channel + '&from_action=' + item.action)))

            elif item.contentSerieName:
                # Descargar series
                if item.contentType == "tvshow" and item.action not in ['findvideos']:
                    if item.channel == 'videolibrary':
                        context_commands.append((config.get_localized_string(60003), "XBMC.RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, 'channel=downloads&action=save_download&unseen=true&from_channel=' + item.channel + '&from_action=' + item.action)))
                    context_commands.append((config.get_localized_string(60355), "XBMC.RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, 'channel=downloads&action=save_download&from_channel=' + item.channel + '&from_action=' + item.action)))
                    context_commands.append((config.get_localized_string(60357), "XBMC.RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, 'channel=downloads&action=save_download&download=season&from_channel=' + item.channel + '&from_action=' + item.action)))
                # Download episode
                elif item.contentType == "episode" or item.action in ['findvideos']:
                    context_commands.append((config.get_localized_string(60356), "XBMC.RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, 'channel=downloads&action=save_download&from_channel=' + item.channel + '&from_action=' + item.action)))
                # Download season
                elif item.contentType == "season":
                    context_commands.append((config.get_localized_string(60357), "XBMC.RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, 'channel=downloads&action=save_download&download=season&from_channel=' + item.channel + '&from_action=' + item.action)))

        # # Open settings
        # if parent_item.channel not in ["setting", "news", "search"] and item.action == "play":
        #     context_commands.append((config.get_localized_string(60358), "XBMC.Container.Update(%s?%s)" %
        #                              (sys.argv[0], Item(channel="setting", action="mainlist").tourl())))

        # Open settings...
        if item.action in ["findvideos", 'episodios', 'check', 'new_search'] or "buscar_trailer" in context:
            context_commands.append((config.get_localized_string(60359), "XBMC.RunPlugin(%s?%s)" % (sys.argv[0], urllib.urlencode({ 'channel': "trailertools", 'action': "buscartrailer", 'search_title': item.contentTitle if item.contentTitle else item.fulltitle, 'contextual': True}))))

        if kwargs.get('superfavourites'):
            context_commands.append((config.get_localized_string(60361), "XBMC.RunScript(special://home/addons/plugin.program.super.favourites/LaunchSFMenu.py)"))

    # context_commands = sorted(context_commands, key=lambda comand: comand[0])

    # Quick Menu
    # context_commands.insert(0, (config.get_localized_string(60360),
    #                             "XBMC.Container.Update (%s?%s)" % (sys.argv[0], Item(channel='side_menu',
    #                                                                                  action="open_menu",
    #                                                                                  parent=parent_item.tourl()).tourl(
    #                             ))))
    if config.dev_mode():
        context_commands.insert(0, ("item info", "XBMC.Container.Update (%s?%s)" % (sys.argv[0], Item(action="itemInfo", parent=item.tojson()).tourl())))
    return context_commands


def is_playing():
    return xbmc_player.isPlaying()


def play_video(item, strm=False, force_direct=False, autoplay=False):
    logger.info()
    # logger.debug(item.tostring('\n'))
    logger.debug('item play: %s' % item)
    xbmc_player = XBMCPlayer()
    if item.channel == 'downloads':
        logger.info("Reproducir video local: %s [%s]" % (item.title, item.url))
        xlistitem = xbmcgui.ListItem(path=item.url)
        if config.get_platform(True)['num_version'] >= 16.0:
            xlistitem.setArt({"thumb": item.thumbnail})
        else:
            xlistitem.setThumbnailImage(item.thumbnail)

        set_infolabels(xlistitem, item, True)
        set_player(item, xlistitem, item.url, True, None) # Fix Play From Download Section
        # xbmc_player.play(item.url, xlistitem)
        return

    default_action = config.get_setting("default_action")
    logger.info("default_action=%s" % default_action)

    # Open the selection dialog to see the available options
    opciones, video_urls, seleccion, salir = get_dialogo_opciones(item, default_action, strm, autoplay)
    if salir:
        return

    # get default option of addon configuration
    seleccion = get_seleccion(default_action, opciones, seleccion, video_urls)
    if seleccion < 0:  # Canceled box
        return

    logger.info("selection=%d" % seleccion)
    logger.info("selection=%s" % opciones[seleccion])

    # run the available option, jdwonloader, download, favorites, add to the video library ... IF IT IS NOT PLAY
    salir = set_opcion(item, seleccion, opciones, video_urls)
    if salir:
        return

    # we get the selected video
    mediaurl, view, mpd = get_video_seleccionado(item, seleccion, video_urls)
    if mediaurl == "":
        return
    # # no certificate verification
    # mediaurl = mediaurl.replace('https://', 'http://')

    # video information is obtained.
    if not item.contentThumbnail:
        thumb = item.thumbnail
    else:
        thumb = item.contentThumbnail

    xlistitem = xbmcgui.ListItem(path=item.url)
    if config.get_platform(True)['num_version'] >= 16.0:
        xlistitem.setArt({"thumb": thumb})
    else:
        xlistitem.setThumbnailImage(thumb)

    set_infolabels(xlistitem, item, True)

    # if it is a video in mpd format, the listitem is configured to play it
    # with the inpustreamaddon addon implemented in Kodi 17
    if mpd:
        xlistitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
        xlistitem.setProperty('inputstream.adaptive.manifest_type', 'mpd')

    # player launches
    if force_direct:  # when it comes from a window and not directly from the addon base
        # We add the listitem to a playlist
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()
        playlist.add(mediaurl, xlistitem)

        # Reproduce
        xbmc_player.play(playlist, xlistitem)
    else:
        set_player(item, xlistitem, mediaurl, view, strm)


def stop_video():
    xbmc_player.stop()


def get_seleccion(default_action, opciones, seleccion, video_urls):
    fixpri = False
    # to know what priority you work on
    priority = int(config.get_setting("resolve_priority"))
    # will be used to check for premium or debrider links
    check = []
    # Check if resolve stop is disabled
    if config.get_setting("resolve_stop") == False:
        fixpri = True
    # ask
    if default_action == 0:
        # "Choose an option"
        seleccion = dialog_select(config.get_localized_string(30163), opciones)
    # View in low quality
    elif default_action == 1:
        resolutions = []
        for url in video_urls:
            if "debrid]" in url[0] or "Premium)" in url[0]:
                check.append(True)
            res = calcResolution(url[0])
            if res:
                resolutions.append(res)
        if resolutions:
            if (fixpri == True and
                    check and
                    priority == 2):
                seleccion = 0
            else:
                seleccion = resolutions.index(min(resolutions))
        else:
            seleccion = 0
    # See in high quality
    elif default_action == 2:
        resolutions = []
        for url in video_urls:
            if "debrid]" in url[0] or "Premium)" in url[0]:
                check.append(True)
            res = calcResolution(url[0])
            if res:
                resolutions.append(res)

        if resolutions:
            if (fixpri == True and
                    check and
                    priority == 2):
                seleccion = 0
            else:
                seleccion = resolutions.index(max(resolutions))
        else:
            if fixpri == True and check:
                seleccion = 0
            else:
                seleccion = len(video_urls) - 1
    else:
        seleccion = 0
    return seleccion


def calcResolution(option):
    match = scrapertools.find_single_match(option, '([0-9]{2,4})x([0-9]{2,4})')
    resolution = False
    if match:
        resolution = int(match[0]) * int(match[1])
    else:
        if '240p' in option:
            resolution = 320 * 240
        elif '360p' in option:
            resolution = 480 * 360
        elif ('480p' in option) or ('480i' in option):
            resolution = 720 * 480
        elif ('576p' in option) or ('576p' in option):
            resolution = 720 * 576
        elif ('720p' in option) or ('HD' in option):
            resolution = 1280 * 720
        elif ('1080p' in option) or ('1080i' in option) or ('Full HD' in option):
            resolution = 1920 * 1080

    return resolution


def show_channel_settings(**kwargs):
    """
    It shows a customized configuration box for each channel and saves the data when closing it.
    The parameters passed to it can be seen in the method that is called

    @return: returns the window with the elements
    @rtype: SettingsWindow
    """
    from platformcode.xbmc_config_menu import SettingsWindow
    return SettingsWindow("ChannelSettings.xml", config.get_runtime_path()).start(**kwargs)


def show_video_info(*args, **kwargs):
    """
    It shows a window with the info of the video.
    The parameters passed to it can be seen in the method that is called

    @return: returns the window with the elements
    @rtype: InfoWindow
    """

    from platformcode.xbmc_info_window import InfoWindow
    return InfoWindow("InfoWindow.xml", config.get_runtime_path()).start(*args, **kwargs)


def show_recaptcha(key, referer):
    from platformcode.recaptcha import Recaptcha
    return Recaptcha("Recaptcha.xml", config.get_runtime_path()).Start(key, referer)


def alert_no_disponible_server(server):
    # 'The video is no longer in %s', 'Try another server or another channel'
    dialog_ok(config.get_localized_string(30055), (config.get_localized_string(30057) % server), config.get_localized_string(30058))


def alert_unsopported_server():
    # 'Unsupported or unknown server ',' Test on another server or on another channel'
    dialog_ok(config.get_localized_string(30065), config.get_localized_string(30058))


def handle_wait(time_to_wait, title, text):
    logger.info("handle_wait(time_to_wait=%d)" % time_to_wait)
    espera = dialog_progress(' ' + title, "")

    secs = 0
    increment = int(old_div(100, time_to_wait))

    cancelled = False
    while secs < time_to_wait:
        secs += 1
        percent = increment * secs
        secs_left = str((time_to_wait - secs))
        remaining_display = config.get_localized_string(70176) + secs_left + config.get_localized_string(70177)
        espera.update(percent, ' ' + text, remaining_display)
        xbmc.sleep(1000)
        if espera.iscanceled():
            cancelled = True
            break

    if cancelled:
        logger.info('Wait canceled')
        return False
    else:
        logger.info('Wait finished')
        return True


def get_dialogo_opciones(item, default_action, strm, autoplay):
    logger.info()
    # logger.debug(item.tostring('\n'))
    from core import servertools

    opciones = []
    error = False

    try:
        item.server = item.server.lower()
    except AttributeError:
        item.server = ""

    if item.server == "":
        item.server = "directo"

    # If it is not the normal mode, it does not show the dialog because XBMC hangs
    muestra_dialogo = (config.get_setting("player_mode") == 0 and not strm)

    # Extract the URLs of the videos, and if you can't see it, it tells you the reason
    # Allow multiple qualities for "direct" server

    if item.video_urls:
        video_urls, puedes, motivo = item.video_urls, True, ""
    else:
        video_urls, puedes, motivo = servertools.resolve_video_urls_for_playing(
            item.server, item.url, item.password, muestra_dialogo)

    seleccion = 0
    # If you can see the video, present the options
    if puedes:
        for video_url in video_urls:
            opciones.append(config.get_localized_string(60221) + " " + video_url[0])

        if item.server == "local":
            opciones.append(config.get_localized_string(30164))
        else:
            # "Download"
            downloadenabled = config.get_setting('downloadenabled')
            if downloadenabled != False and item.channel != 'videolibrary':
                opcion = config.get_localized_string(30153)
                opciones.append(opcion)

            if item.isFavourite:
                # "Remove from favorites"
                opciones.append(config.get_localized_string(30154))
            else:
                # "Add to Favorites"
                opciones.append(config.get_localized_string(30155))

            if not strm and item.contentType == 'movie' and item.channel != 'videolibrary':
                # "Add to video library"
                opciones.append(config.get_localized_string(30161))

        if default_action == 3:
            seleccion = len(opciones) - 1

        # Search for trailers on youtube
        if item.channel not in ["Trailer", "ecarteleratrailers"]:
            # "Search Trailer"
            opciones.append(config.get_localized_string(30162))

    # If you can't see the video it informs you
    else:
        if not autoplay:
            if item.server != "":
                if "<br/>" in motivo:
                    ret = dialog_yesno(config.get_localized_string(60362), motivo.split("<br/>")[0], motivo.split("<br/>")[1], item.url, nolabel='ok', yeslabel=config.get_localized_string(70739))
                else:
                    ret = dialog_yesno(config.get_localized_string(60362), motivo, item.url, nolabel='ok', yeslabel=config.get_localized_string(70739))
            else:
                ret = dialog_yesno(config.get_localized_string(60362), config.get_localized_string(60363), config.get_localized_string(60364), item.url, nolabel='ok', yeslabel=config.get_localized_string(70739))
            if ret:
                xbmc.executebuiltin("XBMC.Container.Update (%s?%s)" % (sys.argv[0], Item(action="open_browser", url=item.url).tourl()))
            if item.channel == "favorites":
                # "Remove from favorites"
                opciones.append(config.get_localized_string(30154))

            if len(opciones) == 0:
                error = True

    return opciones, video_urls, seleccion, error


def set_opcion(item, seleccion, opciones, video_urls):
    logger.info()
    # logger.debug(item.tostring('\n'))
    salir = False
    # You have not chosen anything, most likely because you have given the ESC

    if seleccion == -1:
        # To avoid the error "One or more elements failed" when deselecting from strm file
        listitem = xbmcgui.ListItem(item.title)

        if config.get_platform(True)['num_version'] >= 16.0:
            listitem.setArt({'icon': "DefaultVideo.png", 'thumb': item.thumbnail})
        else:
            listitem.setIconImage("DefaultVideo.png")
            listitem.setThumbnailImage(item.thumbnail)

        xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, listitem)

    # "Download"
    elif opciones[seleccion] == config.get_localized_string(30153):
        from specials import downloads

        if item.contentType == "list" or item.contentType == "tvshow":
            item.contentType = "video"
        item.play_menu = True
        downloads.save_download(item)
        salir = True

    # "Remove from favorites"
    elif opciones[seleccion] == config.get_localized_string(30154):
        from specials import favorites
        favorites.delFavourite(item)
        salir = True

    # "Add to Favorites":
    elif opciones[seleccion] == config.get_localized_string(30155):
        from specials import favorites
        item.from_channel = "favorites"
        favorites.addFavourite(item)
        salir = True

    # "Search Trailer":
    elif opciones[seleccion] == config.get_localized_string(30162):
        config.set_setting("subtitulo", False)
        xbmc.executebuiltin("XBMC.RunPlugin(%s?%s)" % (sys.argv[0], item.clone(channel="trailertools", action="buscartrailer", contextual=True).tourl()))
        salir = True

    return salir


def get_video_seleccionado(item, seleccion, video_urls):
    logger.info()
    mediaurl = ""
    view = False
    wait_time = 0
    mpd = False

    # You have chosen one of the videos
    if seleccion < len(video_urls):
        mediaurl = video_urls[seleccion][1]
        if len(video_urls[seleccion]) > 4:
            wait_time = video_urls[seleccion][2]
            if not item.subtitle:
                item.subtitle = video_urls[seleccion][3]
            mpd = True
        elif len(video_urls[seleccion]) > 3:
            wait_time = video_urls[seleccion][2]
            if not item.subtitle:
                item.subtitle = video_urls[seleccion][3]
        elif len(video_urls[seleccion]) > 2:
            wait_time = video_urls[seleccion][2]
        view = True

    # If there is no mediaurl it is because the video is not there :)
    logger.info("mediaurl=" + mediaurl)
    if mediaurl == "":
        if item.server == "unknown":
            alert_unsopported_server()
        else:
            alert_no_disponible_server(item.server)

    # If there is a timeout (like in megaupload), impose it now
    if wait_time > 0:
        continuar = handle_wait(wait_time, item.server, config.get_localized_string(60365))
        if not continuar:
            mediaurl = ""

    return mediaurl, view, mpd


def set_player(item, xlistitem, mediaurl, view, strm):
    logger.info()
    logger.debug("item:\n" + item.tostring('\n'))
    # Moved del conector "torrent" here
    if item.server == "torrent":
        play_torrent(item, xlistitem, mediaurl)
        return

    # If it is a strm file, play is not necessary
    elif strm:
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xlistitem)
        if item.subtitle != "":
            xbmc.sleep(2000)
            xbmc_player.setSubtitles(item.subtitle)

    else:
        logger.info("player_mode=%s" % config.get_setting("player_mode"))
        logger.info("mediaurl=" + mediaurl)
        if config.get_setting("player_mode") == 3 or "megacrypter.com" in mediaurl:
            from platformcode import download_and_play
            download_and_play.download_and_play(mediaurl, "download_and_play.tmp", config.get_setting("downloadpath"))
            return

        elif config.get_setting("player_mode") == 0 or item.play_from == 'window' or \
                (config.get_setting("player_mode") == 3 and mediaurl.startswith("rtmp")):
            # We add the listitem to a playlist
            playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            playlist.clear()
            playlist.add(mediaurl, xlistitem)

            # Reproduce
            # xbmc_player = xbmc_player
            xbmc_player.play(playlist, xlistitem)
            if config.get_setting('trakt_sync'):
                trakt_tools.wait_for_update_trakt()

        # elif config.get_setting("player_mode") == 1 or item.isPlayable:
        elif config.get_setting("player_mode") == 1:
            logger.info("Tras setResolvedUrl")
            # if it is a video library file send to mark as seen

            if strm or item.strm_path:
                from platformcode import xbmc_videolibrary
                xbmc_videolibrary.mark_auto_as_watched(item)
            logger.debug(item)
            xlistitem.setPath(mediaurl)
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xlistitem)
            xbmc.sleep(2500)

        elif config.get_setting("player_mode") == 2:
            xbmc.executebuiltin("PlayMedia(" + mediaurl + ")")

    # ALL LOOKING TO REMOVE VIEW
    if item.subtitle != "" and view:
        logger.info("Subtítulos externos: " + item.subtitle)
        xbmc.sleep(2000)
        xbmc_player.setSubtitles(item.subtitle)

    # if it is a video library file send to mark as seen
    if strm or item.strm_path:
        from platformcode import xbmc_videolibrary
        xbmc_videolibrary.mark_auto_as_watched(item)


def torrent_client_installed(show_tuple=False):
    # External plugins found in servers / torrent.json node clients
    from core import filetools
    from core import jsontools
    torrent_clients = jsontools.get_node_from_file("torrent.json", "clients", filetools.join(config.get_runtime_path(), "servers"))
    torrent_options = []
    for client in torrent_clients:
        if xbmc.getCondVisibility('System.HasAddon("%s")' % client["id"]):
            if show_tuple:
                torrent_options.append([client["name"], client["url"]])
            else:
                torrent_options.append(client["name"])
    return torrent_options


def play_torrent(item, xlistitem, mediaurl):
    logger.info()
    import time
    from servers import torrent

    torrent_options = torrent_client_installed(show_tuple=True)
    if len(torrent_options) == 0:
        from specials import elementum_download
        elementum_download.download()
        return play_torrent(item, xlistitem, mediaurl)
    elif len(torrent_options) > 1:
        selection = dialog_select(config.get_localized_string(70193), [opcion[0] for opcion in torrent_options])
    else:
        selection = 0

    if selection >= 0:

        xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, xlistitem)
        time.sleep(1)

        mediaurl = urllib.quote_plus(item.url)
        torr_client = torrent_options[selection][0]

        if torr_client in ['elementum'] and item.infoLabels['tmdb_id']:
            if item.contentType == 'episode' and "elementum" not in torr_client:
                mediaurl += "&episode=%s&library=&season=%s&show=%s&tmdb=%s&type=episode" % (item.infoLabels['episode'], item.infoLabels['season'], item.infoLabels['tmdb_id'], item.infoLabels['tmdb_id'])
            elif item.contentType == 'movie':
                mediaurl += "&library=&tmdb=%s&type=movie" % (item.infoLabels['tmdb_id'])

        if torr_client in ['elementum'] and item.downloadFilename:
            torrent.elementum_download(item)
        else:
            time.sleep(3)
            xbmc.executebuiltin("PlayMedia(" + torrent_options[selection][1] % mediaurl + ")")

            torrent.mark_auto_as_watched(item)

            while is_playing() and not xbmc.abortRequested:
                time.sleep(3)


def log(texto):
    xbmc.log(texto, xbmc.LOGNOTICE)
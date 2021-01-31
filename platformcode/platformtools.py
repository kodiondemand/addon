# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# platformtools
# ------------------------------------------------------------
# Tools responsible for adapting the different dialog boxes to a specific platform.
# version 2.0
# ------------------------------------------------------------

import sys
if sys.version_info[0] >= 3:
    PY3 = True
    import urllib.parse as urllib
else:
    PY3 = False
    import urllib

import os, xbmc, xbmcgui, xbmcplugin
from past.utils import old_div
from channelselector import get_thumb
from core import scrapertools
from core.item import Item
from platformcode import logger, config

addon = config.__settings__
addon_icon = os.path.join( addon.getAddonInfo( "path" ),'resources', 'media', "logo.png" )

# class XBMCPlayer(xbmc.Player):

#     def __init__(self, *args):
#         pass


xbmc_player = xbmc.Player()


def dialog_ok(heading, message):
    dialog = xbmcgui.Dialog()
    return dialog.ok(heading, message)


def dialog_notification(heading, message, icon=3, time=5000, sound=True):
    dialog = xbmcgui.Dialog()
    try:
        l_icono = [xbmcgui.NOTIFICATION_INFO, xbmcgui.NOTIFICATION_WARNING, xbmcgui.NOTIFICATION_ERROR, addon_icon]
        dialog.notification(heading, message, l_icono[icon], time, sound)
    except:
        dialog_ok(heading, message)


def dialog_yesno(heading, message, nolabel=config.get_localized_string(70170), yeslabel=config.get_localized_string(30022), autoclose=0, customlabel=None):
    dialog = xbmcgui.Dialog()
    # customlabel only work on kodi 19
    if PY3 and customlabel:
        return dialog.yesnocustom(heading, message, customlabel=customlabel, nolabel=nolabel, yeslabel=yeslabel, autoclose=autoclose)
    else:
        return dialog.yesno(heading, message, nolabel=nolabel, yeslabel=yeslabel, autoclose=autoclose)


def dialog_select(heading, _list, preselect=0, useDetails=False):
    return xbmcgui.Dialog().select(heading, _list, preselect=preselect, useDetails=useDetails)


def dialog_multiselect(heading, _list, autoclose=0, preselect=[], useDetails=False):
    return xbmcgui.Dialog().multiselect(heading, _list, autoclose=autoclose, preselect=preselect, useDetails=useDetails)


def dialog_progress(heading, message):
    dialog = xbmcgui.DialogProgress()
    dialog.create(heading, message)
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


def dialog_browse(_type, heading, shares="files", mask="", useThumbs=False, treatAsFolder=False, defaultt="", enableMultiple=False):
    dialog = xbmcgui.Dialog()
    d = dialog.browse(_type, heading, shares, mask, useThumbs, treatAsFolder, defaultt, enableMultiple)
    return d


def dialog_register(heading, user=False, email=False, password=False, user_default='', email_default='', password_default='', captcha_img=''):
    class Register(xbmcgui.WindowXMLDialog):
        def Start(self, heading, user, email, password, user_default, email_default, password_default, captcha_img):
            self.result = {}
            self.heading = heading
            self.user = user
            self.email = email
            self.password = password
            self.user_default = user_default
            self.email_default = email_default
            self.password_default = password_default
            self.captcha_img = captcha_img
            self.doModal()

            return self.result

        def __init__(self, *args, **kwargs):
            self.mensaje = kwargs.get("mensaje")
            self.imagen = kwargs.get("imagen")

        def onInit(self):
            #### Kodi 18 compatibility ####
            if config.get_platform(True)['num_version'] < 18:
                self.setCoordinateResolution(2)
            height = 90
            self.getControl(10002).setText(self.heading)
            if self.user:
                self.getControl(10003).setText(self.user_default)
                height += 70
            else:
                self.getControl(10003).setVisible(False)
            if self.email:
                self.getControl(10004).setText(self.email_default)
                height += 70
            else:
                self.getControl(10004).setVisible(False)
            if self.password:
                self.getControl(10005).setText(self.password_default)
                height += 70
            else:
                self.getControl(10005).setVisible(False)
            if self.captcha_img:

                self.getControl(10007).setImage(self.captcha_img)
                height += 240
            else:
                self.getControl(10005).setVisible(False)
            height += 40
            if height < 250: height = 250
            self.getControl(10000).setHeight(height)
            self.getControl(10001).setHeight(height)
            self.getControl(10000).setPosition(255, old_div(720 - height, 2))
            self.setFocusId(30000)

        def onClick(self, control):
            if control in [10010]:
                self.close()

            elif control in [10009]:
                if self.user: self.result['user'] = self.getControl(10003).getText()
                if self.email: self.result['email'] = self.getControl(10004).getText()
                if self.password: self.result['password'] = self.getControl(10005).getText()
                if self.captcha_img: self.result['captcha'] = self.getControl(10006).getText()
                self.close()

    dialog = Register('Register.xml', config.get_runtime_path()).Start(heading, user, email, password, user_default, email_default, password_default, captcha_img)
    return dialog

def dialog_info(item, scraper):
    class TitleOrIDWindow(xbmcgui.WindowXMLDialog):
        def Start(self, item, scraper):
            self.item = item
            self.item.exit = False
            self.title = item.show if item.show else item.fulltitle
            self.id = item.infoLabels.get('tmdb_id', '') if scraper == 'tmdb' else item.infoLabels.get('tvdb_id', '')
            self.scraper = scraper
            self.idtitle = 'TMDB ID' if scraper == 'tmdb' else 'TVDB ID'
            self.doModal()
            return self.item

        def onInit(self):
            #### Kodi 18 compatibility ####
            if config.get_platform(True)['num_version'] < 18:
                self.setCoordinateResolution(2)
            self.HEADER = self.getControl(100)
            self.TITLE = self.getControl(101)
            self.ID = self.getControl(102)
            self.EXIT = self.getControl(103)
            self.EXIT2 = self.getControl(104)

            self.HEADER.setText(config.get_localized_string(60228) % self.title)
            self.TITLE.setLabel('[UPPERCASE]' + config.get_localized_string(60230).replace(':','') + '[/UPPERCASE]')
            self.ID.setLabel(self.idtitle)
            self.setFocusId(101)

        def onClick(self, control):
            if control in [101]:
                result = dialog_input(self.title)
                if result:
                    if self.item.contentType == 'movie': self.item.contentTitle = result
                    else: self.item.contentSerieName = result
                    self.close()
            elif control in [102]:
                result = dialog_numeric(0, self.idtitle, self.id)
                if result:
                    if self.scraper == 'tmdb': self.item.infoLabels['tmdb_id'] = result
                    elif self.scraper == 'tvdb': self.item.infoLabels['tvdb_id'] = result
                    self.close()

            elif control in [103, 104]:
                self.item.exit = True
                self.close()

        def onAction(self, action):
            action = action.getId()
            if action in [92, 10]:
                self.item.exit = True
                self.close()

    dialog = TitleOrIDWindow('TitleOrIDWindow.xml', config.get_runtime_path()).Start(item, scraper)
    return dialog


def itemlist_refresh():
    # pos = Item().fromurl(xbmc.getInfoLabel('ListItem.FileNameAndPath')).itemlistPosition
    # logger.info('Current position: ' + str(pos))
    xbmc.executebuiltin("Container.Refresh")

    # while Item().fromurl(xbmc.getInfoLabel('ListItem.FileNameAndPath')).itemlistPosition != pos:
    #     win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
    #     cid = win.getFocusId()
    #     ctl = win.getControl(cid)
    #     ctl.selectItem(pos)


def itemlist_update(item, replace=False):
    if replace:  # reset the path history
        xbmc.executebuiltin("Container.Update(" + sys.argv[0] + "?" + item.tourl() + ", replace)")
    else:
        xbmc.executebuiltin("Container.Update(" + sys.argv[0] + "?" + item.tourl() + ")")


def render_items(itemlist, parent_item):
    """
    Function used to render itemlist on kodi
    """
    logger.debug('START render_items')
    thumb_type = config.get_setting('video_thumbnail_type')
    from platformcode import shortcuts
    # from core import httptools
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
        # item.itemlistPosition = n + 1
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
            item.thumbnail = config.get_online_server_thumb(item.server)

        # if cloudflare and cloudscraper is used, cookies are needed to display images taken from site
        # before checking domain (time consuming), checking if tmdb failed (so, images scraped from website are used)
        # if item.action in ['findvideos'] and not item.infoLabels['tmdb_id']:
            # faster but ugly way of checking
            # for d in httptools.FORCE_CLOUDSCRAPER_LIST:
            #     if d + '/' in item.url:
            #         item.thumbnail = httptools.get_url_headers(item.thumbnail)
            #         item.fanart = httptools.get_url_headers(item.fanart)
            #         break

        icon_image = "DefaultFolder.png" if item.folder else "DefaultVideo.png"
        listitem = xbmcgui.ListItem(item.title)
        listitem.setArt({'icon': icon_image, 'thumb': item.thumbnail, 'poster': item.thumbnail,
                         'fanart': item.fanart if item.fanart else default_fanart})

        if config.get_setting("player_mode") == 1 and item.action == "play" and not item.nfo:
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
    logger.debug('END render_items')


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
            or parent_item.action in ['now_on_tv', 'now_on_misc', 'now_on_misc_film', 'mostrar_perfil', 'live', 'replay', 'news']:
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
            logger.debug('default mode')
            mode = 55
        xbmcplugin.setContent(handle=int(sys.argv[1]), content=Type)
        xbmc.executebuiltin('Container.SetViewMode(%s)' % mode)
        logger.debug('TYPE: ' + Type + ' - ' + 'CONTENT: ' + content)


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
                context_commands.append((command["title"], "Container.Refresh (%s?%s)" % (sys.argv[0], item.clone(**command).tourl())))
            else:
                context_commands.append((command["title"], "RunPlugin(%s?%s)" % (sys.argv[0], item.clone(**command).tourl())))
    # Do not add more predefined options if you are inside kodfavoritos
    if parent_item.channel == 'kodfavorites':
        return context_commands
        # Options according to criteria, only if the item is not a tag, nor is it "Add to the video library", etc...
    if item.action and item.action not in ["add_pelicula_to_library", "add_serie_to_library", "buscartrailer", "actualizar_titulos"]:
        # Show information: if the item has a plot, we assume that it is a series, season, chapter or movie
        # if item.infoLabels['plot'] and (num_version_xbmc < 17.0 or item.contentType == 'season'):
        #     context_commands.append((config.get_localized_string(60348), "Action(Info)"))

        # ExtendedInfo: If the addon is installed and a series of conditions are met
        if kwargs.get('has_extendedinfo') \
                and config.get_setting("extended_info") == True:
            if item.contentType == "episode" and item.contentEpisodeNumber and item.contentSeason and (item.infoLabels['tmdb_id'] or item.contentSerieName):
                param = "tvshow_id =%s, tvshow=%s, season=%s, episode=%s" % (item.infoLabels['tmdb_id'], item.contentSerieName, item.contentSeason, item.contentEpisodeNumber)
                context_commands.append(("ExtendedInfo", "RunScript(script.extendedinfo,info=extendedepisodeinfo,%s)" % param))

            elif item.contentType == "season" and item.contentSeason and (item.infoLabels['tmdb_id'] or item.contentSerieName):
                param = "tvshow_id =%s,tvshow=%s, season=%s" % (item.infoLabels['tmdb_id'], item.contentSerieName, item.contentSeason)
                context_commands.append(("ExtendedInfo", "RunScript(script.extendedinfo,info=seasoninfo,%s)" % param))

            elif item.contentType == "tvshow" and (item.infoLabels['tmdb_id'] or item.infoLabels['tvdb_id'] or item.infoLabels['imdb_id'] or item.contentSerieName):
                param = "id =%s,tvdb_id=%s,imdb_id=%s,name=%s" % (item.infoLabels['tmdb_id'], item.infoLabels['tvdb_id'], item.infoLabels['imdb_id'], item.contentSerieName)
                context_commands.append(("ExtendedInfo", "RunScript(script.extendedinfo,info=extendedtvinfo,%s)" % param))

            elif item.contentType == "movie" and (item.infoLabels['tmdb_id'] or item.infoLabels['imdb_id'] or item.contentTitle):
                param = "id =%s,imdb_id=%s,name=%s" % (item.infoLabels['tmdb_id'], item.infoLabels['imdb_id'], item.contentTitle)
                context_commands.append(("ExtendedInfo", "RunScript(script.extendedinfo,info=extendedinfo,%s)" % param))

        # InfoPlus
        if config.get_setting("infoplus"):
            #if item.infoLabels['tmdb_id'] or item.infoLabels['imdb_id'] or item.infoLabels['tvdb_id'] or \
            #        (item.contentTitle and item.infoLabels["year"]) or item.contentSerieName:
            if item.infoLabels['tmdb_id'] or item.infoLabels['imdb_id'] or item.infoLabels['tvdb_id']:
                context_commands.append(("InfoPlus", "RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, 'channel=infoplus&action=Main&from_channel=' + item.channel)))

        # Go to the Main Menu (channel.mainlist)
        if parent_item.channel not in ["news", "channelselector", "downloads", "search"] and item.action != "mainlist" and not parent_item.noMainMenu:
            if parent_item.action != "mainlist":
                context_commands.insert(0, (config.get_localized_string(60349), "Container.Refresh (%s?%s)" % (sys.argv[0], Item(channel=item.channel, action="mainlist").tourl())))
            context_commands.insert(1, (config.get_localized_string(70739), "Container.Update (%s?%s)" % (sys.argv[0], Item(action="open_browser", url=item.url).tourl())))

        # Add to kodfavoritos (My links)
        if item.channel not in ["favorites", "videolibrary", "help", ""] and parent_item.channel != "favorites":
            context_commands.append( (config.get_localized_string(70557), "RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, urllib.urlencode({'channel': "kodfavorites", 'action': "addFavourite", 'from_channel': item.channel, 'from_action': item.action}))))
        # Add to kodfavoritos 
        if parent_item.channel == 'globalsearch':
            context_commands.append( (config.get_localized_string(30155), "RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, urllib.urlencode({'channel': "favorites", 'action': "addFavourite", 'from_channel': item.channel, 'from_action': item.action}))))
        # Search in other channels
        if item.contentTitle and item.contentType in ['movie', 'tvshow'] and parent_item.channel != 'search' and item.action not in ['play'] and parent_item.action != 'mainlist':

            # Search in other channels
            if item.contentSerieName != '':
                item.wanted = item.contentSerieName
            else:
                item.wanted = item.contentTitle

            if item.contentType == 'tvshow':
                mediatype = 'tv'
            else:
                mediatype = item.contentType

            context_commands.append((config.get_localized_string(60350), "Container.Update (%s?%s&%s)" % (sys.argv[0], item_url, urllib.urlencode({'channel': 'search', 'action': "from_context", 'from_channel': item.channel, 'contextual': True, 'text': item.wanted}))))

            context_commands.append( (config.get_localized_string(70561), "Container.Update (%s?%s&%s)" % (sys.argv[0], item_url, 'channel=search&action=from_context&search_type=list&page=1&list_type=%s/%s/similar' % (mediatype, item.infoLabels['tmdb_id']))))

        if item.channel != "videolibrary":
            # Add Series to the video library
            if item.action in ["episodios", "get_episodios", "get_seasons"] and item.contentSerieName:
                context_commands.append((config.get_localized_string(60352), "RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, 'action=add_serie_to_library&from_action=' + item.action)))
            # Add Movie to Video Library
            elif item.action in ["detail", "findvideos"] and item.contentType == 'movie' and item.contentTitle:
                context_commands.append((config.get_localized_string(60353), "RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, 'action=add_pelicula_to_library&from_action=' + item.action)))

        if not item.local and item.channel not in ["downloads", "filmontv", "search"] and item.server != 'torrent' and parent_item.action != 'mainlist' and config.get_setting('downloadenabled'):
            # Download movie
            if item.contentType == "movie":
                context_commands.append((config.get_localized_string(60354), "RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, 'channel=downloads&action=save_download&from_channel=' + item.channel + '&from_action=' + item.action)))

            elif item.contentSerieName:
                # Descargar series
                if item.contentType == "tvshow" and item.action not in ['findvideos']:
                    if item.channel == 'videolibrary':
                        context_commands.append((config.get_localized_string(60003), "RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, 'channel=downloads&action=save_download&unseen=true&from_channel=' + item.channel + '&from_action=' + item.action)))
                    context_commands.append((config.get_localized_string(60355), "RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, 'channel=downloads&action=save_download&from_channel=' + item.channel + '&from_action=' + item.action)))
                    context_commands.append((config.get_localized_string(60357), "RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, 'channel=downloads&action=save_download&download=season&from_channel=' + item.channel + '&from_action=' + item.action)))
                # Download episode
                elif item.contentType == "episode" and item.action in ['findvideos']:
                    context_commands.append((config.get_localized_string(60356), "RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, 'channel=downloads&action=save_download&from_channel=' + item.channel + '&from_action=' + item.action)))
                # Download season
                elif item.contentType == "season":
                    context_commands.append((config.get_localized_string(60357), "RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, 'channel=downloads&action=save_download&download=season&from_channel=' + item.channel + '&from_action=' + item.action)))

        # Search trailer...
        if (item.contentTitle and item.contentType in ['movie', 'tvshow']) or "buscar_trailer" in context:
            context_commands.append((config.get_localized_string(60359), "RunPlugin(%s?%s)" % (sys.argv[0], urllib.urlencode({ 'channel': "trailertools", 'action': "buscartrailer", 'search_title': item.contentTitle if item.contentTitle else item.fulltitle, 'contextual': True}))))

        if kwargs.get('superfavourites'):
            context_commands.append((config.get_localized_string(60361), "RunScript(special://home/addons/plugin.program.super.favourites/LaunchSFMenu.py)"))

    if config.dev_mode():
        context_commands.insert(0, ("item info", "Container.Update (%s?%s)" % (sys.argv[0], Item(action="itemInfo", parent=item.tojson()).tourl())))
    return context_commands


def is_playing():
    return xbmc_player.isPlaying()


def play_video(item, strm=False, force_direct=False, autoplay=False):
    logger.debug()
    logger.debug(item.tostring('\n'))
    if item.channel == 'downloads':
        logger.debug("Play local video: %s [%s]" % (item.title, item.url))
        xlistitem = xbmcgui.ListItem(path=item.url)
        xlistitem.setArt({"thumb": item.thumbnail})
        set_infolabels(xlistitem, item, True)
        set_player(item, xlistitem, item.url, True, None) # Fix Play From Download Section
        return

    default_action = config.get_setting("default_action")
    logger.debug("default_action=%s" % default_action)

    # pass referer
    if item.referer:
        from core import httptools
        httptools.default_headers['Referer'] = item.referer

    # Open the selection dialog to see the available options
    opciones, video_urls, seleccion, salir = get_dialogo_opciones(item, default_action, strm, autoplay)
    if salir: exit()

    # get default option of addon configuration
    seleccion = get_seleccion(default_action, opciones, seleccion, video_urls)
    if seleccion < 0: exit() # Canceled box

    logger.debug("selection=%d" % seleccion)
    logger.debug("selection=%s" % opciones[seleccion])

    # run the available option, jdwonloader, download, favorites, add to the video library ... IF IT IS NOT PLAY
    salir = set_opcion(item, seleccion, opciones, video_urls)
    if salir:
        return

    # we get the selected video
    mediaurl, view, mpd = get_video_seleccionado(item, seleccion, video_urls, autoplay)
    if not mediaurl: return

    # video information is obtained.
    xlistitem = xbmcgui.ListItem(path=item.url)
    xlistitem.setArt({"thumb": item.contentThumbnail if item.contentThumbnail else item.thumbnail})
    set_infolabels(xlistitem, item, True)

    # if it is a video in mpd format, the listitem is configured to play it ith the inpustreamaddon addon implemented in Kodi 17
    # from core.support import dbg;dbg()
    if mpd:
        if not install_inputstream():
            return
        xlistitem.setProperty('inputstream' if PY3 else 'inputstreamaddon', 'inputstream.adaptive')
        xlistitem.setProperty('inputstream.adaptive.manifest_type', 'mpd')
        if item.drm and item.license:
            install_widevine()
            xlistitem.setProperty("inputstream.adaptive.license_type", item.drm)
            xlistitem.setProperty("inputstream.adaptive.license_key", item.license)
            xlistitem.setMimeType('application/dash+xml')

    if force_direct: item.play_from = 'window'

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
    dialog_ok(config.get_localized_string(30055), (config.get_localized_string(30057) % server) + '\n' + config.get_localized_string(30058))


def alert_unsopported_server():
    # 'Unsupported or unknown server ',' Test on another server or on another channel'
    dialog_ok(config.get_localized_string(30065), config.get_localized_string(30058))


def handle_wait(time_to_wait, title, text):
    logger.debug("handle_wait(time_to_wait=%d)" % time_to_wait)
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
        logger.debug('Wait canceled')
        return False
    else:
        logger.debug('Wait finished')
        return True


def get_dialogo_opciones(item, default_action, strm, autoplay):
    logger.debug()
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
                    ret = dialog_yesno(config.get_localized_string(60362) % item.server, motivo.split("<br/>")[0] + '\n' + motivo.split("<br/>")[1], nolabel='ok', yeslabel=config.get_localized_string(70739))
                else:
                    ret = dialog_yesno(config.get_localized_string(60362) % item.server, motivo, nolabel='ok', yeslabel=config.get_localized_string(70739))
            else:
                ret = dialog_yesno(config.get_localized_string(60362) % item.server, config.get_localized_string(60363) + '\n' + config.get_localized_string(60364), nolabel='ok', yeslabel=config.get_localized_string(70739))
            if ret:
                xbmc.executebuiltin("Container.Update (%s?%s)" %
                                    (sys.argv[0], Item(action="open_browser", url=item.url).tourl()))
            if item.channel == "favorites":
                # "Remove from favorites"
                opciones.append(config.get_localized_string(30154))

            if len(opciones) == 0:
                error = True

    return opciones, video_urls, seleccion, error


def set_opcion(item, seleccion, opciones, video_urls):
    logger.debug()
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
        xbmc.executebuiltin("RunPlugin(%s?%s)" % (sys.argv[0], item.clone(channel="trailertools", action="buscartrailer", contextual=True).tourl()))
        salir = True

    return salir


def get_video_seleccionado(item, seleccion, video_urls, autoplay=False):
    logger.debug()
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

    if 'mpd' in video_urls[seleccion][0]:
        mpd = True

    # If there is no mediaurl it is because the video is not there :)
    logger.debug("mediaurl=" + mediaurl)
    if mediaurl == "" and not autoplay:
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
    logger.debug()
    item.options = {'strm':False}
    # logger.debug("item:\n" + item.tostring('\n'))

    # Moved del conector "torrent" here
    if item.server == "torrent":
        play_torrent(item, xlistitem, mediaurl)
        return
    # If it is a strm file, play is not necessary
    elif strm:
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xlistitem)
        if item.subtitle:
            xbmc.sleep(2000)
            xbmc_player.setSubtitles(item.subtitle)

    else:
        if type(item.player_mode) == int:
            player_mode = item.player_mode
        else:
            player_mode = config.get_setting("player_mode")
        if (player_mode == 3 and mediaurl.startswith("rtmp")): player_mode = 0
        elif "megacrypter.com" in mediaurl: player_mode = 3
        logger.info("mediaurl=" + mediaurl)

        if player_mode in [0,1]:
            prevent_busy(item)
            if player_mode in [1]:
                item.played_time = resume_playback(get_played_time(item))

            logger.info('Player Mode:',['Direct', 'Bookmark'][player_mode])
            # Add the listitem to a playlist
            playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            playlist.clear()
            playlist.add(mediaurl, xlistitem)
            # Reproduce
            xbmc_player.play(playlist, xlistitem)

            if config.get_setting('trakt_sync'):
                from core import trakt_tools
                trakt_tools.wait_for_update_trakt()

        elif player_mode == 2:
            logger.info('Player Mode: Built-In')
            xbmc.executebuiltin("PlayMedia(" + mediaurl + ")")

        elif player_mode == 3:
            logger.info('Player Mode: Download and Play')
            from platformcode import download_and_play
            download_and_play.download_and_play(mediaurl, "download_and_play.tmp", config.get_setting("downloadpath"))
            return

    # ALL LOOKING TO REMOVE VIEW
    if item.subtitle and view:
        logger.info("External subtitles: " + item.subtitle)
        xbmc.sleep(2000)
        xbmc_player.setSubtitles(item.subtitle)

    # if it is a video library file send to mark as seen
    if strm or item.strm_path: item.options['strm'] = True
    # if player_mode == 1: item.options['continue'] = True
    from platformcode import xbmc_videolibrary
    xbmc_videolibrary.mark_auto_as_watched(item)

    # for cases where the audio playback window appears in place of the video one
    if item.focusOnVideoPlayer:
        while is_playing() and xbmcgui.getCurrentWindowId() != 12006:
            continue
        xbmc.sleep(500)
        xbmcgui.Window(12005).show()


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
    logger.debug()
    import time
    from servers import torrent

    torrent_options = torrent_client_installed(show_tuple=True)
    if len(torrent_options) == 0:
        from platformcode import elementum_download
        elementum_download.download()
        return play_torrent(item, xlistitem, mediaurl)
    elif len(torrent_options) > 1:
        selection = dialog_select(config.get_localized_string(70193), [opcion[0] for opcion in torrent_options])
    else:
        selection = 0

    if selection >= 0:
        prevent_busy(item)

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

            if not item.globalsearch:
                while is_playing() and not xbmc.Monitor().abortRequested():
                    time.sleep(3)


def resume_playback(played_time):
    class ResumePlayback(xbmcgui.WindowXMLDialog):
        Close = False
        Resume = False

        def __init__(self, *args, **kwargs):
            self.action_exitkeys_id = [92, 10]
            self.progress_control = None
            played_time = kwargs.get('played_time')
            m, s = divmod(played_time, 60)
            h, m = divmod(m, 60)
            self.setProperty("time", '%02d:%02d:%02d' % (h, m, s))

        def set_values(self, value):
            self.Resume = value
            self.Close = True

        def is_close(self):
            return self.Close

        def onClick(self, controlId):
            if controlId == 3012:  # Resume
                self.set_values(True)
                self.close()
            elif controlId == 3013:  # Cancel
                self.set_values(False)
                self.close()

        def onAction(self, action):
            if action in self.action_exitkeys_id:
                self.set_values(False)
                self.close()
    if played_time:
        Dialog = ResumePlayback('ResumePlayback.xml', config.get_runtime_path(), played_time=played_time)
        Dialog.show()
        t = 0
        while not Dialog.is_close() and t < 100:
            t += 1
            xbmc.sleep(100)
        if not Dialog.Resume: played_time = 0
    else: played_time = 0
    xbmc.sleep(300)
    return played_time

##### INPUTSTREM #####

def install_inputstream():
    from xbmcaddon import Addon
    if not os.path.exists(os.path.join(xbmc.translatePath('special://home/addons/'),'inputstream.adaptive')) and not os.path.exists(os.path.join(xbmc.translatePath('special://xbmcbinaddons/'),'inputstream.adaptive')):
        try:
            # See if there's an installed repo that has it
            xbmc.executebuiltin('InstallAddon(inputstream.adaptive)', wait=True)

            # Check if InputStream add-on exists!
            Addon('inputstream.adaptive')

            logger.info('InputStream add-on installed from repo.')
        except RuntimeError:
            logger.info('InputStream add-on not installed.')
            dialog_ok(config.get_localized_string(20000), config.get_localized_string(30126))
            return False
    else:
        try:
            Addon('inputstream.adaptive')
            logger.info('InputStream add-on is installed and enabled')
        except:
            logger.info('enabling InputStream add-on')
            xbmc.executebuiltin('UpdateLocalAddons')
            xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id":1, "method": "Addons.SetAddonEnabled", "params": { "addonid": "inputstream.adaptive", "enabled": true }}')
    return True


def install_widevine():
    platform = get_platform()
    if platform['os'] != 'android':
        from core.httptools import downloadpage
        from xbmcaddon import Addon
        from core import jsontools
        from distutils.version import LooseVersion
        path = xbmc.translatePath(Addon('inputstream.adaptive').getSetting('DECRYPTERPATH'))

        # if Widevine CDM is not installed
        if not os.path.exists(path) or not os.listdir(path):
            select = dialog_yesno('Widevine CDM', config.get_localized_string(70808))
            if select > 0:
                if not 'arm' in platform['arch']:
                    last_version = downloadpage('https://dl.google.com/widevine-cdm/versions.txt').data.split()[-1]
                    download_widevine(last_version, platform, path)
                else:
                    json = downloadpage('https://dl.google.com/dl/edgedl/chromeos/recovery/recovery.json').data
                    devices = jsontools.load(json)
                    download_chromeos_image(devices, platform, path)

        # if Widevine CDM is outdated
        elif platform['os'] != 'android':
            if not 'arm' in platform['arch']:
                last_version = downloadpage('https://dl.google.com/widevine-cdm/versions.txt').data.split()[-1]
                current_version = jsontools.load(open(os.path.join(path, 'manifest.json')).read())['version']
                if LooseVersion(last_version) > LooseVersion(current_version):
                    select = dialog_yesno(config.get_localized_string(70810),config.get_localized_string(70809))
                    if select > 0: download_widevine(last_version, platform, path)
            else:
                devices = jsontools.load(downloadpage('https://dl.google.com/dl/edgedl/chromeos/recovery/recovery.json').data)
                current_version = jsontools.load(open(os.path.join(path, 'config.json')).read())['version']
                last_version = best_chromeos_image(devices)['version']
                if LooseVersion(last_version) > LooseVersion(current_version):
                    select = dialog_yesno(config.get_localized_string(70810),config.get_localized_string(70809))
                    if select > 0:download_chromeos_image(devices, platform, path)


def download_widevine(version, platform, path):
    # for x86 architectures
    from zipfile import ZipFile
    from core import downloadtools
    archiveName = 'https://dl.google.com/widevine-cdm/' + version + '-' + platform['os'] + '-' + platform['arch'] + '.zip'
    fileName = config.get_temp_file('widevine.zip')
    if not os.path.exists(archiveName):
        if not os.path.exists(fileName):
            downloadtools.downloadfile(archiveName, fileName, header='Download Widevine CDM')
        zip_obj = ZipFile(fileName)
        for filename in zip_obj.namelist():
            zip_obj.extract(filename, path)
        zip_obj.close()
        os.remove(fileName)


def download_chromeos_image(devices, platform, path):
    # for arm architectures
    from core import downloadtools
    from core import jsontools
    best = best_chromeos_image(devices)
    archiveName = best['url']
    version = best['version']

    fileName = config.get_temp_file(archiveName.split('/')[-1])
    if not os.path.exists(fileName):
        downloadtools.downloadfile(archiveName, fileName, header='Download Widevine CDM')
    from lib.arm_chromeos import ChromeOSImage
    ChromeOSImage(fileName).extract_file(
                filename='libwidevinecdm.so',
                extract_path=os.path.join(path),
                progress=dialog_progress(config.get_localized_string(70811),config.get_localized_string(70812)))
    recovery_file = os.path.join(path, os.path.basename('https://dl.google.com/dl/edgedl/chromeos/recovery/recovery.json'))
    config_file = os.path.join(path, 'config.json')
    if not os.path.exists(path):
        os.mkdir(path)
    with open(recovery_file, 'w') as reco_file:
        reco_file.write(jsontools.dump(devices, indent=4))
        reco_file.close()
    with open(config_file, 'w') as conf_file:
        conf_file.write(jsontools.dump(best))
        conf_file.close()
    os.remove(fileName)

def best_chromeos_image(devices):
    best = None
    for device in devices:
        # Select ARM hardware only
        for arm_hwid in ['BIG','BLAZE','BOB','DRUWL','DUMO','ELM','EXPRESSO','FIEVEL','HANA','JAQ','JERRY','KEVIN','KITTY','MICKEY','MIGHTY','MINNIE','PHASER','PHASER360','PI','PIT','RELM','SCARLET','SKATE','SNOW','SPEEDY','SPRING','TIGER']:
            if arm_hwid in device['hwidmatch']:
                hwid = arm_hwid
                break  # We found an ARM device, rejoice !
        else:
            continue  # Not ARM, skip this device

        device['hwid'] = hwid

        # Select the first ARM device
        if best is None:
            best = device
            continue  # Go to the next device

        # Skip identical hwid
        if hwid == best['hwid']:
            continue

        # Select the newest version
        from distutils.version import LooseVersion  # pylint: disable=import-error,no-name-in-module,useless-suppression
        if LooseVersion(device['version']) > LooseVersion(best['version']):
            logger.info('%s (%s) is newer than %s (%s)' % (device['hwid'], device['version'], best['hwid'], best['version']))
            best = device

        # Select the smallest image (disk space requirement)
        elif LooseVersion(device['version']) == LooseVersion(best['version']):
            if int(device['filesize']) + int(device['zipfilesize']) < int(best['filesize']) + int(best['zipfilesize']):
                logger.info('%s (%d) is smaller than %s (%d)' % (device['hwid'], int(device['filesize']) + int(device['zipfilesize']), best['hwid'], int(best['filesize']) + int(best['zipfilesize'])))
                best = device
    return best

def get_platform():
    import platform
    build = xbmc.getInfoLabel("System.BuildVersion")
    kodi_version = int(build.split()[0][:2])
    ret = {
        "auto_arch": sys.maxsize > 2 ** 32 and "64-bit" or "32-bit",
        "arch": sys.maxsize > 2 ** 32 and "x64" or "ia32",
        "os": "",
        "version": platform.release(),
        "kodi": kodi_version,
        "build": build
    }
    if xbmc.getCondVisibility("system.platform.android"):
        ret["os"] = "android"
        if "arm" in platform.machine() or "aarch" in platform.machine():
            ret["arch"] = "arm"
            if "64" in platform.machine() and ret["auto_arch"] == "64-bit":
                ret["arch"] = "arm64"
    elif xbmc.getCondVisibility("system.platform.linux"):
        ret["os"] = "linux"
        if "aarch" in platform.machine() or "arm64" in platform.machine():
            if xbmc.getCondVisibility("system.platform.linux.raspberrypi"):
                ret["arch"] = "armv7"
            elif ret["auto_arch"] == "32-bit":
                ret["arch"] = "armv7"
            elif ret["auto_arch"] == "64-bit":
                ret["arch"] = "arm64"
            elif platform.architecture()[0].startswith("32"):
                ret["arch"] = "arm"
            else:
                ret["arch"] = "arm64"
        elif "armv7" in platform.machine():
            ret["arch"] = "armv7"
        elif "arm" in platform.machine():
            ret["arch"] = "arm"
    elif xbmc.getCondVisibility("system.platform.xbox"):
        ret["os"] = "win"
        ret["arch"] = "x64"
    elif xbmc.getCondVisibility("system.platform.windows"):
        ret["os"] = "win"
        if platform.machine().endswith('64'):
            ret["arch"] = "x64"
    elif xbmc.getCondVisibility("system.platform.osx"):
        ret["os"] = "mac"
        ret["arch"] = "x64"
    elif xbmc.getCondVisibility("system.platform.ios"):
        ret["os"] = "ios"
        ret["arch"] = "arm"

    return ret



def get_played_time(item):
    logger.debug()
    from core import db

    if not item.infoLabels:
        return 0
    ID = item.infoLabels.get('tmdb_id','')
    if not ID:
        return 0

    S = item.infoLabels.get('season')
    E = item.infoLabels.get('episode')

    if item.contentType == 'movie':
        db.execute("SELECT played_time FROM viewed WHERE tmdb_id=?", (ID,))

    elif S and E:
        S = item.infoLabels['season']
        E = item.infoLabels['episode']
        db.execute("SELECT played_time FROM viewed WHERE tmdb_id=? AND season=? AND episode=?", (ID, S, E))

    elif E:
        E = item.infoLabels['episode']
        db.execute("SELECT played_time FROM viewed WHERE tmdb_id=? AND episode=?", (ID, E))

    result = db.fetchone()

    if not result: played_time = 0
    else: played_time = result[0]

    return played_time


def set_played_time(item):
    logger.debug()
    from core import db, db_conn

    played_time = item.played_time
    if not item.infoLabels:
        return

    ID = item.infoLabels.get('tmdb_id','')
    if not ID:
        return

    S = item.infoLabels.get('season')
    E = item.infoLabels.get('episode')


    if item.contentType == 'movie':
        db.execute("SELECT played_time FROM viewed WHERE tmdb_id=?", (ID,))
        result = db.fetchone()
        if result:
            if played_time > 0: db.execute("UPDATE viewed SET played_time=? WHERE tmdb_id=?", (played_time, ID))
            else: db.execute("DELETE from viewed WHERE tmdb_id=?", (ID,))
        else: db.execute("INSERT INTO viewed (tmdb_id, played_time) VALUES (?, ?)", (ID, played_time))

    elif S and E:
        db.execute("SELECT played_time FROM viewed WHERE tmdb_id=? AND season = ? AND episode=?", (ID, S, E))
        result = db.fetchone()
        if result:
            if played_time > 0: db.execute("UPDATE viewed SET played_time=? WHERE tmdb_id=? AND season=? AND episode=?", (played_time, ID, S, E))
            else: db.execute("DELETE from viewed WHERE tmdb_id=? AND season=? AND episode=?", (ID, S, E))
        else: db.execute("INSERT INTO viewed (tmdb_id, season, episode, played_time) VALUES (?, ?, ?, ?)", (ID, S, E, played_time))

    elif E:
        E = item.infoLabels['episode']
        db.execute("SELECT played_time FROM viewed WHERE tmdb_id=? AND episode=?", (ID, E))
        result = db.fetchone()
        if result:
            if played_time > 0: db.execute("UPDATE viewed SET played_time=? WHERE tmdb_id=? AND episode=?", (played_time, ID, E))
            else: db.execute("DELETE from viewed WHERE tmdb_id=? AND episode=?", (ID, E))
        else: db.execute("INSERT INTO viewed (tmdb_id, episode, played_time) VALUES (?, ?, ?)", (ID, E, played_time))

    db_conn.commit()


def prevent_busy(item):
    logger.debug()
    if not item.autoplay and not item.window:
        if item.globalsearch: xbmc.Player().play(os.path.join(config.get_runtime_path(), "resources", "kod.mp4"))
        else: xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=os.path.join(config.get_runtime_path(), "resources", "kod.mp4")))
        xbmc.sleep(100)
        xbmc.Player().stop()
        # xbmc.executebuiltin('Action(Stop)')
        # xbmc.sleep(500)
        # xbmc.Player().stop()
        # xbmc.sleep(500)
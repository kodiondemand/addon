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
    from concurrent import futures
else:
    PY3 = False
    import urllib
    from concurrent_py2 import futures

import os, xbmc, xbmcgui, xbmcplugin
from past.utils import old_div
from core import filetools, scrapertools
from core.item import Item
from platformcode import logger, config

addon = config.__settings__

xbmcPlayer = xbmc.Player()

playCanceled = False


def dialogOk(heading, message):
    dialog = xbmcgui.Dialog()
    return dialog.ok(heading, message)


def dialogNotification(heading, message, icon=3, time=5000, sound=True):
    dialog = xbmcgui.Dialog()
    try:
        l_icono = [xbmcgui.NOTIFICATION_INFO, xbmcgui.NOTIFICATION_WARNING, xbmcgui.NOTIFICATION_ERROR, config.addonIcon]
        dialog.notification(heading, message, l_icono[icon], time, sound)
    except:
        dialogOk(heading, message)


def dialogYesNo(heading, message, nolabel=config.getLocalizedString(70170), yeslabel=config.getLocalizedString(30022), autoclose=0, customlabel=None):
    dialog = xbmcgui.Dialog()
    # customlabel only work on kodi 19
    if PY3 and customlabel:
        return dialog.yesnocustom(heading, message, customlabel=customlabel, nolabel=nolabel, yeslabel=yeslabel, autoclose=autoclose)
    else:
        return dialog.yesno(heading, message, nolabel=nolabel, yeslabel=yeslabel, autoclose=autoclose)


def dialogSelect(heading, _list, preselect=0, useDetails=False):
    return xbmcgui.Dialog().select(heading, _list, preselect=preselect, useDetails=useDetails)


def dialogMultiselect(heading, _list, autoclose=0, preselect=[], useDetails=False):
    return xbmcgui.Dialog().multiselect(heading, _list, autoclose=autoclose, preselect=preselect, useDetails=useDetails)


def dialogProgress(heading, message):
    if getWindow() in ('WINDOW_HOME', 'WINDOW_SETTINGS_MENU', 'WINDOW_SETTINGS_INTERFACE', 'WINDOW_SKIN_SETTINGS', 'SKIN'):
        # in widget, hide any progress
        class Dummy(object):
            def __getattr__(self, name):
                def _missing(*args, **kwargs):
                    pass
                return _missing
        return Dummy()
    else:
        dialog = xbmcgui.DialogProgress()
        dialog.create(heading, message)
        return dialog


def dialogProgressBg(heading, message=""):
    try:
        dialog = xbmcgui.DialogProgressBG()
        dialog.create(heading, message)
        return dialog
    except:
        return dialogProgress(heading, message)


def dialogInput(default="", heading="", hidden=False):
    keyboard = xbmc.Keyboard(default, heading, hidden)
    keyboard.doModal()
    if keyboard.isConfirmed():
        return keyboard.getText()
    else:
        return None


def dialogNumeric(_type, heading, default="", option=0):
    dialog = xbmcgui.Dialog()
    d = dialog.numeric(_type, heading, default, option)
    return d


def dialogTextviewer(heading, text):  # available from kodi 16
    return xbmcgui.Dialog().textviewer(heading, text)


def dialogBrowse(_type, heading, shares="files", mask="", useThumbs=False, treatAsFolder=False, defaultt="", enableMultiple=False):
    dialog = xbmcgui.Dialog()
    d = dialog.browse(_type, heading, shares, mask, useThumbs, treatAsFolder, defaultt, enableMultiple)
    return d


def dialogRegister(heading, user=False, email=False, password=False, user_default='', email_default='', password_default='', captcha_img=''):
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
            if config.getXBMCPlatform(True)['num_version'] < 18:
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
                self.getControl(10006).setVisible(False)
                self.getControl(10007).setVisible(False)
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

    dialog = Register('Register.xml', config.getRuntimePath()).Start(heading, user, email, password, user_default, email_default, password_default, captcha_img)
    return dialog


def dialogInfo(item, scraper):
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
            if config.getXBMCPlatform(True)['num_version'] < 18:
                self.setCoordinateResolution(2)
            self.HEADER = self.getControl(100)
            self.TITLE = self.getControl(101)
            self.ID = self.getControl(102)
            self.EXIT = self.getControl(103)
            self.EXIT2 = self.getControl(104)

            self.HEADER.setText(config.getLocalizedString(60228) % self.title)
            self.TITLE.setLabel('[UPPERCASE]' + config.getLocalizedString(60230).replace(':','') + '[/UPPERCASE]')
            self.ID.setLabel(self.idtitle)
            self.setFocusId(101)

        def onClick(self, control):
            if control in [101]:
                result = dialogInput(self.title)
                if result:
                    if self.item.contentType == 'movie': self.item.contentTitle = result
                    else: self.item.contentSerieName = result
                    self.close()
            elif control in [102]:
                result = dialogNumeric(0, self.idtitle, self.id)
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

    dialog = TitleOrIDWindow('TitleOrIDWindow.xml', config.getRuntimePath()).Start(item, scraper)
    return dialog


def dialogSelectGroup(heading, _list, preselect=0):
    class SelectGroup(xbmcgui.WindowXMLDialog):
        def start(self, heading, _list, preselect):
            self.selected = preselect
            self.heading = heading
            self.list = _list
            self.doModal()

            return self.selected

        def onInit(self):
            self.getControl(1).setText(self.heading)
            itemlist = []
            for n, it in enumerate(self.list):
                logger.debug(it)
                item = xbmcgui.ListItem(str(n))
                item.setProperty('title', it[0])
                item.setProperty('seasons', str(it[1]))
                item.setProperty('episodes', str(it[2]))
                item.setProperty('description', '\n' + it[3])
                item.setProperty('thumb', it[4])
                itemlist.append(item)

            self.getControl(2).addItems(itemlist)
            self.setFocusId(2)
            self.getControl(2).selectItem(self.selected)

        def onClick(self, control):
            if control in [100]:
                self.selected = -1
                self.close()
            elif control in [2]:
                self.selected = self.getControl(2).getSelectedPosition()
                self.close()

        def onAction(self, action):
            action = action.getId()
            if action in [10, 92]:
                self.selected = -1
                self.close()

    dialog = SelectGroup('SelectGroup.xml', config.getRuntimePath()).start(heading, _list, preselect)
    return dialog


def dialogBusy(state):
    if state: xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
    else: xbmc.executebuiltin('Dialog.Close(busydialognocancel)')


def itemlistRefresh(offset=0, disable=False):
    if disable:
        xbmc.executebuiltin("Container.Refresh")
    else:
        try:
            _id = xbmcgui.getCurrentWindowId()
            win = xbmcgui.Window(_id)
            cid = win.getFocusId()
            ctl = win.getControl(cid)
            pos = Item().fromurl(xbmc.getInfoLabel('ListItem.FileNameAndPath')).itemlistPosition + offset
            logger.debug('ID:', _id, 'POSITION:', pos)
            xbmc.executebuiltin("Container.Refresh")
            # xbmc.executebuiltin('ReloadSkin()')

            while xbmcgui.getCurrentWindowDialogId() != 10138:
                pass
            while xbmcgui.getCurrentWindowDialogId() == 10138:
                pass

            ctl.selectItem(pos)
        except:
            xbmc.executebuiltin("Container.Refresh")


def itemlistUpdate(item, replace=False):
    if replace:  # reset the path history
        xbmc.executebuiltin("Container.Update(" + sys.argv[0] + "?" + item.tourl() + ", replace)")
    else:
        xbmc.executebuiltin("Container.Update(" + sys.argv[0] + "?" + item.tourl() + ")")


def renderItems(itemlist, parent_item):
    """
    Function used to render itemlist on kodi
    """

    # if it's not a list, do nothing
    if not isinstance(itemlist, list):
        return

    logger.debug('START renderItems')
    thumb_type = config.getSetting('video_thumbnail_type')
    from platformcode import shortcuts
    _handle = int(sys.argv[1])
    default_fanart = config.getFanart()
    def_context_commands = shortcuts.context()

    # if there's no item, add "no elements" item
    if not len(itemlist):
        from core.support import thumb
        itemlist.append(Item(title=config.getLocalizedString(60347), thumbnail=thumb('nofolder')))

    dirItems = []

    def setItem(n, item, parent_item):
        item.itemlistPosition = n
        item_url = item.tourl()

        if item.category == "":
            item.category = parent_item.category
        # If there is no action or it is findvideos / play, folder = False because no listing will be returned
        if item.action in ['play', 'findvideos', '']:
            item.folder = False
        if item.fanart == "":
            item.fanart = parent_item.fanart
        if item.action == 'play' and thumb_type == 1 and not item.forcethumb:
            item.thumbnail = config.getOnlineServerThumb(item.server)

        icon_image = "DefaultFolder.png" if item.folder else "DefaultVideo.png"

        title = setTitle(item)


        listitem = xbmcgui.ListItem(title)
        art = {'icon': icon_image, 'thumb': item.thumbnail, 'poster': item.thumbnail, 'fanart': item.fanart if item.fanart else default_fanart}
        if item.infoLabels.get('landscape'): art['landscape'] = item.infoLabels['landscape']
        if item.infoLabels.get('clearlogo'): art['clearlogo'] = item.infoLabels['clearlogo']
        if item.infoLabels.get('clearart'): art['clearart'] = item.infoLabels['clearart']
        if item.infoLabels.get('banner'): art['banner'] = item.infoLabels['banner']
        if item.infoLabels.get('disc'): art['banner'] = item.infoLabels['disc']
        listitem.setProperty('ResumeTime', str(getPlayedTime(item)))

        listitem.setArt(art)

        if config.getSetting("player_mode") == 1 and item.action == "play" and not item.nfo:
            listitem.setProperty('IsPlayable', 'true')

        if item.infoLabels.get('castandrole'):
            try:
                cast = [{'name':c[0], 'role':c[1], 'thumbnail':c[2], 'order':c[3]} for c in item.infoLabels.get("castandrole", [])]
                cast.sort(key=lambda c: c['order'])
                listitem.setCast(cast)
                del item.infoLabels['castandrole']
            except:
                pass

        setInfolabels(listitem, item)


        # context menu
        if parent_item.channel != 'special':
            context_commands = def_context_commands + setContextCommands(item, item_url, parent_item)
        else:
            context_commands = def_context_commands
        listitem.addContextMenuItems(context_commands)
        return item, item_url, listitem

    # For Debug
    # logger.dbg()
    # r_list = [setItem(i, item, parent_item) for i, item in enumerate(itemlist)]

    r_list = []
    position = None

    with futures.ThreadPoolExecutor() as executor:
        searchList = [executor.submit(setItem, i, item, parent_item) for i, item in enumerate(itemlist)]
        for res in futures.as_completed(searchList):
            r_list.append(res.result())
    r_list.sort(key=lambda it: it[0].itemlistPosition)



    for item, item_url, listitem in r_list:
        if position == None and not item.infoLabels.get('playcount', 0) and item.channel != 'downloads':
            position = item.itemlistPosition
        dirItems.append(('%s?%s' % (sys.argv[0], item_url), listitem, item.folder, len(r_list)))
    xbmcplugin.addDirectoryItems(_handle, dirItems)

    if parent_item.sorted:
        if parent_item.sorted == 'year': xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
        elif parent_item.sorted == 'name':xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)

    if parent_item.list_type == '':
        breadcrumb = parent_item.category #.capitalize()
    else:
        if 'similar' in parent_item.list_type:
            if parent_item.contentTitle != '':
                breadcrumb = config.getLocalizedString(70693) + parent_item.contentTitle
            else:
                breadcrumb = config.getLocalizedString(70693) + parent_item.contentSerieName
        else:
            breadcrumb = config.getLocalizedString(70693)

    xbmcplugin.setPluginCategory(handle=_handle, category=breadcrumb)
    setViewMode(itemlist[0], parent_item)

    ctrl = None
    pos = None
    if parent_item.channel == 'videolibrary' and parent_item.action in ['get_episodes', 'get_seasons'] and position:
        win = xbmcgui.Window(10025)
        ctrlId = win.getFocusId()
        if ctrlId:
            ctrl = win.getControl(ctrlId)
            pos = position  + (1 if xbmc.getInfoLabel('Container(10138).HasParent') else 0)

    updateListing = True if parent_item.update else False
    xbmcplugin.endOfDirectory(_handle, succeeded=True, updateListing=updateListing, cacheToDisc=True)

    if ctrl and pos:
        ctrl.selectItem(pos)

    logger.debug('END renderItems')



def setTitle(item, hideServerName=False):
    from core.support import typo
    title = item.title if item.title else item.contentTitle
    episode = ''

    if title[:1] not in ['[', '•']:
        # if item.contentTitle: title = item.contentTitle
        # elif item.contentSerieName: title = item.contentSerieName
        if type(item.contentSeason) == int and type(item.contentEpisodeNumber) == int and not item.onlyep:
            episode = '{}x{:02d}'.format(item.contentSeason, item.contentEpisodeNumber)
        elif type(item.contentEpisodeNumber) == int:
            episode = '{:02d}'.format(item.contentEpisodeNumber)
            if item.episodeExtra: episode += item.episodeExtra
        if episode and item.episode2:
            if len(item.episode2) < 4: episode = '{}-{}'.format(episode, '-'.join('{:02d}'.format(int(e)) for e in item.episode2))
            else: episode = '{} -> {:02d}'.format(episode, item.episode2[-1])
        if episode: title = '{}. {}'.format(episode, title)
        if item.title2: title = '{} - {}'.format(title, item.title2)

        if config.getSetting('format_title') or item.server:
            server = typo(item.serverName, '__ [] bold') if item.server and hideServerName == False  else ''
            quality = typo(item.quality, '_ [] color kod') if item.quality else ''
            lang = typo(item.contentLanguage, '_ [] color kod') if item.contentLanguage else ''
            extra = typo(item.extraInfo, '_ [] color kod') if item.extraInfo else ''
            size = typo(item.size, '_ [] color kod') if item.size else ''
            seed = typo('Seed: ' + item.seed, '_ [] color kod') if item.seed else ''

            title = '{}{}{}{}{}{}{}'.format(server, title, quality, lang, extra, size, seed)
    return title


def viewModeMonitor():
    if getWindow() == 'WINDOW_VIDEO_NAV':
        try:
            currentModeName = xbmc.getInfoLabel('Container.Viewmode')
            parent_info = xbmc.getInfoLabel('Container.FolderPath')
            item_info = xbmc.getInfoLabel('Container.ListItemPosition(2).FileNameAndPath')
            parent_item = Item().fromurl(parent_info)
            win = xbmcgui.Window(10025)
            currentMode = int(win.getFocusId())
            if currentModeName and 'plugin.video.kod' in parent_info and 50 <= currentMode < 1000:  # inside addon and in itemlist view
                content, Type = getCurrentView(Item().fromurl(item_info) if item_info else Item(), Item().fromurl(parent_info))
                if content:
                    defaultMode = int(config.getSetting('view_mode_%s' % content).split(',')[-1])
                    if currentMode != defaultMode:
                        config.setSetting('view_mode_%s' % content, currentModeName + ', ' + str(currentMode))
                        # dialogNotification(config.getLocalizedString(70153),
                        #                                 config.getLocalizedString(70187) % (content, currentModeName),
                        #                                 sound=False)
        except:
            import traceback
            logger.error(traceback.print_exc())


def getCurrentView(item=None, parent_item=None):

    if not item:
        item = Item()
    if not parent_item:
        logger.debug('ESCO')
        return None, None

    parent_actions = ['movies', 'news', 'search', 'get_from_temp', 'newest', 'discover_list', 'new_search', 'channel_search']

    addons = 'addons' if config.getSetting('touch_view') else ''

    if parent_item.action == 'findvideos' or (parent_item.action in ['channel_search', 'new_search'] and parent_item.infoLabels['tmdb_id']):
        return 'server', addons

    elif parent_item.action == 'mainlist':
        return 'channel', addons

    elif (item.contentType in ['movie'] and parent_item.action in parent_actions) \
            or (item.channel in ['videolibrary'] and parent_item.action in ['list_movies']) \
            or (parent_item.channel in ['favorites'] and parent_item.action in ['mainlist']) \
            or parent_item.action in ['now_on_tv', 'now_on_misc', 'now_on_misc_film', 'mostrar_perfil', 'live', 'replay', 'news']:
        return 'movie', 'movies'

    elif (item.contentType in ['tvshow'] and parent_item.action in parent_actions) \
            or (item.channel in ['videolibrary'] and parent_item.action in ['list_tvshows']):
        return 'tvshow', 'tvshows'

    elif parent_item.action in ['episodes', 'get_episodes'] or item.contentType == 'episode':
        return 'episode', 'tvshows'

    elif parent_item.action in ['get_seasons']:
        logger.debug('CONTENTTYPE:',item.contentType)
        return 'season', 'tvshows'

    elif parent_item.action in ['getmainlist', '', 'getchanneltypes']:
        return 'home', addons

    elif parent_item.action in ['filterchannels']:
        return 'channels', addons

    else:
        return 'menu', addons

    # else:
    #     return None, None


def setViewMode(item, parent_item):
    def resetViewMode():
        for mode in ['menu','channel','channels','home', 'movie','tvshow','season','episode','server']:
            config.setSetting('skin_name', xbmc.getSkinDir())
            config.setSetting('view_mode_{}'.format(mode), config.getLocalizedString(70003) + ' , 0')

    if xbmc.getSkinDir() != config.getSetting('skin_name') or not config.getSetting('skin_name'):
        resetViewMode()
        xbmcplugin.setContent(handle=int(sys.argv[1]), content='')
        xbmc.executebuiltin('Container.SetViewMode({})'.format(55))

    content, Type = getCurrentView(item, parent_item)
    if content:
        mode = int(config.getSetting('view_mode_{}'.format(content)).split(',')[-1])
        if mode == 0:
            logger.debug('default mode')
            mode = 55
        xbmcplugin.setContent(handle=int(sys.argv[1]), content=Type)
        xbmc.executebuiltin('Container.SetViewMode({})'.format(mode))
        logger.debug('TYPE: ' + Type + ' - ' + 'CONTENT: ' + content)


def setInfolabels(listitem, item, player=False):
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

    infoLabels_dict = {'aired': 'aired', 'album': 'album', 'artist': 'artist', 'cast': 'cast', 'castandrole': 'castandrole',
                       'tmdb_id': 'code', 'code': 'code', 'country': 'country', 'credits': 'credits', 'release_date': 'dateadded',
                       'dateadded': 'dateadded', 'dbid': 'dbid', 'director': 'director', 'duration': 'duration', 'episode': 'episode',
                       'episode_plot': 'episodeguide', 'episode_title': 'title', 'episode_vote_average': 'rating', 'episode_vote_count': 'votes',
                       'genre': 'genre', 'imdb_id': 'imdbnumber', 'imdbnumber': 'imdbnumber', 'last_air_date': 'lastplayed', 'mediatype': 'mediatype',
                       'mpaa': 'mpaa', 'originaltitle': 'originaltitle', 'overlay': 'overlay', 'poster_path': 'path', 'playcount': 'playcount',
                       'plot': 'plot', 'plotoutline': 'plotoutline', 'premiered': 'premiered', 'rating': 'rating', 'season': 'season', 'set': 'set',
                       'setid': 'setid', 'setoverview': 'setoverview', 'showlink': 'showlink', 'sortepisode': 'sortepisode', 'sortseason': 'sortseason',
                       'sorttitle': 'sorttitle', 'status': 'status', 'studio': 'studio', 'tag': 'tag', 'tagline': 'tagline', 'title': 'title',
                       'top250': 'top250', 'tracknumber': 'tracknumber', 'trailer': 'trailer', 'tvshowtitle': 'tvshowtitle', 'userrating': 'userrating',
                       'votes': 'votes', 'writer': 'writer', 'year': 'year'}
    # if item.infoLabels:
    try:
        infoLabels_kodi = {infoLabels_dict[label_tag]: item.infoLabels[label_tag] for label_tag, label_value in list(item.infoLabels.items()) if label_tag in infoLabels_dict}
        listitem.setInfo("video", infoLabels_kodi)
    except:
        listitem.setInfo("video", item.infoLabels)
            # logger.error(item.infoLabels)
        # if item.infoLabels.get('castandrole'):
        #     cast = [{'name':c[0], 'role':c[1], 'thumbnail':c[2], 'order':c[3]} for c in item.infoLabels.get("castandrole", [])]
        #     listitem.setCast(cast)
    # listitem.setInfo("video", item.infoLabels)


def setContextCommands(item, item_url, parent_item, **kwargs):
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
    # num_version_xbmc = config.getXBMCPlatform(True)['num_version']

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
    if item.action and item.action not in ["add_movie_to_library", "add_serie_to_library", "buscartrailer", "actualizar_titulos"]:
        # if item.nextPage:
        #     context_commands.append((config.getLocalizedString(70511), "RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, 'action=gotopage&real_action='+item.action)))
        # Show information: if the item has a plot, we assume that it is a series, season, chapter or movie
        # if item.infoLabels['plot'] and (num_version_xbmc < 17.0 or item.contentType == 'season'):
        #     context_commands.append((config.getLocalizedString(60348), "Action(Info)"))

        # InfoPlus
        # if config.getSetting("infoplus"):
            #if item.infoLabels['tmdb_id'] or item.infoLabels['imdb_id'] or item.infoLabels['tvdb_id'] or \
            #        (item.contentTitle and item.infoLabels["year"]) or item.contentSerieName:
        if item.infoLabels['tmdb_id'] or item.infoLabels['imdb_id'] or item.infoLabels['tvdb_id']:
            context_commands.append(("InfoPlus", "RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, 'channel=infoplus&action=start&from_channel=' + item.channel)))
        if config.getSetting("token_trakt", "trakt") and item.contentType in ['movie', 'tvshow']:
            context_commands.append((config.getLocalizedString(70318), "RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, 'channel=trakt_tools&action=context')))
        # Open in browser and previous menu
        if parent_item.channel not in ["news", "channelselector", "downloads", "search"] and item.action != "mainlist" and not parent_item.noMainMenu:
            context_commands.insert(1, (config.getLocalizedString(70739), "Container.Update (%s?%s)" % (sys.argv[0], Item(channel= 'shortcuts', action="open_browser", url=item.url).tourl())))

        # Add to kodfavoritos (My links)
        if item.channel not in ["favorites", "videolibrary", "help", ""] and parent_item.channel != "favorites":
            context_commands.append( (config.getLocalizedString(70557), "RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, urllib.urlencode({'channel': "kodfavorites", 'action': "addFavourite", 'from_channel': item.channel, 'from_action': item.action}))))
        # Add to kodfavoritos 
        if parent_item.channel == 'globalsearch':
            context_commands.append( (config.getLocalizedString(30155), "RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, urllib.urlencode({'channel': "favorites", 'action': "addFavourite", 'from_channel': item.channel, 'from_action': item.action}))))
        # Search in other channels
        if item.contentTitle and item.contentType in ['movie', 'tvshow'] and parent_item.channel not in ['search', 'globalsearch'] and item.action not in ['play'] and parent_item.action != 'mainlist':

            # Search in other channels
            if item.contentSerieName != '':
                item.wanted = item.contentSerieName
            else:
                item.wanted = item.contentTitle

            if item.contentType == 'tvshow':
                mediatype = 'tv'
            else:
                mediatype = item.contentType

            if config.getSetting('new_search'):
                context_commands.append((config.getLocalizedString(60350), "RunPlugin (%s?%s&%s)" % (sys.argv[0], item_url, urllib.urlencode({'channel': 'search', 'action': "from_context", 'from_channel': item.channel, 'contextual': True}))))
            else:
                context_commands.append((config.getLocalizedString(60350), "Container.Refresh (%s?%s&%s)" % (sys.argv[0], item_url, urllib.urlencode({'channel': 'search', 'action': "from_context", 'from_channel': item.channel, 'contextual': True, 'text': item.wanted}))))
            context_commands.append( (config.getLocalizedString(70561), "Container.Update (%s?%s&%s)" % (sys.argv[0], item_url, 'channel=search&action=from_context&search_type=list&page=1&list_type=%s/%s/similar' % (mediatype, item.infoLabels['tmdb_id']))))

        if item.channel != "videolibrary" and item.videolibrary != False and not item.disable_videolibrary:
            # Add Series to the video library
            if item.contentTitle or item.contentSerieName:
                context_commands.append((config.getLocalizedString(30161), "RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, 'action=add_to_library&from_action={}&contentChannel=videolibrary'.format(item.action))))

        if not item.local and item.channel not in ["downloads", "filmontv", "search"] and item.server != 'torrent' and parent_item.action != 'mainlist' and config.getSetting('downloadenabled') and not item.disable_videolibrary:
            # Download movie
            if item.contentType == "movie":
                context_commands.append((config.getLocalizedString(60354), "RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, 'channel=downloads&action=save_download&from_channel=' + item.channel + '&from_action=' + item.action)))

            elif item.contentSerieName:
                # Download series
                if item.contentType == "tvshow" and item.action not in ['findvideos']:
                    if item.channel == 'videolibrary':
                        context_commands.append((config.getLocalizedString(60003), "RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, 'channel=downloads&action=save_download&unseen=true&from_channel=' + item.channel + '&from_action=' + item.action)))
                    context_commands.append((config.getLocalizedString(60355), "RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, 'channel=downloads&action=save_download&from_channel=' + item.channel + '&from_action=' + item.action)))
                    context_commands.append((config.getLocalizedString(60357), "RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, 'channel=downloads&action=save_download&download=season&from_channel=' + item.channel + '&from_action=' + item.action)))
                # Download episode
                elif item.contentType == "episode" and item.action in ['findvideos']:
                    context_commands.append((config.getLocalizedString(60356), "RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, 'channel=downloads&action=save_download&from_channel=' + item.channel + '&from_action=' + item.action)))
                # Download season
                elif item.contentType == "season":
                    context_commands.append((config.getLocalizedString(60357), "RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, 'channel=downloads&action=save_download&download=season&from_channel=' + item.channel + '&from_action=' + item.action)))

        # Search trailer...
        if (item.contentTitle and item.contentType in ['movie', 'tvshow']) or "buscar_trailer" in context:
            context_commands.append((config.getLocalizedString(60359), "RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url, urllib.urlencode({ 'channel': "trailertools", 'action': "buscartrailer", 'search_title': item.contentTitle if item.contentTitle else item.fulltitle, 'contextual': True}))))

        
    if config.devMode():
        context_commands.insert(0, ("item info", "Container.Update (%s?%s)" % (sys.argv[0], Item(channel='platformtools', action="itemInfo", parent=item.tojson()).tourl())))
    return context_commands


def isPlaying():
    return xbmcPlayer.isPlaying()


def getWindow():
    """
    Return if addon is used as widget
    For doing so, it check current window ID (https://kodi.wiki/view/Window_IDs)
    """
    winId = xbmcgui.getCurrentWindowId()
    if winId == 9999:
        return 'WINDOW_INVALID'
    elif winId == 10000:
        return 'WINDOW_HOME'
    elif winId == 10001:
        return 'WINDOW_PROGRAMS'
    elif winId == 10002:
        return 'WINDOW_PICTURES'
    elif winId == 10003:
        return 'WINDOW_FILES'
    elif winId == 10004:
        return 'WINDOW_SETTINGS_MENU'
    elif winId == 10007:
        return 'WINDOW_SYSTEM_INFORMATION'
    elif winId == 10011:
        return 'WINDOW_SCREEN_CALIBRATION'

    elif winId == 10016:
        return 'WINDOW_SETTINGS_START'
    elif winId == 10016:
        return 'WINDOW_SETTINGS_SYSTEM'
    elif winId == 10018:
        return 'WINDOW_SETTINGS_SERVICE'

    elif winId == 10021:
        return 'WINDOW_SETTINGS_MYPVR'
    elif winId == 10022:
        return 'WINDOW_SETTINGS_MYGAMES'

    elif winId == 10025:
        return 'WINDOW_VIDEO_NAV'
    elif winId == 10028:
        return 'WINDOW_VIDEO_PLAYLIST'

    elif winId == 10029:
        return 'WINDOW_LOGIN_SCREEN'

    elif winId == 10030:
        return 'WINDOW_SETTINGS_PLAYER'
    elif winId == 10031:
        return 'WINDOW_SETTINGS_MEDIA'
    elif winId == 10032:
        return 'WINDOW_SETTINGS_INTERFACE'

    elif winId == 10034:
        return 'WINDOW_SETTINGS_PROFILES'
    elif winId == 10035:
        return 'WINDOW_SKIN_SETTINGS'

    elif winId == 10040:
        return 'WINDOW_ADDON_BROWSER'

    elif winId == 10050:
        return 'WINDOW_EVENT_LOG'

    elif winId == 97:
        return 'WINDOW_SCREENSAVER_DIM'
    elif winId == 98:
        return 'WINDOW_DEBUG_INFO'
    elif winId == 10099:
        return 'WINDOW_DIALOG_POINTER'
    elif winId == 10100:
        return 'WINDOW_DIALOG_YES_NO'
    elif winId == 10101:
        return 'WINDOW_dialogProgress'
    elif winId == 10103:
        return 'WINDOW_DIALOG_KEYBOARD'
    elif winId == 10104:
        return 'WINDOW_DIALOG_VOLUME_BAR'
    elif winId == 10105:
        return 'WINDOW_DIALOG_SUB_MENU'
    elif winId == 10106:
        return 'WINDOW_DIALOG_CONTEXT_MENU'
    elif winId == 10107:
        return 'WINDOW_DIALOG_KAI_TOAST'
    elif winId == 10109:
        return 'WINDOW_dialogNumeric'
    elif winId == 10110:
        return 'WINDOW_DIALOG_GAMEPAD'
    elif winId == 10111:
        return 'WINDOW_DIALOG_BUTTON_MENU'
    elif winId == 10114:
        return 'WINDOW_DIALOG_PLAYER_CONTROLS'
    elif winId == 10115:
        return 'WINDOW_DIALOG_SEEK_BAR'
    elif winId == 10116:
        return 'WINDOW_DIALOG_PLAYER_PROCESS_INFO'
    elif winId == 10120:
        return 'WINDOW_DIALOG_MUSIC_OSD'
    elif winId == 10121:
        return 'WINDOW_DIALOG_VIS_SETTINGS'
    elif winId == 10122:
        return 'WINDOW_DIALOG_VIS_PRESET_LIST'
    elif winId == 10123:
        return 'WINDOW_DIALOG_VIDEO_OSD_SETTINGS'
    elif winId == 10124:
        return 'WINDOW_DIALOG_AUDIO_OSD_SETTINGS'
    elif winId == 10125:
        return 'WINDOW_DIALOG_VIDEO_BOOKMARKS'
    elif winId == 10126:
        return 'WINDOW_DIALOG_FILE_BROWSER'
    elif winId == 10128:
        return 'WINDOW_DIALOG_NETWORK_SETUP'
    elif winId == 10129:
        return 'WINDOW_DIALOG_MEDIA_SOURCE'
    elif winId == 10130:
        return 'WINDOW_DIALOG_PROFILE_SETTINGS'
    elif winId == 10131:
        return 'WINDOW_DIALOG_LOCK_SETTINGS'
    elif winId == 10132:
        return 'WINDOW_DIALOG_CONTENT_SETTINGS'
    elif winId == 10133:
        return 'WINDOW_DIALOG_LIBEXPORT_SETTINGS'
    elif winId == 10134:
        return 'WINDOW_DIALOG_FAVOURITES'
    elif winId == 10135:
        return 'WINDOW_DIALOG_SONG_INFO'
    elif winId == 10136:
        return 'WINDOW_DIALOG_SMART_PLAYLIST_EDITOR'
    elif winId == 10137:
        return 'WINDOW_DIALOG_SMART_PLAYLIST_RULE'
    elif winId == 10138:
        return 'WINDOW_dialogBusy'
    elif winId == 10139:
        return 'WINDOW_DIALOG_PICTURE_INFO'
    elif winId == 10140:
        return 'WINDOW_DIALOG_ADDON_SETTINGS'
    elif winId == 10142:
        return 'WINDOW_DIALOG_FULLSCREEN_INFO'
    elif winId == 10145:
        return 'WINDOW_DIALOG_SLIDER'
    elif winId == 10146:
        return 'WINDOW_DIALOG_ADDON_INFO'
    elif winId == 10147:
        return 'WINDOW_DIALOG_TEXT_VIEWER'
    elif winId == 10148:
        return 'WINDOW_DIALOG_PLAY_EJECT'
    elif winId == 10149:
        return 'WINDOW_DIALOG_PERIPHERALS'
    elif winId == 10150:
        return 'WINDOW_DIALOG_PERIPHERAL_SETTINGS'
    elif winId == 10151:
        return 'WINDOW_DIALOG_EXT_PROGRESS'
    elif winId == 10152:
        return 'WINDOW_DIALOG_MEDIA_FILTER'
    elif winId == 10153:
        return 'WINDOW_DIALOG_SUBTITLES'
    elif winId == 10156:
        return 'WINDOW_DIALOG_KEYBOARD_TOUCH'
    elif winId == 10157:
        return 'WINDOW_DIALOG_CMS_OSD_SETTINGS'
    elif winId == 10158:
        return 'WINDOW_dialogInfoPROVIDER_SETTINGS'
    elif winId == 10159:
        return 'WINDOW_DIALOG_SUBTITLE_OSD_SETTINGS'
    elif winId == 10160:
        return 'WINDOW_dialogBusy_NOCANCEL'

    elif winId == 10500:
        return 'WINDOW_MUSIC_PLAYLIST'
    elif winId == 10502:
        return 'WINDOW_MUSIC_NAV'
    elif winId == 10503:
        return 'WINDOW_MUSIC_PLAYLIST_EDITOR'

    elif winId == 10550:
        return 'WINDOW_DIALOG_OSD_TELETEXT'

    # PVR related Window and Dialog ID's

    elif 10600 < winId < 10613:
        return 'WINDOW_DIALOG_PVR'


    elif 10700 < winId < 10711:
        return 'WINDOW_PVR_ID'

    # virtual windows for PVR specific keymap bindings in fullscreen playback
    elif winId == 10800:
        return 'WINDOW_FULLSCREEN_LIVETV'
    elif winId == 10801:
        return 'WINDOW_FULLSCREEN_RADIO'
    elif winId == 10802:
        return 'WINDOW_FULLSCREEN_LIVETV_PREVIEW'
    elif winId == 10803:
        return 'WINDOW_FULLSCREEN_RADIO_PREVIEW'
    elif winId == 10804:
        return 'WINDOW_FULLSCREEN_LIVETV_INPUT'
    elif winId == 10805:
        return 'WINDOW_FULLSCREEN_RADIO_INPUT'

    elif winId == 10820:
        return 'WINDOW_DIALOG_GAME_CONTROLLERS'
    elif winId == 10821:
        return 'WINDOW_GAMES'
    elif winId == 10822:
        return 'WINDOW_DIALOG_GAME_OSD'
    elif winId == 10823:
        return 'WINDOW_DIALOG_GAME_VIDEO_FILTER'
    elif winId == 10824:
        return 'WINDOW_DIALOG_GAME_STRETCH_MODE'
    elif winId == 10825:
        return 'WINDOW_DIALOG_GAME_VOLUME'
    elif winId == 10826:
        return 'WINDOW_DIALOG_GAME_ADVANCED_SETTINGS'
    elif winId == 10827:
        return 'WINDOW_DIALOG_GAME_VIDEO_ROTATION'
    elif 11100 < winId < 11199:
        return 'SKIN'  # WINDOW_ID's from 11100 to 11199 reserved for Skins

    elif winId == 12000:
        return 'WINDOW_dialogSelect'
    elif winId == 12001:
        return 'WINDOW_DIALOG_MUSIC_INFO'
    elif winId == 12002:
        return 'WINDOW_dialogOk'
    elif winId == 12003:
        return 'WINDOW_DIALOG_VIDEO_INFO'
    elif winId == 12005:
        return 'WINDOW_FULLSCREEN_VIDEO'
    elif winId == 12006:
        return 'WINDOW_VISUALISATION'
    elif winId == 12007:
        return 'WINDOW_SLIDESHOW'
    elif winId == 12600:
        return 'WINDOW_WEATHER'
    elif winId == 12900:
        return 'WINDOW_SCREENSAVER'
    elif winId == 12901:
        return 'WINDOW_DIALOG_VIDEO_OSD'

    elif winId == 12902:
        return 'WINDOW_VIDEO_MENU'
    elif winId == 12905:
        return 'WINDOW_VIDEO_TIME_SEEK'  # virtual window for time seeking during fullscreen video

    elif winId == 12906:
        return 'WINDOW_FULLSCREEN_GAME'

    elif winId == 12997:
        return 'WINDOW_SPLASH'  # splash window
    elif winId == 12998:
        return 'WINDOW_START'  # first window to load
    elif winId == 12999:
        return 'WINDOW_STARTUP_ANIM'  # for startup animations

    elif 13000 < winId < 13099:
        return 'PYTHON'  # WINDOW_ID's from 13000 to 13099 reserved for Python

    elif 14000 < winId < 14099:
        return 'ADDON'  # WINDOW_ID's from 14000 to 14099 reserved for Addons


def playVideo(item, strm=False, force_direct=False, autoplay=False):
    logger.debug(item)

    def play():
        if item.channel == 'downloads':
            logger.debug("Play local video: %s [%s]" % (item.fulltitle, item.url))
            xlistitem = setListitem(item, item.url)
            setPlayer(item, xlistitem, item.url, True, None) # Fix Play From Download Section
            return

        default_action = config.getSetting("default_action")
        logger.debug("default_action=%s" % default_action)

        # pass referer
        if item.referer:
            from core import httptools
            httptools.default_headers['Referer'] = item.referer

        # Open the selection dialog to see the available options
        options, videoUrls, selection, _exit = getOptionsDialog(item, default_action, strm, autoplay)
        if _exit: return

        # get default option of addon configuration
        selection = getSelection(default_action, options, selection, videoUrls)

        # Canceled box
        if selection < 0:
            # preventBusy(item)
            return

        logger.debug("selection=%d" % selection)
        logger.debug("selection=%s" % options[selection])

        # run the available option, jdwonloader, download, favorites, add to the video library ... IF IT IS NOT PLAY
        _exit = setOption(item, selection, options, videoUrls)
        if _exit:
            return

        # we get the selected video
        mediaUrl, view, mpd, m3u8 = getSelectedVideo(item, selection, videoUrls, autoplay)
        if not mediaUrl: return

        # video information is obtained.
        xlistitem = setListitem(item, item.url)
        setInfolabels(xlistitem, item, True)

        # if it is a video in mpd format, the listitem is configured to play it ith the inpustreamaddon addon implemented in Kodi 17
        if mpd or item.manifest == 'mpd':
            if not installInputstream():
                return
            xlistitem.setProperty('inputstream' if PY3 else 'inputstreamaddon', 'inputstream.adaptive')
            xlistitem.setProperty('inputstream.adaptive.manifest_type', 'mpd')
            if item.drm and item.license:
                # installWidevine()
                xlistitem.setProperty("inputstream.adaptive.license_type", item.drm)
                xlistitem.setProperty("inputstream.adaptive.license_key", item.license)
                xlistitem.setMimeType('application/dash+xml')
        elif m3u8 or item.manifest == 'hls':
            if not installInputstream():
                return
            xlistitem.setProperty('inputstream' if PY3 else 'inputstreamaddon', 'inputstream.adaptive')
            xlistitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
            xlistitem.setMimeType('application/x-mpegURL')
            xlistitem.setProperty("inputstream.adaptive.license_type", item.drm)
            xlistitem.setProperty("inputstream.adaptive.license_key", item.license)

        if force_direct: item.window = True

        setPlayer(item, xlistitem, mediaUrl, view, strm)
        return True

    if not play():
        # close db to ensure his thread will stop
        from core import db
        db.close()


def stopVideo():
    xbmcPlayer.stop()


def getSelection(default_action, options, selection, videoUrls):
    resolutions = []
    for url in videoUrls:
        resolutions.append(calcResolution(url['res']) if 'res' in url else 0)

    resolutions.sort()
    if default_action == 2: resolutions.reverse()

     # ask
    if default_action == 0:
        # "Choose an option"
        selection = dialogSelect(config.getLocalizedString(30163), options)
    else:
        selection = 0

    return selection


def calcResolution(option):
    match = scrapertools.find_single_match(option, '([0-9]{2,4})(?:p|i|x[0-9]{2,4}|)')
    resolution = 0

    if match:
        resolution = int(match)
    elif 'sd' in option.lower():
        resolution = 480
    elif 'hd' in option.lower():
        resolution = 720
        if 'full' in option.lower():
            resolution = 1080
    elif '2k' in option.lower():
        resolution = 1440
    elif '4k' in option.lower():
        resolution = 2160
    elif 'auto' in option.lower():
        resolution = 10000

    return resolution


def showChannelSettings(**kwargs):
    """
    It shows a customized configuration box for each channel and saves the data when closing it.
    The parameters passed to it can be seen in the method that is called

    @return: returns the window with the elements
    @rtype: SettingsWindow
    """
    from platformcode.xbmc_config_menu import SettingsWindow
    # return SettingsWindow("ChannelSettings.xml", config.getRuntimePath()).start(**kwargs)
    return SettingsWindow("ChSettings.xml", config.getRuntimePath()).start(**kwargs)


def showVideoInfo(*args, **kwargs):
    """
    It shows a window with the info of the video.
    The parameters passed to it can be seen in the method that is called

    @return: returns the window with the elements
    @rtype: InfoWindow
    """

    from platformcode.xbmc_info_window import InfoWindow
    return InfoWindow("InfoWindow.xml", config.getRuntimePath()).start(*args, **kwargs)


def showRecaptcha(key, referer):
    from platformcode.recaptcha import Recaptcha
    return Recaptcha("Recaptcha.xml", config.getRuntimePath()).Start(key, referer)


def alertNoDisponibleServer(server):
    # 'The video is no longer in %s', 'Try another server or another channel'
    dialogOk(config.getLocalizedString(30055), (config.getLocalizedString(30057) % server) + '\n' + config.getLocalizedString(30058))


def alertUnsopportedServer():
    # 'Unsupported or unknown server ',' Test on another server or on another channel'
    dialogOk(config.getLocalizedString(30065), config.getLocalizedString(30058))


def handleWait(time_to_wait, title, text):
    logger.debug("handleWait(time_to_wait=%d)" % time_to_wait)
    waiting = dialogProgress(' ' + title, "")

    secs = 0
    increment = int(old_div(100, time_to_wait))

    cancelled = False
    while secs < time_to_wait:
        secs += 1
        percent = increment * secs
        secsLeft = str((time_to_wait - secs))
        remaining_display = config.getLocalizedString(70176) + secsLeft + config.getLocalizedString(70177)
        waiting.update(percent, ' ' + text, remaining_display)
        xbmc.sleep(1000)
        if waiting.iscanceled():
            cancelled = True
            break

    if cancelled:
        logger.debug('Wait canceled')
        return False
    else:
        logger.debug('Wait finished')
        return True


def getOptionsDialog(item, default_action, strm, autoplay):
    logger.debug()
    # logger.debug(item.tostring('\n'))
    from core import servertools

    options = []
    error = False

    try:
        item.server = item.server.lower()
    except AttributeError:
        item.server = ""

    if item.server == "":
        item.server = "directo"

    # If it is not the normal mode, it does not show the dialog because XBMC hangs
    muestra_dialogo = (config.getSetting("player_mode") == 0 and not strm)

    # Extract the URLs of the videos, and if you can't see it, it tells you the reason
    # Allow multiple qualities for "direct" server

    if item.videoUrls:
        videoUrls, puedes, motivo = item.videoUrls, True, ""
    else:
        videoUrls, puedes, motivo = servertools.resolve_videoUrls_for_playing(
            item.server, item.url, item.password, muestra_dialogo)

    if playCanceled:
        return options, [], 0, True

    selection = 0
    # If you can see the video, present the options
    if puedes:
        videoUrls = sorted(videoUrls, key=lambda k: calcResolution(k['res']) if 'res' in k else 0)
        videoUrls.reverse()
        for videoUrl in videoUrls:
            name = '{} {} [{}]'.format(config.getLocalizedString(60221), videoUrl.get('type'), servertools.get_server_parameters(item.server)['name'])
            if videoUrl.get('res',''): name += ' [{}]'.format(videoUrl.get('res',''))
            options.append(name)

        if item.server == "local":
            options.append(config.getLocalizedString(30164))
        else:
            # "Download"
            downloadenabled = config.getSetting('downloadenabled')
            if downloadenabled != False and item.channel != 'videolibrary':
                opcion = config.getLocalizedString(30153)
                options.append(opcion)

            if item.isFavourite:
                # "Remove from favorites"
                options.append(config.getLocalizedString(30154))
            else:
                # "Add to Favorites"
                options.append(config.getLocalizedString(30155))

        if default_action == 3:
            selection = len(options) - 1

        # Search for trailers
        if item.channel not in ["trailertools"]:
            # "Search Trailer"
            options.append(config.getLocalizedString(30162))

    # If you can't see the video it informs you
    else:
        if not autoplay:
            if item.server != "":
                if "<br/>" in motivo:
                    ret = dialogYesNo(config.getLocalizedString(60362) % item.server, motivo.split("<br/>")[0] + '\n' + motivo.split("<br/>")[1], nolabel='ok', yeslabel=config.getLocalizedString(70739))
                else:
                    ret = dialogYesNo(config.getLocalizedString(60362) % item.server, motivo, nolabel='ok', yeslabel=config.getLocalizedString(70739))
            else:
                ret = dialogYesNo(config.getLocalizedString(60362) % item.server, config.getLocalizedString(60363) + '\n' + config.getLocalizedString(60364), nolabel='ok', yeslabel=config.getLocalizedString(70739))
            if ret:
                xbmc.executebuiltin("Container.Update (%s?%s)" %
                                    (sys.argv[0], Item(action="open_browser", url=item.url).tourl()))
            if item.channel == "favorites":
                # "Remove from favorites"
                options.append(config.getLocalizedString(30154))

            if len(options) == 0:
                error = True

    return options, videoUrls, selection, error


def setOption(item, selection, options, videoUrls):
    logger.debug()
    # logger.debug(item.tostring('\n'))
    _exit = False
    # You have not chosen anything, most likely because you have given the ESC

    if selection == -1:
        # To avoid the error "One or more elements failed" when deselecting from strm file
        listitem = setListitem(item)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, listitem)

    # "Download"
    elif options[selection] == config.getLocalizedString(30153):
        from specials import downloads

        if item.contentType == "list" or item.contentType == "tvshow":
            item.contentType = "video"
        item.play_menu = True
        downloads.save_download(item)
        _exit = True

    # "Remove from favorites"
    elif options[selection] == config.getLocalizedString(30154):
        from specials import favorites
        favorites.delFavourite(item)
        _exit = True

    # "Add to Favorites":
    elif options[selection] == config.getLocalizedString(30155):
        from specials import favorites
        item.from_channel = "favorites"
        favorites.addFavourite(item)
        _exit = True

    # "Search Trailer":
    elif options[selection] == config.getLocalizedString(30162):
        config.setSetting("subtitulo", False)
        xbmc.executebuiltin("RunPlugin(%s?%s)" % (sys.argv[0], item.clone(channel="trailertools", action="buscartrailer", contextual=True).tourl()))
        _exit = True

    return _exit


def getSelectedVideo(item, selection, videoUrls, autoplay=False):
    logger.debug()
    mediaUrl = ""
    view = False
    waitTime = 0
    fileType = ''
    mpd = False
    m3u8 = False
    # videoUrls Format:
    #    [{'type':'Video Extension', 'url': 'Video url', 'wait':seconds to wait, 'sub':'subtitle url'}]
    # You have chosen one of the videos
    if selection < len(videoUrls):
        videoUrl = videoUrls[selection]
        mediaUrl = videoUrl.get('url', '')
        waitTime = videoUrl.get('wait', 0)
        fileType = videoUrl.get('type', 'Video').lower()
        if not item.subtitle: item.subtitle = videoUrl.get('sub', '')
        view = True

    if 'mpd' in fileType:
        mpd = True
    elif 'm3u8' in fileType:
        m3u8 = True

    # If there is no mediaUrl it is because the video is not there :)
    logger.debug("mediaUrl=" + mediaUrl)
    if mediaUrl == "" and not autoplay:
        if item.server == "unknown":
            alertUnsopportedServer()
        else:
            alertNoDisponibleServer(item.server)

    # If there is a timeout (like in megaupload), impose it now
    if waitTime > 0:
        continuar = handleWait(waitTime, item.server, config.getLocalizedString(60365))
        if not continuar:
            mediaUrl = ""

    return mediaUrl, view, mpd, m3u8


def setPlayer(item, xlistitem, mediaUrl, view, strm):
    logger.debug()
    item.options = {'strm':False}
    # logger.debug("item:\n" + item.tostring('\n'))

    # Get Media Url for play Torrent
    if item.server == "torrent":
        mediaUrl = playTorrent(item, mediaUrl)
        if not mediaUrl:
            return

    # If it is a strm file, play is not necessary
    if strm:
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xlistitem)
        if item.subtitle:
            xbmc.sleep(2000)
            xbmcPlayer.setSubtitles(item.subtitle)

    else:
        if type(item.player_mode) == int:
            player_mode = item.player_mode
        else:
            player_mode = config.getSetting("player_mode")
        if (player_mode == 3 and mediaUrl.startswith("rtmp")): player_mode = 0
        elif "megacrypter.com" in mediaUrl: player_mode = 3
        logger.info("mediaUrl=" + mediaUrl)

        if player_mode in [0,1]:
            if player_mode in [1] and item.server != "torrent":
                item.played_time = resumePlayback(getPlayedTime(item))

            from core import db
            db['control']['playItem'] = item
            db.close()

            logger.info('Player Mode:',['Direct', 'Bookmark'][player_mode])
            # Add the listitem to a playlist
            playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            playlist.clear()
            playlist.add(mediaUrl, xlistitem)
            # Reproduce
            xbmcPlayer.play(playlist, xlistitem)
            addNextToPlaylist(item)

            if config.getSetting('trakt_sync'):
                from core import trakt_tools
                trakt_tools.wait_for_update_trakt()

        elif player_mode == 2:
            logger.info('Player Mode: Built-In')
            xbmc.executebuiltin("PlayMedia(" + mediaUrl + ")")

        elif player_mode == 3:
            logger.info('Player Mode: Download and Play')
            from platformcode import download_and_play
            download_and_play.download_and_play(mediaUrl, "download_and_play.tmp", config.getSetting("downloadpath"))
            return

    # ALL LOOKING TO REMOVE VIEW
    if item.subtitle and view:
        logger.info("External subtitles: " + item.subtitle)
        xbmc.sleep(2000)
        xbmcPlayer.setSubtitles(item.subtitle)

    # if it is a video library file send to mark as seen
    if strm or item.strm_path or item.from_library: item.options['strm'] = True


def addNextToPlaylist(item):
    import threading
    from core import filetools, videolibrarytools
    from platformcode import xbmc_videolibrary
    def addToPlaylist(item):
        if item.contentType != 'movie':
            next= xbmc_videolibrary.next_ep(item)
            if next:
                next.back = True
                nextItem = setListitem(item, next.url)
                nextItem.setArt({"thumb": next.contentThumbnail if next.contentThumbnail else next.thumbnail})
                nexturl = "plugin://plugin.video.kod/?" + next.tourl()
                playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
                playlist.add(nexturl, nextItem)
                addToPlaylist(next)
    if item.contentType != 'movie' and config.getSetting('next_ep') == 3:
        threading.Thread(target=addToPlaylist, args=[item]).start()


def torrentClientInstalled(showTuple=False):
    # External plugins found in servers / torrent.json node clients
    from core import filetools
    from core import jsontools
    torrentClients = jsontools.getNodeFromFile("torrent.json", "clients", filetools.join(config.getRuntimePath(), "servers"))
    torrentOptions = []
    for client in torrentClients:
        if xbmc.getCondVisibility('System.HasAddon("%s")' % client["id"]):
            if showTuple:
                torrentOptions.append([client["name"], client["url"]])
            else:
                torrentOptions.append(client["name"])
    return torrentOptions


def playTorrent(item, mediaUrl):
    logger.debug()
    # logger.dbg()
    import time
    from servers import torrent

    torrentOptions = torrentClientInstalled(showTuple=True)
    if len(torrentOptions) == 0:
        from platformcode import elementum_download
        elementum_download.download()
        return playTorrent(item, mediaUrl)
    elif len(torrentOptions) > 1:
        selection = dialogSelect(config.getLocalizedString(70193), [opcion[0] for opcion in torrentOptions])
    else:
        selection = 0

    if selection >= 0:
        # preventBusy()

        mediaUrl = urllib.quote_plus(item.url)
        torr_client = torrentOptions[selection][0]

        if torr_client in ['elementum'] and item.infoLabels['tmdb_id']:
            if item.contentType == 'episode' and "elementum" not in torr_client:
                mediaUrl += "&episode=%s&library=&season=%s&show=%s&tmdb=%s&type=episode" % (item.infoLabels['episode'], item.infoLabels['season'], item.infoLabels['tmdb_id'], item.infoLabels['tmdb_id'])
            elif item.contentType == 'movie':
                mediaUrl += "&library=&tmdb=%s&type=movie" % (item.infoLabels['tmdb_id'])

        if torr_client in ['elementum'] and item.downloadFilename:
            torrent.elementum_download(item)
        else:
            import xbmcaddon
            addon = xbmcaddon.Addon(id='plugin.video.elementum')
            if addon.getSetting('download_storage') == '0':
                addon.setSetting('download_storage', '1')
                xbmc.sleep(3000)
            mediaUrl = torrentOptions[selection][1] % mediaUrl
        return mediaUrl
    return ''


def resumePlayback(played_time):
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
        Dialog = ResumePlayback('ResumePlayback.xml', config.getRuntimePath(), played_time=played_time)
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

def installInputstream():
    from xbmcaddon import Addon
    if not filetools.exists(filetools.join(xbmc.translatePath('special://home/addons/'),'inputstream.adaptive')) and not filetools.exists(filetools.join(xbmc.translatePath('special://xbmcbinaddons/'),'inputstream.adaptive')):
        try:
            # See if there's an installed repo that has it
            xbmc.executebuiltin('InstallAddon(inputstream.adaptive)', wait=True)

            # Check if InputStream add-on exists!
            Addon('inputstream.adaptive')

            logger.info('InputStream add-on installed from repo.')
        except RuntimeError:
            logger.info('InputStream add-on not installed.')
            dialogOk(config.getLocalizedString(20000), config.getLocalizedString(30126))
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


def installWidevine():
    addonName = 'script.module.inputstreamhelper'
    def isHelper():
        ret = False
        if filetools.exists(xbmc.translatePath('special://home/addons/{}'.format(addonName))):
            ret = True
        return ret

    if isHelper():
        from  xbmcaddon import Addon
        addon = Addon(id=addonName)
        path = filetools.join(addon.getAddonInfo('Path'), 'lib')
        sys.path.append(path)
        from inputstreamhelper import Helper
        helper = Helper('mpd', drm='widevine')
        # logger.dbg()
        helper._update_widevine()


def getPlayedTime(item):
    logger.debug()
    from core import videolibrarydb

    played_time = 0
    if not item.infoLabels:
        return 0
    ID = item.infoLabels.get('tmdb_id', '')
    if not ID:
        return 0

    s = item.infoLabels.get('season',0)
    e = item.infoLabels.get('episode')
    result = None

    try:
        result = videolibrarydb['viewed'].get(ID)
        if type(result) == dict:
            result = videolibrarydb['viewed'].get(ID, {}).get('{}x{}'.format(s, e), 0)
        played_time = result

    except:
        import traceback
        logger.error(traceback.format_exc())
        del videolibrarydb['viewed'][ID]

    return played_time


def setPlayedTime(item):
    logger.debug()
    # logger.dbg()
    from core import videolibrarydb

    played_time = item.played_time
    if not item.infoLabels:
        return

    ID = item.infoLabels.get('tmdb_id', '')
    if not ID:
        return

    s = item.infoLabels.get('season',0)
    e = item.infoLabels.get('episode',0)

    try:
        # logger.dbg()
        if e:
            newDict = videolibrarydb['viewed'].get(ID, {})
            newDict['{}x{}'.format(s, e)] = played_time
            videolibrarydb['viewed'][ID] = newDict

        else:
            videolibrarydb['viewed'][ID] = played_time

    except:
        import traceback
        logger.error(traceback.format_exc())
        del videolibrarydb['viewed'][ID]

    videolibrarydb.close()


def preventBusy():
    xbmc.executebuiltin('Dialog.Close(all,true)')


def fakeVideo():
    media = filetools.join(config.getRuntimePath(), "resources", "kod.mp4")
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=media))
    while not isPlaying():
        xbmc.sleep(100)
    if xbmc.getCondVisibility("system.platform.android"):
        xbmc.sleep(300)
    xbmc.Player().stop()


def serverWindow(item, itemlist):
    from core import filetools, jsontools

    LEFT = 1
    RIGHT = 2
    UP = 3
    DOWN = 4
    ENTER = 7
    EXIT = 10
    BACKSPACE = 92

    class ServerWindow(xbmcgui.WindowXML):
        def start(self, item, itemlist):
            self.itemlist = itemlist
            self.item = item
            self.servers = []
            items = []
            self.selection = -1
            self.actions = {}

            for videoitem in self.itemlist:
                videoitem.thumbnail = config.getOnlineServerThumb(videoitem.server)
                quality = ' [' + videoitem.quality + ']' if videoitem.quality else ''
                if videoitem.server:
                    color = scrapertools.find_single_match(videoitem.alive, r'(FF[^\]]+)')
                    it = xbmcgui.ListItem('{}{}'.format(videoitem.serverName, quality))

                    # format Title
                    if self.item.contentSeason and self.item.contentEpisodeNumber:
                        title = '{}x{:02d}. {}'.format(self.item.contentSeason, self.item.contentEpisodeNumber, self.item.contentTitle)
                    elif self.item.contentEpisodeNumber:
                        title = '{:02d}. {}'.format(self.item.contentEpisodeNumber, self.item.contentTitle)
                    else:
                        title = self.item.contentTitle

                    it.setProperties({'name': title, 'channel': videoitem.ch_name, 'color': color if color else 'FF0082C2'})
                    it.setArt({'poster':self.item.contentThumbnail if self.item.contentThumbnail else self.item.thumbnail, 'thumb':videoitem.thumbnail,  'fanart':videoitem.fanart})
                    self.servers.append(it)
                    items.append(videoitem)
                else:
                    # logger.dbg()
                    it = xbmcgui.ListItem(videoitem.title)
                    if 'library' in videoitem.action:
                        self.actions['videolibrary'] = videoitem
                    if 'download' in videoitem.action:
                        self.actions['download'] = videoitem

            self.itemlist = items
            self.doModal()

        def onInit(self):
            self.SERVERS = self.getControl(100)
            self.VIDEOLIBRARY = self.getControl(102)
            self.DOWNLOAD = self.getControl(103)
            if 'videolibrary' not in self.actions.keys():
                self.VIDEOLIBRARY.setVisible(False)
            if 'download' not in self.actions.keys():
                self.DOWNLOAD.setVisible(False)
            self.SERVERS.reset()
            self.SERVERS.addItems(self.servers)
            self.setFocusId(100)

        def onAction(self, action):
            action = action.getId()
            focus = self.getFocusId()
            if action in [UP, DOWN, LEFT, RIGHT] and focus not in [100, 101, 102, 103]:
                self.setFocusId(100)
            elif action in [EXIT, BACKSPACE]:
                self.close()

        def onClick(self, control):
            if control == 100:
                self.selection = self.itemlist[self.SERVERS.getSelectedPosition()].clone(window=True)
                self.run(self.selection)
            elif control in [102]:
                self.run(self.actions['videolibrary'])
            elif control in [103]:
                self.run(self.actions['download'])

        def run(self, action):
            from platformcode.launcher import run
            run(action)


    if itemlist:
        xbmc.executebuiltin('Dialog.Close(all)')
        ServerWindow('Servers.xml', config.getRuntimePath()).start(item, itemlist)


def channelImport(channelId):
    ch = ''
    path = filetools.join(config.getRuntimePath(), '{}', channelId + ".py")
    if filetools.exists(path.format('channels')): ch = 'channels.{}'.format(channelId)
    elif filetools.exists(path.format('specials')): ch = 'specials.{}'.format(channelId)
    elif filetools.exists(path.format('platformcode')): ch = 'platformcode.{}'.format(channelId)
    elif filetools.exists(path.format('core')): ch = 'core.{}'.format(channelId)
    if ch:
        channel = __import__(ch, None, None, [ch])
    else:
        logger.info('Channel {} not Exist'.format(channelId))
        channel = None
    return channel


def itemInfo(item):
    dialogTextviewer('Item info', item.parent)

def setListitem(item, url=''):
    listitem = xbmcgui.ListItem(setTitle(item, hideServerName=True), path=url)
    listitem.setArt({'icon': "DefaultVideo.png", "thumb": item.contentThumbnail if item.contentThumbnail else item.thumbnail})
    setInfolabels(listitem, item, True)
    return listitem


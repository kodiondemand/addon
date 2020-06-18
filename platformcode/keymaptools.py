# -*- coding: utf-8 -*-

from builtins import map
import sys, xbmc, xbmcaddon, xbmcgui, base64, json
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int
from threading import Timer

from channelselector import get_thumb
from platformcode import config, logger
import channelselector


class KeyListener(xbmcgui.WindowXMLDialog):
    TIMEOUT = 10

    def __new__(cls):
        gui_api = tuple(map(int, xbmcaddon.Addon('xbmc.gui').getAddonInfo('version').split('.')))
        if gui_api >= (5, 11, 0):
            filenname = "DialogNotification.xml"
        else:
            filenname = "DialogKaiToast.xml"
        return super(KeyListener, cls).__new__(cls, filenname, "")


    def __init__(self):
        self.key = None


    def onInit(self):
        try:
            self.getControl(401).addLabel(config.get_localized_string(70698))
            self.getControl(402).addLabel(config.get_localized_string(70699) % self.TIMEOUT)
        except AttributeError:
            self.getControl(401).setLabel(config.get_localized_string(70698))
            self.getControl(402).setLabel(config.get_localized_string(70699) % self.TIMEOUT)


    def onAction(self, action):
        code = action.getButtonCode()
        if code == 0:
            self.key = None
        else:
            self.key = str(code)
        self.close()


    @staticmethod
    def record_key():
        dialog = KeyListener()
        timeout = Timer(KeyListener.TIMEOUT, dialog.close)
        timeout.start()
        dialog.doModal()
        timeout.cancel()
        key = dialog.key
        del dialog
        return key


def set_key():
    saved_key = config.get_setting("shortcut_key")
    new_key = KeyListener().record_key()

    if new_key and saved_key != new_key:
        from core import filetools
        from platformcode import platformtools
        import xbmc
        file_xml = "special://profile/keymaps/kod.xml"
        data = '<keymap><global><keyboard><key id="%s">' % new_key + 'runplugin(plugin://plugin.video.kod/?ew0KICAgICJhY3Rpb24iOiAia2V5bWFwIiwNCiAgICAib3BlbiI6IHRydWUNCn0=)</key></keyboard></global></keymap>'
        filetools.write(xbmc.translatePath(file_xml), data)
        platformtools.dialog_notification(config.get_localized_string(70700),config.get_localized_string(70702))

        config.set_setting("shortcut_key", new_key)

    return


def delete_key():
    from core import filetools
    from platformcode import platformtools
    import xbmc

    filetools.remove(xbmc.translatePath( "special://profile/keymaps/kod.xml"))
    platformtools.dialog_notification(config.get_localized_string(70701),config.get_localized_string(70702))

    config.set_setting("shortcut_key", '')


class Main(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.items = []


    def onInit(self):
        #### Compatibility with Kodi 18 ####
        if config.get_platform(True)['num_version'] < 18:
            self.setCoordinateResolution(2)

        for menuentry in menu:
            if not menuentry.channel: menuentry.channel = prevchannel
            item = xbmcgui.ListItem(menuentry.title)
            if not submenu and menuentry.channel in ['news', 'channelselector', 'search', 'videolibrary']:
                item.setProperty('sub', 'Controls/spinUp-Focus.png')
            if menuentry.title != 'Redirect':
                for key , value in json.loads(menuentry.tojson()).items():
                    item.setProperty(key, str(value))
                item.setProperty('run', menuentry.tojson())
                self.items.append(item)

        self.getControl(32500).addItems(self.items)
        self.setFocusId(32500)


    def onClick(self, control_id):
        if control_id == 32500:
            action = self.getControl(32500).getSelectedItem().getProperty('run')
            self.close()
            xbmc.executebuiltin('ActivateWindow(10025, "plugin://plugin.video.kod/?' + base64.b64encode(action) + '")')



    def onAction(self, action):
        # exit
        if action.getId() in [xbmcgui.ACTION_PREVIOUS_MENU, xbmcgui.ACTION_NAV_BACK]:
            self.close()
            if submenu: open_shortcut_menu(self=True)

        if action.getId() == xbmcgui.ACTION_CONTEXT_MENU:
            config.open_settings()

        focus = self.getFocusId()

        if action == 3:
            if focus == 61:
                self.setFocusId(32500)
            elif submenu:
                self.close()
                open_shortcut_menu(self=True)
            elif self.getControl(32500).getSelectedItem().getProperty('channel') in ['news', 'channelselector', 'search', 'videolibrary']:
                channel_name = self.getControl(32500).getSelectedItem().getProperty('channel')
                if channel_name == 'channelselector':
                    import channelselector
                    self.close()
                    open_shortcut_menu(channelselector.getchanneltypes(), channel_name, self=True)
                else:
                    from core.item import Item
                    channel = __import__('specials.%s' % channel_name, fromlist=["specials.%s" % channel_name])
                    self.close()
                    open_shortcut_menu(channel.mainlist(Item()), channel_name, self=True)


def open_shortcut_menu(newmenu='', channel='', self=False):
    if not self: xbmc.executebuiltin('Dialog.Close(all,true)')
    global menu
    global submenu
    global prevchannel
    prevchannel = channel
    if newmenu:
        menu = newmenu
        submenu = True
    else:
        menu = channelselector.getmainlist()
        submenu = False
    XML =  'ShortCutMenu.xml'
    if config.get_setting('icon_set') == 'dark':
        XML = 'Dark' + XML
    main = Main(XML, config.get_runtime_path())
    main.doModal()
    del main

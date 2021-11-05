# -*- coding: utf-8 -*-

from builtins import map
import xbmc, xbmcaddon, xbmcgui, re
from threading import Timer
from platformcode import config, logger, platformtools, launcher
from core import filetools
from core.item import Item
import channelselector
addon_icon = filetools.join( config.__settings__.getAddonInfo( "path" ),'resources', 'media', 'logo.png' )

background = 'FF232323'
overlay = '77232323'
text = 'FFFFFFFF'
select = 'FF0082C2'
if config.get_setting('icon_set') == 'dark':
    background = 'FFDCDCDC'
    overlay = '77DCDCDC'
    text = 'FF232323'
    select = 'FF78BDDF'

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
            self.getControl(400).setImage(addon_icon)
            self.getControl(401).addLabel(config.get_localized_string(70698))
            self.getControl(402).addLabel(config.get_localized_string(70699) % self.TIMEOUT)
        except AttributeError:
            self.getControl(400).setImage(addon_icon)
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
        # platformtools.dialog_notification(config.get_localized_string(70700),config.get_localized_string(70702),4)

        config.set_setting("shortcut_key", new_key)

    return


def delete_key():
    from core import filetools
    from platformcode import platformtools
    import xbmc

    filetools.remove(xbmc.translatePath( "special://profile/keymaps/kod.xml"))
    # platformtools.dialog_notification(config.get_localized_string(70701),config.get_localized_string(70702),4)

    config.set_setting("shortcut_key", '')
    xbmc.executebuiltin('Action(reloadkeymaps)')

LEFT = 1
RIGHT = 2
UP = 3
DOWN = 4
EXIT = 10
BACKSPACE = 92
RIGHTCLICK = 101
MOUSEMOVE = 107

class Main(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.items = []

    def onInit(self):
        self.MENU = self.getControl(1)
        self.SUBMENU = self.getControl(2)
        #### Compatibility with Kodi 18 ####
        if config.get_platform(True)['num_version'] < 18:
            self.setCoordinateResolution(2)

        itemlist = self.menulist(channelselector.getmainlist())

        self.MENU.addItems(itemlist)
        self.setFocusId(1)
        self.submenu()

    def menulist(self, menu):
        itemlist = []
        self.getControl(200).setLabel(background)
        self.getControl(201).setLabel(overlay)
        self.getControl(202).setLabel(select)
        self.getControl(203).setLabel(text)
        for menuentry in menu:
            # if not menuentry.channel: menuentry.channel = 'news'

            title = re.sub(r'(\[[/]?COLOR[^\]]*\])','',menuentry.title)
            item = xbmcgui.ListItem(title)
            item.setProperty('channel', menuentry.channel)
            item.setProperty('focus', '0')
            item.setProperty('thumbnail', menuentry.thumbnail)
            if menuentry.channel not in ['downloads', 'setting', 'help']:
                item.setProperty('sub', 'true')
            item.setProperty('run', menuentry.tourl())
            itemlist.append(item)
        return itemlist


    def onClick(self, control_id):
        if control_id in [1, 2]:
            action = self.getControl(control_id).getSelectedItem().getProperty('run')
            self.close()
            if Item().fromurl(action).folder == False:
                xbmc.executebuiltin('RunPlugin("plugin://plugin.video.kod/?' + action + '")')
            else:
                xbmc.executebuiltin('ActivateWindow(10025, "plugin://plugin.video.kod/?' + action + '")')

        elif control_id in [101]:
            self.setFocusId(2)
        elif control_id in [102]:
            self.setFocusId(1)



    def onAction(self, action):
        if action.getButtonCode() == config.get_setting('shortcut_key'):
            self.close()

        action = action.getId()

        if action in [EXIT, BACKSPACE, RIGHTCLICK]:
            self.close()

        focus = self.getFocusId()

        if action in [LEFT, RIGHT, MOUSEMOVE] and self.getFocusId() in [1]:
            if focus in [1]:
                self.submenu()
            else:
                itfocus = str(self.SUBMENU.getSelectedPosition())
                self.MENU.getSelectedItem().setProperty('focus', itfocus)


    def submenu(self):
        itemlist = []
        channel_name = self.MENU.getSelectedItem().getProperty('channel')
        focus = int(self.MENU.getSelectedItem().getProperty('focus'))
        if channel_name == 'channelselector':
            import channelselector
            itemlist = self.menulist(channelselector.getchanneltypes())
        elif channel_name not in ['downloads', 'setting', 'help']:
            channel = __import__('specials.%s' % channel_name, fromlist=["specials.%s" % channel_name])
            itemlist = self.menulist(channel.mainlist(Item().fromurl(self.MENU.getSelectedItem().getProperty('run'))))
        self.SUBMENU.reset()
        self.SUBMENU.addItems(itemlist)
        self.SUBMENU.selectItem(focus)

    def context(self):
        focus = self.getFocusId()
        item_url = self.MENU.getSelectedItem().getProperty('run')
        item = Item().fromurl(item_url)
        commands = platformtools.set_context_commands(item, item_url, Item())
        context = [c[0] for c in commands]
        context_commands = [c[1].replace('Container.Refresh', 'RunPlugin').replace('Container.Update', 'RunPlugin') for c in commands]
        index = xbmcgui.Dialog().contextmenu(context)
        if index > 0: xbmc.executebuiltin(context_commands[index])


def open_shortcut_menu():
    if xbmcgui.getCurrentWindowDialogId() == 9999:
        main = Main('ShortCutMenu.xml', config.get_runtime_path())
        main.doModal()

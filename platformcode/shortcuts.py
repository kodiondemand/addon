# -*- coding: utf-8 -*-
import sys
from platformcode import logger, platformtools, config

def context():
    from platformcode import config
    context = []
    # original
    # if config.getSetting('quick_menu'): context.append((config.getLocalizedString(60360).upper(), "RunPlugin(plugin://plugin.video.kod/?%s)" % Item(channel='shortcuts', action="shortcut_menu").tourl()))
    # if config.getSetting('kod_menu'): context.append((config.getLocalizedString(60026), "RunPlugin(plugin://plugin.video.kod/?%s)" % Item(channel='shortcuts', action="settings_menu").tourl()))

    # pre-serialised
    if config.getSetting('quick_menu'): context.append((config.getLocalizedString(60360), 'RunPlugin(plugin://plugin.video.kod/?channel=shortcuts&action=shortcut_menu)'))
    # if config.getSetting('kod_menu'): context.append((config.getLocalizedString(60026), 'RunPlugin(plugin://plugin.video.kod/?ewogICAgImFjdGlvbiI6ICJzZXR0aW5nc19tZW51IiwgCiAgICAiY2hhbm5lbCI6ICJzaG9ydGN1dHMiLCAKICAgICJpbmZvTGFiZWxzIjoge30KfQ%3D%3D)'))

    return context

def open_browser(item):
    import webbrowser
    if not webbrowser.open(item.url):
        import xbmc
        if xbmc.getCondVisibility('system.platform.linux') and xbmc.getCondVisibility('system.platform.android'):  # android
            xbmc.executebuiltin('StartAndroidActivity("", "android.intent.action.VIEW", "", "%s")' % item.url)
        else:
            platformtools.dialogOk(config.getLocalizedString(20000), config.getLocalizedString(70740) % "\n".join([item.url[j:j+57] for j in range(0, len(item.url), 57)]))

def gotopage(item):
    item.channel = item.from_cannel
    from core import scrapertools
    head = config.getLocalizedString(70511)
    scraped_page = scrapertools.find_single_match(item.url,'[=/]([0-9]+)')

    if item.total_pages and (item.page or scraped_page.isdigit()):
        pages = [str(p) for p in range(1, item.total_pages + 1)]
        page = item.page if item.page else int(scraped_page)
        page = platformtools.dialogSelect(head, pages, page - 2) + 1
    else:
        page = platformtools.dialogNumeric(0, head)
    if page and int(page) > -1:
        import xbmc
        item.action = item.real_action
        item.page = int(page)
        item.update = True
        import re
        item.url = re.sub('([=/])[0-9]+(/?)$', '\g<1>{}\g<2>'.format(page), item.url)
        xbmc.executebuiltin("Container.Update(%s?%s)" % (sys.argv[0], item.tourl()))

def gotoseason(item):
    item.channel = item.from_cannel	
    head = 'Seleziona la stagione'
    seasons = [str(s) for s in item.allSeasons]
    season = platformtools.dialogSelect(head, seasons, item.nextSeason - 1)
    if int(season) > -1:
        import xbmc
        item.action = item.real_action
        item.nextSeason = season
        item.update = True
        xbmc.executebuiltin("Container.Update(%s?%s)" % (sys.argv[0], item.tourl()))


def shortcut_menu(item):
    from platformcode import keymaptools
    if item.add:
        keymaptools.set_key()
    elif item.delete:
        keymaptools.delete_key()
    else:
        keymaptools.open_shortcut_menu()

def settings_menu(item):
    from platformcode import config
    config.openSettings()

def servers_menu(item):
    from core import servertools
    from core.item import Item
    from platformcode import config, platformtools
    from specials import setting

    names = []
    ids = []

    if item.type == 'debriders':
        action = 'server_debrid_config'
        server_list = list(servertools.get_debriders_list().keys())
        for server in server_list:
            server_parameters = servertools.get_server_parameters(server)
            if server_parameters['has_settings'] and server_parameters['active']:
                names.append(server_parameters['name'])
                ids.append(server)

        select = platformtools.dialogSelect(config.getLocalizedString(60552), names)
        if select != -1:
            ID = ids[select]

            it = Item(channel = 'settings',
                    action = action,
                    config = ID)
            setting.server_debrid_config(it)
    else:
        action = 'server_config'
        server_list = list(servertools.get_servers_list().keys())
        for server in sorted(server_list):
            server_parameters = servertools.get_server_parameters(server)
            if server_parameters["has_settings"] and [x for x in server_parameters["settings"]] and server_parameters['active']:
                names.append(server_parameters['name'])
                ids.append(server)

        select = platformtools.dialogSelect(config.getLocalizedString(60538), names)
        if select != -1:
            ID = ids[select]

            it = Item(channel = 'settings',
                    action = action,
                    config = ID)

            setting.server_config(it)
    if select != -1:
        servers_menu(item)

def channels_menu(item):
    import channelselector
    from core import channeltools
    from core.item import Item
    from platformcode import config, platformtools
    from specials import setting

    names = []
    ids = []

    channel_list = channelselector.filterchannels("all")
    for channel in channel_list:
        if not channel.channel:
            continue
        channel_parameters = channeltools.get_channel_parameters(channel.channel)
        if channel_parameters["has_settings"]:
            names.append(channel.title)
            ids.append(channel.channel)

    select = platformtools.dialogSelect(config.getLocalizedString(60537), names)
    if select != -1:
        ID = ids[select]

        it = Item(channel='settings',
                action="channel_config",
                config=ID)

        setting.channel_config(it)
        return channels_menu(item)

def check_channels(item):
    from specials import setting
    from platformcode import config, platformtools
    item.channel = 'setting'
    item.extra = 'lib_check_datajson'
    itemlist = setting.conf_tools(item)
    text = ''
    for item in itemlist:
        text += item.title + '\n'

    platformtools.dialogTextviewer(config.getLocalizedString(60537), text)

def SettingOnPosition(item):
    # addonId is the Addon ID
    # item.category is the Category (Tab) offset (0=first, 1=second, 2...etc)
    # item.setting is the Setting (Control) offse (0=first, 1=second, 2...etc)
    # This will open settings dialog focusing on fourth setting (control) inside the third category (tab)

    import xbmc
    from platformcode import config

    config.openSettings()
    category = item.category if item.category else 0
    setting = item.setting if item.setting else 0
    logger.debug('SETTING= ' + str(setting))
    xbmc.executebuiltin('SetFocus(%i)' % (category - 100))
    xbmc.executebuiltin('SetFocus(%i)' % (setting - 80))

def select(item):
    from platformcode import config, platformtools
    # item.id = setting ID
    # item.type = labels or values
    # item.values = values separeted by |
    # item.label = string or string id

    label = config.getLocalizedString(int(item.label)) if item.label.isdigit() else item.label
    values = []

    if item.type == 'labels':
        for val in item.values.split('|'):
            values.append(config.getLocalizedString(int(val)))
    else:
        values = item.values.split('|')
    ID = config.getSetting(item.id) if config.getSetting(item.id) else 0
    select = platformtools.dialogSelect(label, values, ID)

    config.setSetting(item.id, values[select])

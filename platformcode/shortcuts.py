# -*- coding: utf-8 -*-
from platformcode import logger, side_menu


def context():
	from platformcode import config
	context = []
	# original
	# if config.get_setting('quick_menu'): context.append((config.get_localized_string(60360).upper(), "RunPlugin(plugin://plugin.video.kod/?%s)" % Item(channel='shortcuts', action="shortcut_menu").tourl()))
	# if config.get_setting('side_menu'): context.append((config.get_localized_string(70737).upper(), "RunPlugin(plugin://plugin.video.kod/?%s)" % Item(channel='shortcuts',action="Side_menu").tourl()))
	# if config.get_setting('kod_menu'): context.append((config.get_localized_string(60026), "RunPlugin(plugin://plugin.video.kod/?%s)" % Item(channel='shortcuts', action="settings_menu").tourl()))

	# pre-serialised
	if config.get_setting('quick_menu'): context.append((config.get_localized_string(60360), 'RunPlugin(plugin://plugin.video.kod/?ewogICAgImFjdGlvbiI6ICJzaG9ydGN1dF9tZW51IiwgCiAgICAiY2hhbm5lbCI6ICJzaG9ydGN1dHMiLCAKICAgICJpbmZvTGFiZWxzIjoge30KfQ%3D%3D)'))
	if config.get_setting('Side_menu'): context.append((config.get_localized_string(70737), 'RunPlugin(plugin://plugin.video.kod/?ewogICAgImFjdGlvbiI6ICJTaWRlX21lbnUiLCAKICAgICJjaGFubmVsIjogInNob3J0Y3V0cyIsIAogICAgImluZm9MYWJlbHMiOiB7fQp9)'))
	if config.get_setting('kod_menu'): context.append((config.get_localized_string(60026), 'RunPlugin(plugin://plugin.video.kod/?ewogICAgImFjdGlvbiI6ICJzZXR0aW5nc19tZW51IiwgCiAgICAiY2hhbm5lbCI6ICJzaG9ydGN1dHMiLCAKICAgICJpbmZvTGFiZWxzIjoge30KfQ%3D%3D)'))

	return context

def Side_menu(item):
	side_menu.open_menu(item)

def shortcut_menu(item):
	from platformcode import keymaptools
	keymaptools.open_shortcut_menu()

def settings_menu(item):
	from platformcode import config
	config.open_settings()

def servers_menu(item):
	# from core.support import dbg; dbg()
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
			if server_parameters['has_settings']:
				names.append(server_parameters['name'])
				ids.append(server)

		select = platformtools.dialog_select(config.get_localized_string(60552), names)
		ID = ids[select]

		it = Item(channel = 'settings',
				action = action,
				config = ID)
		return setting.server_debrid_config(it)
	else:
		action = 'server_config'
		server_list = list(servertools.get_servers_list().keys())
		for server in sorted(server_list):
			server_parameters = servertools.get_server_parameters(server)
			if server_parameters["has_settings"] and [x for x in server_parameters["settings"] if x["id"] not in ["black_list", "white_list"]]:
				names.append(server_parameters['name'])
				ids.append(server)

		select = platformtools.dialog_select(config.get_localized_string(60538), names)
		ID = ids[select]

		it = Item(channel = 'settings',
				action = action,
				config = ID)

		return setting.server_config(it)

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

	select = platformtools.dialog_select(config.get_localized_string(60537), names)
	ID = ids[select]

	it = Item(channel='settings',
			  action="channel_config",
			  config=ID)

	return setting.channel_config(it)

def check_channels(item):
	from specials import setting
	from platformcode import config, platformtools
	# from core.support import dbg; dbg()
	item.channel = 'setting'
	item.extra = 'lib_check_datajson'
	itemlist = setting.conf_tools(item)
	text = ''
	for item in itemlist:
		text += item.title + '\n'

	platformtools.dialog_textviewer(config.get_localized_string(60537), text)


def SettingOnPosition(item):
	# addonId is the Addon ID
	# item.category is the Category (Tab) offset (0=first, 1=second, 2...etc)
	# item.setting is the Setting (Control) offse (0=first, 1=second, 2...etc)
	# This will open settings dialog focusing on fourth setting (control) inside the third category (tab)

	import xbmc

	xbmc.executebuiltin('Addon.OpenSettings(plugin.video.kod)')
	category = item.category if item.category else 0
	setting = item.setting if item.setting else 0
	logger.info('SETTING= ' + str(setting))
	xbmc.executebuiltin('SetFocus(%i)' % (category - 100))
	xbmc.executebuiltin('SetFocus(%i)' % (setting - 80))


def select(item):
	from platformcode import config, platformtools
	# item.id = setting ID
	# item.type = labels or values
	# item.values = values separeted by |
	# item.label = string or string id

	label = config.get_localized_string(int(item.label)) if item.label.isdigit() else item.label
	values = []

	if item.type == 'labels':
		for val in item.values.split('|'):
			values.append(config.get_localized_string(int(val)))
	else:
		values = item.values.split('|')

	select = platformtools.dialog_select(label, values, config.get_setting(item.id))
	config.set_setting(item.id, values[select])
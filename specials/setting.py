# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Configuracion
# ------------------------------------------------------------

from channelselector import get_thumb
from core import filetools
from core import servertools
from core.item import Item
from platformcode import config, logger
from platformcode import platformtools
import xbmcgui

CHANNELNAME = "setting"
AUTOSTART = config.is_autorun_enabled()

def mainlist(item):
    logger.info()

    itemlist = list()
    itemlist.append(Item(channel=CHANNELNAME, title=config.get_localized_string(60535), action="settings", folder=False,
                         thumbnail=get_thumb("setting_0.png")))
    if AUTOSTART is False:
        autostart_mode = config.get_localized_string(70707)
    else:
        autostart_mode = config.get_localized_string(70708)
    itemlist.append(Item(channel=CHANNELNAME, title=autostart_mode + " " + config.get_localized_string(70706), action="autostart", folder=False, thumbnail=get_thumb("setting_0.png")))
    
    #itemlist.append(Item(channel=CHANNELNAME, title="", action="", folder=False, thumbnail=get_thumb("setting_0.png")))

    itemlist.append(Item(channel=CHANNELNAME, title=config.get_localized_string(60536) + ":", text_bold=True, action="", folder=False,
                         thumbnail=get_thumb("setting_0.png")))
    itemlist.append(Item(channel=CHANNELNAME, title="     " + config.get_localized_string(60537), action="menu_channels", folder=True,
                         thumbnail=get_thumb("channels.png")))
    itemlist.append(Item(channel=CHANNELNAME, title="     " + config.get_localized_string(60538), action="menu_servers", folder=True,
                         thumbnail=get_thumb("channels.png")))
    itemlist.append(Item(channel="news", title="     " + config.get_localized_string(60539), action="menu_opciones",
                         folder=True, thumbnail=get_thumb("news.png")))
    itemlist.append(Item(channel="search", title="     " + config.get_localized_string(60540), action="opciones", folder=True,
                         thumbnail=get_thumb("search.png")))
    itemlist.append(Item(channel=CHANNELNAME, title="     " + config.get_localized_string(60541), action="channel_config",
                         config="downloads", folder=True, thumbnail=get_thumb("downloads.png")))

    if config.get_videolibrary_support():
        itemlist.append(Item(channel="videolibrary", title="     " + config.get_localized_string(60542), action="channel_config",
                             folder=True, thumbnail=get_thumb("videolibrary.png")))

    if config.is_xbmc():
        itemlist.append(Item(channel=CHANNELNAME, title="     " + config.get_localized_string(70253), action="setting_torrent",
                             folder=True, thumbnail=get_thumb("channels_torrent.png")))
    #itemlist.append(Item(channel=CHANNELNAME, action="", title="", folder=False, thumbnail=get_thumb("setting_0.png")))
    itemlist.append(Item(channel=CHANNELNAME, title=config.get_localized_string(60544), action="submenu_tools", folder=True,
                         thumbnail=get_thumb("setting_0.png")))

    return itemlist


def menu_channels(item):
    logger.info()
    itemlist = list()

    itemlist.append(Item(channel=CHANNELNAME, title=config.get_localized_string(60545), action="conf_tools", folder=False,
                         extra="channels_onoff", thumbnail=get_thumb("setting_0.png")))

    itemlist.append(Item(channel=CHANNELNAME, title=config.get_localized_string(60546) + ":", action="", folder=False,
                         text_bold = True, thumbnail=get_thumb("setting_0.png")))

    # Inicio - Canales configurables
    import channelselector
    from core import channeltools
    channel_list = channelselector.filterchannels("all")
    for channel in channel_list:
        channel_parameters = channeltools.get_channel_parameters(channel.channel)
        if channel_parameters["has_settings"]:
            itemlist.append(Item(channel=CHANNELNAME, title=".    " + config.get_localized_string(60547) % channel.title,
                                 action="channel_config", config=channel.channel, folder=False,
                                 thumbnail=channel.thumbnail))
    # Fin - Canales configurables
    itemlist.append(Item(channel=CHANNELNAME, action="", title="", folder=False, thumbnail=get_thumb("setting_0.png")))
    itemlist.append(Item(channel=CHANNELNAME, title=config.get_localized_string(60548) + ":", action="", folder=False,
                         text_bold=True, thumbnail=get_thumb("channels.png")))
    itemlist.append(Item(channel=CHANNELNAME, title=".    " + config.get_localized_string(60549), action="conf_tools",
                         folder=True, extra="lib_check_datajson", thumbnail=get_thumb("channels.png")))
    return itemlist


def channel_config(item):
    return platformtools.show_channel_settings(channelpath=filetools.join(config.get_runtime_path(), "channels",
                                                                          item.config))


def autostart(item):  # item necessario launcher.py linea 265
    if config.enable_disable_autorun(AUTOSTART):
        xbmcgui.Dialog().ok(config.get_localized_string(20000), config.get_localized_string(70709))
    else:
        xbmcgui.Dialog().ok(config.get_localized_string(20000), config.get_localized_string(70710))


def setting_torrent(item):
    logger.info()

    default = config.get_setting("torrent_client", server="torrent", default=0)

    torrent_options = [config.get_localized_string(30006), config.get_localized_string(70254), config.get_localized_string(70255)]
    torrent_options.extend(platformtools.torrent_client_installed())

    list_controls = [
        {
            "id": "list_torrent",
            "type": "list",
            "label": config.get_localized_string(70256),
            "default": default,
            "enabled": True,
            "visible": True,
            "lvalues": torrent_options
        }
    ]

    platformtools.show_channel_settings(list_controls=list_controls, callback='save_setting_torrent', item=item,
                                        caption=config.get_localized_string(70257), custom_button={'visible': False})


def save_setting_torrent(item, dict_data_saved):
    if dict_data_saved and "list_torrent" in dict_data_saved:
        config.set_setting("torrent_client", dict_data_saved["list_torrent"], server="torrent")

def menu_servers(item):
    logger.info()
    itemlist = list()

    itemlist.append(Item(channel=CHANNELNAME, title=config.get_localized_string(60550), action="servers_blacklist", folder=False,
                         thumbnail=get_thumb("setting_0.png")))

    itemlist.append(Item(channel=CHANNELNAME, title=config.get_localized_string(60551),
                         action="servers_favorites", folder=False, thumbnail=get_thumb("setting_0.png")))

    itemlist.append(Item(channel=CHANNELNAME, title=config.get_localized_string(60552),
                         action="", folder=False, text_bold = True, thumbnail=get_thumb("setting_0.png")))

    # Inicio - Servidores configurables

    server_list = servertools.get_debriders_list().keys()
    for server in server_list:
        server_parameters = servertools.get_server_parameters(server)
        if server_parameters["has_settings"]:
            itemlist.append(
                Item(channel=CHANNELNAME, title = ".    " + config.get_localized_string(60553) % server_parameters["name"],
                     action="server_config", config=server, folder=False, thumbnail=""))

    itemlist.append(Item(channel=CHANNELNAME, title=config.get_localized_string(60554),
                         action="", folder=False, text_bold = True, thumbnail=get_thumb("setting_0.png")))

    server_list = servertools.get_servers_list().keys()

    for server in sorted(server_list):
        server_parameters = servertools.get_server_parameters(server)
        logger.info(server_parameters)
        if server_parameters["has_settings"] and filter(lambda x: x["id"] not in ["black_list", "white_list"],
                                                        server_parameters["settings"]):
            itemlist.append(
                Item(channel=CHANNELNAME, title=".    " + config.get_localized_string(60553) % server_parameters["name"],
                     action="server_config", config=server, folder=False, thumbnail=""))

    # Fin - Servidores configurables

    return itemlist


def server_config(item):
    return platformtools.show_channel_settings(channelpath=filetools.join(config.get_runtime_path(), "servers",
                                                                          item.config))


def servers_blacklist(item):
    server_list = servertools.get_servers_list()
    dict_values = {}

    list_controls = [{"id": "filter_servers",
                      "type": "bool",
                      "label": "@30068",
                      "default": False,
                      "enabled": True,
                      "visible": True}]
    dict_values['filter_servers'] = config.get_setting('filter_servers')
    if dict_values['filter_servers'] == None:
        dict_values['filter_servers'] = False
    for i, server in enumerate(sorted(server_list.keys())):
        server_parameters = server_list[server]
        controls, defaults = servertools.get_server_controls_settings(server)
        dict_values[server] = config.get_setting("black_list", server=server)

        control = {"id": server,
                   "type": "bool",
                   "label": '    %s' % server_parameters["name"],
                   "default": defaults.get("black_list", False),
                   "enabled": "eq(-%s,True)" % (i + 1),
                   "visible": True}
        list_controls.append(control)

    return platformtools.show_channel_settings(list_controls=list_controls, dict_values=dict_values,
                                               caption=config.get_localized_string(60550), callback="cb_servers_blacklist")


def cb_servers_blacklist(item, dict_values):
    f = False
    progreso = platformtools.dialog_progress(config.get_localized_string(60557), config.get_localized_string(60558))
    n = len(dict_values)
    i = 1
    for k, v in dict_values.items():
        if k == 'filter_servers':
            config.set_setting('filter_servers', v)
        else:
            config.set_setting("black_list", v, server=k)
            if v:  # Si el servidor esta en la lista negra no puede estar en la de favoritos
                config.set_setting("favorites_servers_list", 100, server=k)
                f = True
                progreso.update((i * 100) / n, config.get_localized_string(60559) % k)
        i += 1

    if not f:  # Si no hay ningun servidor en la lista, desactivarla
        config.set_setting('filter_servers', False)

    progreso.close()


def servers_favorites(item):
    server_list = servertools.get_servers_list()
    dict_values = {}

    list_controls = [{'id': 'favorites_servers',
                      'type': "bool",
                      'label': config.get_localized_string(60577),
                      'default': False,
                      'enabled': True,
                      'visible': True}]
    dict_values['favorites_servers'] = config.get_setting('favorites_servers')
    if dict_values['favorites_servers'] == None:
        dict_values['favorites_servers'] = False

    server_names = [config.get_localized_string(59992)]

    for server in sorted(server_list.keys()):
        if config.get_setting("black_list", server=server):
            continue

        server_names.append(server_list[server]['name'])

        orden = config.get_setting("favorites_servers_list", server=server)

        if orden > 0:
            dict_values[orden] = len(server_names) - 1

    for x in range(1, 6):
        control = {'id': x,
                   'type': "list",
                   'label': config.get_localized_string(60597) % x,
                   'lvalues': server_names,
                   'default': 0,
                   'enabled': "eq(-%s,True)" % x,
                   'visible': True}
        list_controls.append(control)

    return platformtools.show_channel_settings(list_controls=list_controls, dict_values=dict_values, item=server_names,
                                               caption=config.get_localized_string(60551), callback="cb_servers_favorites")


def cb_servers_favorites(server_names, dict_values):
    dict_name = {}
    progreso = platformtools.dialog_progress(config.get_localized_string(60557), config.get_localized_string(60558))

    for i, v in dict_values.items():
        if i == "favorites_servers":
            config.set_setting("favorites_servers", v)
        elif int(v) > 0:
            dict_name[server_names[v]] = int(i)

    servers_list = servertools.get_servers_list().items()
    n = len(servers_list)
    i = 1
    for server, server_parameters in servers_list:
        if server_parameters['name'] in dict_name.keys():
            config.set_setting("favorites_servers_list", dict_name[server_parameters['name']], server=server)
        else:
            config.set_setting("favorites_servers_list", 0, server=server)
        progreso.update((i * 100) / n, config.get_localized_string(60559) % server_parameters['name'])
        i += 1

    if not dict_name:  # Si no hay ningun servidor en lalista desactivarla
        config.set_setting("favorites_servers", False)

    progreso.close()


def settings(item):
    config.open_settings()


def submenu_tools(item):
    logger.info()
    itemlist = list()

    # Herramientas personalizadas
    import os
    channel_custom = os.path.join(config.get_runtime_path(), 'channels', 'custom.py')
    if not filetools.exists(channel_custom):
        user_custom = os.path.join(config.get_data_path(), 'custom.py')
        if filetools.exists(user_custom):
            filetools.copy(user_custom, channel_custom, silent=True)
    if filetools.exists(channel_custom):
        itemlist.append(Item(channel='custom', action='mainlist', title='Custom Channel'))


    #Disabilitato il menu degli aggiornamenti
    #itemlist.append(Item(channel=CHANNELNAME, action="check_quickfixes", folder=False,
    #                     title=config.get_localized_string(30001), plot="Versión actual: %s" % config.get_addon_version() ))
    itemlist.append(Item(channel=CHANNELNAME, action="update_quasar", folder=False,
                         title=config.get_localized_string(70569)))
    itemlist.append(Item(channel=CHANNELNAME, action="", title="", folder=False,
                         thumbnail=get_thumb("setting_0.png")))

    itemlist.append(Item(channel=CHANNELNAME, title=config.get_localized_string(60564) + ":", action="", folder=False,
                         text_bold=True, thumbnail=get_thumb("channels.png")))
    itemlist.append(Item(channel=CHANNELNAME, title=config.get_localized_string(60565), action="conf_tools",
                         folder=True, extra="lib_check_datajson", thumbnail=get_thumb("channels.png")))

    if config.get_videolibrary_support():
        itemlist.append(Item(channel=CHANNELNAME, action="", title="", folder=False,
                             thumbnail=get_thumb("setting_0.png")))
        itemlist.append(Item(channel=CHANNELNAME, title=config.get_localized_string(60566) + ":", action="", folder=False,
                             text_bold=True, thumbnail=get_thumb("videolibrary.png")))
        itemlist.append(Item(channel=CHANNELNAME, action="overwrite_tools", folder=False,
                             thumbnail=get_thumb("videolibrary.png"),
                             title="- " + config.get_localized_string(60567)))
        itemlist.append(Item(channel="videolibrary", action="update_videolibrary", folder=False,
                             thumbnail=get_thumb("videolibrary.png"),
                             title="- " + config.get_localized_string(60568)))

    return itemlist


def check_quickfixes(item):
    logger.info()    
    
    if not os.path.isfile(config.get_runtime_path() + '/.dev'):
        logger.info("DEV MODE OFF")
        from platformcode import updater
        return updater.check_addon_updates(verbose=True)
    else:
        logger.info("DEV MODE ON")


def update_quasar(item):
    logger.info()
    
    from platformcode import custom_code, platformtools
    stat = False
    stat = custom_code.update_external_addon("quasar")
    if stat:
        platformtools.dialog_notification("Actualización Quasar", "Realizada con éxito")
    else:
        platformtools.dialog_notification("Actualización Quasar", "Ha fallado. Consulte el log")
    
    
def conf_tools(item):
    logger.info()

    # Activar o desactivar canales
    if item.extra == "channels_onoff":
        if config.get_platform(True)['num_version'] >= 17.0: # A partir de Kodi 16 se puede usar multiselect, y de 17 con preselect
            return channels_onoff(item)
        
        import channelselector
        from core import channeltools

        channel_list = channelselector.filterchannels("allchannelstatus")

        excluded_channels = ['url',
                             'search',
                             'videolibrary',
                             'setting',
                             'news',
                             # 'help',
                             'downloads']

        list_controls = []
        try:
            list_controls.append({'id': "all_channels",
                                  'type': "list",
                                  'label': config.get_localized_string(60594),
                                  'default': 0,
                                  'enabled': True,
                                  'visible': True,
                                  'lvalues': ['',
                                              config.get_localized_string(60591),
                                              config.get_localized_string(60592),
                                              config.get_localized_string(60593)]})

            for channel in channel_list:
                # Si el canal esta en la lista de exclusiones lo saltamos
                if channel.channel not in excluded_channels:

                    channel_parameters = channeltools.get_channel_parameters(channel.channel)

                    status_control = ""
                    status = config.get_setting("enabled", channel.channel)
                    # si status no existe es que NO HAY valor en _data.json
                    if status is None:
                        status = channel_parameters["active"]
                        logger.debug("%s | Status (XML): %s" % (channel.channel, status))
                        if not status:
                            status_control = config.get_localized_string(60595)
                    else:
                        logger.debug("%s  | Status: %s" % (channel.channel, status))

                    control = {'id': channel.channel,
                               'type': "bool",
                               'label': channel_parameters["title"] + status_control,
                               'default': status,
                               'enabled': True,
                               'visible': True}
                    list_controls.append(control)

                else:
                    continue

        except:
            import traceback
            logger.error("Error: %s" % traceback.format_exc())
        else:
            return platformtools.show_channel_settings(list_controls=list_controls,
                                                       item=item.clone(channel_list=channel_list),
                                                       caption=config.get_localized_string(60596),
                                                       callback="channel_status",
                                                       custom_button={"visible": False})

    # Comprobacion de archivos channel_data.json
    elif item.extra == "lib_check_datajson":
        itemlist = []
        import channelselector
        from core import channeltools
        channel_list = channelselector.filterchannels("allchannelstatus")

        # Tener una lista de exclusion no tiene mucho sentido por que se comprueba si channel.json tiene "settings",
        # pero por si acaso se deja
        excluded_channels = ['url',
                             'setting',
                             'help']

        try:
            import os
            from core import jsontools
            for channel in channel_list:

                list_status = None
                default_settings = None

                # Se comprueba si el canal esta en la lista de exclusiones
                if channel.channel not in excluded_channels:
                    # Se comprueba que tenga "settings", sino se salta
                    list_controls, dict_settings = channeltools.get_channel_controls_settings(channel.channel)

                    if not list_controls:
                        itemlist.append(Item(channel=CHANNELNAME,
                                             title=channel.title + config.get_localized_string(60569),
                                             action="", folder=False,
                                             thumbnail=channel.thumbnail))
                        continue
                        # logger.info(channel.channel + " SALTADO!")

                    # Se cargan los ajustes del archivo json del canal
                    file_settings = os.path.join(config.get_data_path(), "settings_channels",
                                                 channel.channel + "_data.json")
                    dict_settings = {}
                    dict_file = {}
                    if filetools.exists(file_settings):
                        # logger.info(channel.channel + " Tiene archivo _data.json")
                        channeljson_exists = True
                        # Obtenemos configuracion guardada de ../settings/channel_data.json
                        try:
                            dict_file = jsontools.load(open(file_settings, "rb").read())
                            if isinstance(dict_file, dict) and 'settings' in dict_file:
                                dict_settings = dict_file['settings']
                        except EnvironmentError:
                            logger.error("ERROR al leer el archivo: %s" % file_settings)
                    else:
                        # logger.info(channel.channel + " No tiene archivo _data.json")
                        channeljson_exists = False

                    if channeljson_exists:
                        try:
                            datajson_size = filetools.getsize(file_settings)
                        except:
                            import traceback
                            logger.error(channel.title + config.get_localized_string(60570) % traceback.format_exc())
                    else:
                        datajson_size = None

                    # Si el _data.json esta vacio o no existe...
                    if (len(dict_settings) and datajson_size) == 0 or not channeljson_exists:
                        # Obtenemos controles del archivo ../channels/channel.json
                        needsfix = True
                        try:
                            # Se cargan los ajustes por defecto
                            list_controls, default_settings = channeltools.get_channel_controls_settings(
                                channel.channel)
                            # logger.info(channel.title + " | Default: %s" % default_settings)
                        except:
                            import traceback
                            logger.error(channel.title + config.get_localized_string(60570) % traceback.format_exc())
                            # default_settings = {}

                        # Si _data.json necesita ser reparado o no existe...
                        if needsfix or not channeljson_exists:
                            if default_settings is not None:
                                # Creamos el channel_data.json
                                default_settings.update(dict_settings)
                                dict_settings = default_settings
                                dict_file['settings'] = dict_settings
                                # Creamos el archivo ../settings/channel_data.json
                                json_data = jsontools.dump(dict_file)
                                try:
                                    open(file_settings, "wb").write(json_data)
                                    # logger.info(channel.channel + " - Archivo _data.json GUARDADO!")
                                    # El channel_data.json se ha creado/modificado
                                    list_status = config.get_localized_string(60560)
                                except EnvironmentError:
                                    logger.error("ERROR al salvar el archivo: %s" % file_settings)
                            else:
                                if default_settings is None:
                                    list_status = config.get_localized_string(60571)

                    else:
                        # logger.info(channel.channel + " - NO necesita correccion!")
                        needsfix = False

                    # Si se ha establecido el estado del canal se añade a la lista
                    if needsfix is not None:
                        if needsfix:
                            if not channeljson_exists:
                                list_status = config.get_localized_string(60588)
                                list_colour = "red"
                            else:
                                list_status = config.get_localized_string(60589)
                                list_colour = "green"
                        else:
                            # Si "needsfix" es "false" y "datjson_size" es None habra
                            # ocurrido algun error
                            if datajson_size is None:
                                list_status = config.get_localized_string(60590)
                                list_colour = "red"
                            else:
                                list_status = config.get_localized_string(60589)
                                list_colour = "green"

                    if list_status is not None:
                        itemlist.append(Item(channel=CHANNELNAME,
                                             title=channel.title + list_status,
                                             action="", folder=False,
                                             thumbnail=channel.thumbnail,
                                             text_color=list_colour))
                    else:
                        logger.error("Algo va mal con el canal %s" % channel.channel)

                # Si el canal esta en la lista de exclusiones lo saltamos
                else:
                    continue
        except:
            import traceback
            logger.error("Error: %s" % traceback.format_exc())

        return itemlist


def channels_onoff(item):
    import channelselector, xbmcgui
    from core import channeltools

    # Cargar lista de opciones
    # ------------------------
    lista = []; ids = []
    channels_list = channelselector.filterchannels('allchannelstatus')
    for channel in channels_list:
        channel_parameters = channeltools.get_channel_parameters(channel.channel)
        lbl = '%s' % channel_parameters['language']
        # ~ lbl += ' %s' % [config.get_localized_category(categ) for categ in channel_parameters['categories']]
        lbl += ' %s' % ', '.join(config.get_localized_category(categ) for categ in channel_parameters['categories'])

        it = xbmcgui.ListItem(channel.title, lbl)
        it.setArt({ 'thumb': channel.thumbnail, 'fanart': channel.fanart })
        lista.append(it)
        ids.append(channel.channel)

    # Diálogo para pre-seleccionar
    # ----------------------------
    preselecciones = [config.get_localized_string(70517), config.get_localized_string(70518), config.get_localized_string(70519)]
    ret = platformtools.dialog_select(config.get_localized_string(60545), preselecciones)
    if ret == -1: return False # pedido cancel
    if ret == 2: preselect = []
    elif ret == 1: preselect = range(len(ids))
    else:
        preselect = []
        for i, canal in enumerate(ids):
            channel_status = config.get_setting('enabled', canal)
            if channel_status is None: channel_status = True
            if channel_status:
                preselect.append(i)

    # Diálogo para seleccionar
    # ------------------------
    ret = xbmcgui.Dialog().multiselect(config.get_localized_string(60545), lista, preselect=preselect, useDetails=True)
    if ret == None: return False # pedido cancel
    seleccionados = [ids[i] for i in ret]

    # Guardar cambios en canales activados
    # ------------------------------------
    for canal in ids:
        channel_status = config.get_setting('enabled', canal)
        if channel_status is None: channel_status = True

        if channel_status and canal not in seleccionados:
            config.set_setting('enabled', False, canal)
        elif not channel_status and canal in seleccionados:
            config.set_setting('enabled', True, canal)

    return False


def channel_status(item, dict_values):
    try:
        for k in dict_values:

            if k == "all_channels":
                logger.info("Todos los canales | Estado seleccionado: %s" % dict_values[k])
                if dict_values[k] != 0:
                    excluded_channels = ['url', 'search',
                                         'videolibrary', 'setting',
                                         'news',
                                         'help',
                                         'downloads']

                    for channel in item.channel_list:
                        if channel.channel not in excluded_channels:
                            from core import channeltools
                            channel_parameters = channeltools.get_channel_parameters(channel.channel)
                            new_status_all = None
                            new_status_all_default = channel_parameters["active"]

                            # Opcion Activar todos
                            if dict_values[k] == 1:
                                new_status_all = True

                            # Opcion Desactivar todos
                            if dict_values[k] == 2:
                                new_status_all = False

                            # Opcion Recuperar estado por defecto
                            if dict_values[k] == 3:
                                # Si tiene "enabled" en el _data.json es porque el estado no es el del channel.json
                                if config.get_setting("enabled", channel.channel):
                                    new_status_all = new_status_all_default

                                # Si el canal no tiene "enabled" en el _data.json no se guarda, se pasa al siguiente
                                else:
                                    continue

                            # Se guarda el estado del canal
                            if new_status_all is not None:
                                config.set_setting("enabled", new_status_all, channel.channel)
                    break
                else:
                    continue

            else:
                logger.info("Canal: %s | Estado: %s" % (k, dict_values[k]))
                config.set_setting("enabled", dict_values[k], k)
                logger.info("el valor esta como %s " % config.get_setting("enabled", k))

        platformtools.itemlist_update(Item(channel=CHANNELNAME, action="mainlist"))

    except:
        import traceback
        logger.error("Detalle del error: %s" % traceback.format_exc())
        platformtools.dialog_notification(config.get_localized_string(60579), config.get_localized_string(60580))


def overwrite_tools(item):
    import videolibrary_service
    from core import videolibrarytools

    seleccion = platformtools.dialog_yesno(config.get_localized_string(60581),
                                           config.get_localized_string(60582),
                                           config.get_localized_string(60583))
    if seleccion == 1:
        # tvshows
        heading = config.get_localized_string(60584)
        p_dialog = platformtools.dialog_progress_bg(config.get_localized_string(60585), heading)
        p_dialog.update(0, '')

        show_list = []
        for path, folders, files in filetools.walk(videolibrarytools.TVSHOWS_PATH):
            show_list.extend([filetools.join(path, f) for f in files if f == "tvshow.nfo"])

        if show_list:
            t = float(100) / len(show_list)

        for i, tvshow_file in enumerate(show_list):
            head_nfo, serie = videolibrarytools.read_nfo(tvshow_file)
            path = filetools.dirname(tvshow_file)

            if not serie.active:
                # si la serie no esta activa descartar
                continue

            # Eliminamos la carpeta con la serie ...
            filetools.rmdirtree(path)

            # ... y la volvemos a añadir
            videolibrary_service.update(path, p_dialog, i, t, serie, 3)
        p_dialog.close()

        # movies
        heading = config.get_localized_string(60586)
        p_dialog2 = platformtools.dialog_progress_bg(config.get_localized_string(60585), heading)
        p_dialog2.update(0, '')

        movies_list = []
        for path, folders, files in filetools.walk(videolibrarytools.MOVIES_PATH):
            movies_list.extend([filetools.join(path, f) for f in files if f.endswith(".json")])

        logger.debug("movies_list %s" % movies_list)

        if movies_list:
            t = float(100) / len(movies_list)

        for i, movie_json in enumerate(movies_list):
            try:
                from core import jsontools
                path = filetools.dirname(movie_json)
                movie = Item().fromjson(filetools.read(movie_json))

                # Eliminamos la carpeta con la pelicula ...
                filetools.rmdirtree(path)

                import math
                heading = config.get_localized_string(60587)

                p_dialog2.update(int(math.ceil((i + 1) * t)), heading, "%s: %s" % (movie.contentTitle,
                                                                                   movie.channel.capitalize()))
                # ... y la volvemos a añadir
                videolibrarytools.save_movie(movie)
            except Exception, ex:
                logger.error("Error al crear de nuevo la película")
                template = "An exception of type %s occured. Arguments:\n%r"
                message = template % (type(ex).__name__, ex.args)
                logger.error(message)

        p_dialog2.close()

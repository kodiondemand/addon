# -*- coding: utf-8 -*-

import os

from core import channeltools
from core import jsontools
from core.item import Item
from platformcode import config, logger
from platformcode import platformtools
from platformcode import launcher
from time import sleep
from platformcode.config import get_setting

__channel__ = "autoplay"

PLAYED = False

autoplay_node = {}


def context():
    '''
    Agrega la opcion Configurar AutoPlay al menu contextual

    :return:
    '''

    _context = ""

    if config.is_xbmc():
        _context = [{"title": config.get_localized_string(60071),
                     "action": "autoplay_config",
                     "channel": "autoplay"}]
    return _context


context = context()


def show_option(channel, itemlist, text_color='yellow', thumbnail=None, fanart=None):
    '''
    Agrega la opcion Configurar AutoPlay en la lista recibida

    :param channel: str
    :param itemlist: list (lista donde se desea integrar la opcion de configurar AutoPlay)
    :param text_color: str (color para el texto de la opcion Configurar Autoplay)
    :param thumbnail: str (direccion donde se encuentra el thumbnail para la opcion Configurar Autoplay)
    :return:
    '''
    from channelselector import get_thumb
    logger.info()

    if not config.is_xbmc():
        return itemlist

    if thumbnail == None:
        thumbnail = get_thumb('autoplay.png')
    if fanart == None:
        fanart = get_thumb('autoplay.png')

    plot_autoplay = config.get_localized_string(60399)
    itemlist.append(
        Item(channel=__channel__,
             title=config.get_localized_string(60071),
             action="autoplay_config",
             text_color=text_color,
             thumbnail=thumbnail,
             fanart=fanart,
             plot=plot_autoplay,
             from_channel=channel
             ))
    return itemlist


def start(itemlist, item):
    '''
    Metodo principal desde donde se reproduce automaticamente los enlaces
    - En caso la opcion de personalizar activa utilizara las opciones definidas por el usuario.
    - En caso contrario intentara reproducir cualquier enlace que cuente con el idioma preferido.

    :param itemlist: list (lista de items listos para reproducir, o sea con action='play')
    :param item: item (el item principal del canal)
    :return: intenta autoreproducir, en caso de fallar devuelve el itemlist que recibio en un principio
    '''
    logger.info()

    global PLAYED
    global autoplay_node
    PLAYED = False

    base_item = item

    if not config.is_xbmc():
        #platformtools.dialog_notification('AutoPlay ERROR', 'Sólo disponible para XBMC/Kodi')
        return itemlist


    if not autoplay_node:
        # Obtiene el nodo AUTOPLAY desde el json
        autoplay_node = jsontools.get_node_from_file('autoplay', 'AUTOPLAY')

    channel_id = item.channel
    if item.channel == 'videolibrary':
        autoplay_node = jsontools.get_node_from_file('autoplay', 'AUTOPLAY')
        channel_id = item.contentChannel
    try:
        active = autoplay_node['status']
    except:
        active = is_active(item.channel)

    if not channel_id in autoplay_node or not active:
        return itemlist

    # Agrega servidores y calidades que no estaban listados a autoplay_node
    new_options = check_value(channel_id, itemlist)

    # Obtiene el nodo del canal desde autoplay_node
    channel_node = autoplay_node.get(channel_id, {})
    # Obtiene los ajustes des autoplay para este canal
    settings_node = channel_node.get('settings', {})

    if get_setting('autoplay') or settings_node['active']:
        url_list_valid = []
        autoplay_list = []
        autoplay_b = []
        favorite_servers = []
        favorite_quality = []

        # Guarda el valor actual de "Accion y Player Mode" en preferencias
        user_config_setting_action = config.get_setting("default_action")
        user_config_setting_player = config.get_setting("player_mode")
        # Habilita la accion "Ver en calidad alta" (si el servidor devuelve más de una calidad p.e. gdrive)
        if user_config_setting_action != 2:
            config.set_setting("default_action", 2)
        if user_config_setting_player != 0:
            config.set_setting("player_mode", 0)

        # Informa que AutoPlay esta activo
        #platformtools.dialog_notification('AutoPlay Activo', '', sound=False)

        # Prioridades a la hora de ordenar itemlist:
        #       0: Servidores y calidades
        #       1: Calidades y servidores
        #       2: Solo servidores
        #       3: Solo calidades
        #       4: No ordenar
        if (settings_node['custom_servers'] and settings_node['custom_quality']):
            priority = settings_node['priority']  # 0: Servidores y calidades o 1: Calidades y servidores
        elif settings_node['custom_servers']:
            priority = 2  # Solo servidores
        elif settings_node['custom_quality']:
            priority = 3  # Solo calidades
        else:
            priority = 4  # No ordenar

        # Obtiene las listas servidores, calidades disponibles desde el nodo del json de AutoPlay
        server_list = channel_node.get('servers', [])
        for server in server_list:
            server = server.lower()
        quality_list = channel_node.get('quality', [])

        # Si no se definen calidades la se asigna default como calidad unica
        if len(quality_list) == 0:
            quality_list =['default']

        # Se guardan los textos de cada servidor y calidad en listas p.e. favorite_servers = ['verystream', 'openload',
        # 'streamcloud']
        for num in range(1, 4):
            favorite_servers.append(channel_node['servers'][settings_node['server_%s' % num]].lower())
            favorite_quality.append(channel_node['quality'][settings_node['quality_%s' % num]])

        # Se filtran los enlaces de itemlist y que se correspondan con los valores de autoplay
        for item in itemlist:
            autoplay_elem = dict()
            b_dict = dict()

            # Comprobamos q se trata de un item de video
            if 'server' not in item:
                continue

            # Agrega la opcion configurar AutoPlay al menu contextual
            if 'context' not in item:
                item.context = list()
            if not filter(lambda x: x['action'] == 'autoplay_config', context):
                item.context.append({"title": config.get_localized_string(60071),
                                     "action": "autoplay_config",
                                     "channel": "autoplay",
                                     "from_channel": channel_id})

            # Si no tiene calidad definida le asigna calidad 'default'
            if item.quality == '':
                item.quality = 'default'

            # Se crea la lista para configuracion personalizada
            if priority < 2:  # 0: Servidores y calidades o 1: Calidades y servidores

                # si el servidor y la calidad no se encuentran en las listas de favoritos o la url esta repetida,
                # descartamos el item
                if item.server.lower() not in favorite_servers or item.quality not in favorite_quality \
                        or item.url in url_list_valid:
                    item.type_b = True
                    b_dict['videoitem']= item
                    autoplay_b.append(b_dict)
                    continue
                autoplay_elem["indice_server"] = favorite_servers.index(item.server.lower())
                autoplay_elem["indice_quality"] = favorite_quality.index(item.quality)

            elif priority == 2:  # Solo servidores

                # si el servidor no se encuentra en la lista de favoritos o la url esta repetida,
                # descartamos el item
                if item.server.lower() not in favorite_servers or item.url in url_list_valid:
                    item.type_b = True
                    b_dict['videoitem'] = item
                    autoplay_b.append(b_dict)
                    continue
                autoplay_elem["indice_server"] = favorite_servers.index(item.server.lower())

            elif priority == 3:  # Solo calidades

                # si la calidad no se encuentra en la lista de favoritos o la url esta repetida,
                # descartamos el item
                if item.quality not in favorite_quality or item.url in url_list_valid:
                    item.type_b = True
                    b_dict['videoitem'] = item
                    autoplay_b.append(b_dict)
                    continue
                autoplay_elem["indice_quality"] = favorite_quality.index(item.quality)

            else:  # No ordenar

                # si la url esta repetida, descartamos el item
                if item.url in url_list_valid:
                    continue

            # Si el item llega hasta aqui lo añadimos al listado de urls validas y a autoplay_list
            url_list_valid.append(item.url)
            item.plan_b=True
            autoplay_elem['videoitem'] = item
            # autoplay_elem['server'] = item.server
            # autoplay_elem['quality'] = item.quality
            autoplay_list.append(autoplay_elem)

        # Ordenamos segun la prioridad
        if priority == 0:  # Servidores y calidades
            autoplay_list.sort(key=lambda orden: (orden['indice_server'], orden['indice_quality']))

        elif priority == 1:  # Calidades y servidores
            autoplay_list.sort(key=lambda orden: (orden['indice_quality'], orden['indice_server']))

        elif priority == 2:  # Solo servidores
            autoplay_list.sort(key=lambda orden: orden['indice_server'])

        elif priority == 3:  # Solo calidades
            autoplay_list.sort(key=lambda orden: orden['indice_quality'])

        # Se prepara el plan b, en caso de estar activo se agregan los elementos no favoritos al final
        try:
            plan_b = settings_node['plan_b']
        except:
            plan_b = True
        text_b = ''
        if plan_b:
            autoplay_list.extend(autoplay_b)
        # Si hay elementos en la lista de autoplay se intenta reproducir cada elemento, hasta encontrar uno
        # funcional o fallen todos

        if autoplay_list or (plan_b and autoplay_b):

            #played = False
            max_intentos = 5
            max_intentos_servers = {}

            # Si se esta reproduciendo algo detiene la reproduccion
            if platformtools.is_playing():
                platformtools.stop_video()

            for autoplay_elem in autoplay_list:
                play_item = Item

                # Si no es un elemento favorito si agrega el texto plan b
                if autoplay_elem['videoitem'].type_b:
                    text_b = '(Plan B)'
                if not platformtools.is_playing() and not PLAYED:
                    videoitem = autoplay_elem['videoitem']
                    if videoitem.server.lower() not in max_intentos_servers:
                        max_intentos_servers[videoitem.server.lower()] = max_intentos

                    # Si se han alcanzado el numero maximo de intentos de este servidor saltamos al siguiente
                    if max_intentos_servers[videoitem.server.lower()] == 0:
                        continue

                    lang = " "
                    if hasattr(videoitem, 'language') and videoitem.language != "":
                        lang = " '%s' " % videoitem.language

                    platformtools.dialog_notification("AutoPlay %s" %text_b, "%s%s%s" % (
                        videoitem.server.upper(), lang, videoitem.quality.upper()), sound=False)
                    # TODO videoitem.server es el id del server, pero podria no ser el nombre!!!

                    # Intenta reproducir los enlaces
                    # Si el canal tiene metodo play propio lo utiliza
                    channel = __import__('channels.%s' % channel_id, None, None, ["channels.%s" % channel_id])
                    if hasattr(channel, 'play'):
                        resolved_item = getattr(channel, 'play')(videoitem)
                        if len(resolved_item) > 0:
                            if isinstance(resolved_item[0], list):
                                videoitem.video_urls = resolved_item
                            else:
                                videoitem = resolved_item[0]

                    # Si no directamente reproduce y marca como visto

                    # Verifica si el item viene de la videoteca
                    try:
                        if base_item.contentChannel =='videolibrary':
                            # Marca como visto
                            from platformcode import xbmc_videolibrary
                            xbmc_videolibrary.mark_auto_as_watched(base_item)
                            # Rellena el video con los datos del item principal y reproduce
                            play_item = base_item.clone(url=videoitem)
                            platformtools.play_video(play_item.url, autoplay=True)
                        else:
                            # Si no viene de la videoteca solo reproduce
                            platformtools.play_video(videoitem, autoplay=True)
                    except:
                        pass
                    sleep(3)
                    try:
                        if platformtools.is_playing():
                            PLAYED = True
                            break
                    except:
                        logger.debug(str(len(autoplay_list)))

                    # Si hemos llegado hasta aqui es por q no se ha podido reproducir
                    max_intentos_servers[videoitem.server.lower()] -= 1

                    # Si se han alcanzado el numero maximo de intentos de este servidor
                    # preguntar si queremos seguir probando o lo ignoramos
                    if max_intentos_servers[videoitem.server.lower()] == 0:
                        text = config.get_localized_string(60072) % videoitem.server.upper()
                        if not platformtools.dialog_yesno("AutoPlay", text,
                                                          config.get_localized_string(60073)):
                            max_intentos_servers[videoitem.server.lower()] = max_intentos

                    # Si no quedan elementos en la lista se informa
                    if autoplay_elem == autoplay_list[-1]:
                         platformtools.dialog_notification('AutoPlay', config.get_localized_string(60072))

        else:
            platformtools.dialog_notification(config.get_localized_string(60074), config.get_localized_string(60075))
        if new_options:
            platformtools.dialog_notification("AutoPlay", config.get_localized_string(60076), sound=False)

        # Restaura si es necesario el valor previo de "Accion y Player Mode" en preferencias
        if user_config_setting_action != 2:
            config.set_setting("default_action", user_config_setting_action)
        if user_config_setting_player != 0:
            config.set_setting("player_mode", user_config_setting_player)

    return itemlist


def init(channel, list_servers, list_quality, reset=False):
    '''
    Comprueba la existencia de canal en el archivo de configuracion de Autoplay y si no existe lo añade.
    Es necesario llamar a esta funcion al entrar a cualquier canal que incluya la funcion Autoplay.

    :param channel: (str) id del canal
    :param list_servers: (list) lista inicial de servidores validos para el canal. No es necesario incluirlos todos,
        ya que la lista de servidores validos se ira actualizando dinamicamente.
    :param list_quality: (list) lista inicial de calidades validas para el canal. No es necesario incluirlas todas,
        ya que la lista de calidades validas se ira actualizando dinamicamente.
    :return: (bool) True si la inicializacion ha sido correcta.
    '''
    logger.info()
    change = False
    result = True


    if not config.is_xbmc():
        # platformtools.dialog_notification('AutoPlay ERROR', 'Sólo disponible para XBMC/Kodi')
        result = False
    else:
        autoplay_path = os.path.join(config.get_data_path(), "settings_channels", 'autoplay_data.json')
        if os.path.exists(autoplay_path):
            autoplay_node = jsontools.get_node_from_file('autoplay', "AUTOPLAY")
        else:
            change = True
            autoplay_node = {"AUTOPLAY": {}}

        if channel not in autoplay_node or reset:
            change = True

            # Se comprueba que no haya calidades ni servidores duplicados
            if 'default' not in list_quality:
                list_quality.append('default')
            # list_servers = list(set(list_servers))
            # list_quality = list(set(list_quality))

            # Creamos el nodo del canal y lo añadimos
            channel_node = {"servers": list_servers,
                            "quality": list_quality,
                            "settings": {
                                "active": False,
                                "plan_b": True,
                                "custom_servers": False,
                                "custom_quality": False,
                                "priority": 0}}
            for n in range(1, 4):
                s = c = 0
                if len(list_servers) >= n:
                    s = n - 1
                if len(list_quality) >= n:
                    c = n - 1

                channel_node["settings"]["server_%s" % n] = s
                channel_node["settings"]["quality_%s" % n] = c
            autoplay_node[channel] = channel_node

        if change:
            result, json_data = jsontools.update_node(autoplay_node, 'autoplay', 'AUTOPLAY')

            if not result:
                heading = config.get_localized_string(60077)
                msj = config.get_localized_string(60078)
                icon = 1

                platformtools.dialog_notification(heading, msj, icon, sound=False)

    return result


def check_value(channel, itemlist):
    ''' comprueba la existencia de un valor en la lista de servidores o calidades
        si no existiera los agrega a la lista en el json

    :param channel: str
    :param values: list (una de servidores o calidades)
    :param value_type: str (server o quality)
    :return: list
    '''
    logger.info()
    global autoplay_node
    change = False

    if not autoplay_node:
        # Obtiene el nodo AUTOPLAY desde el json
        autoplay_node = jsontools.get_node_from_file('autoplay', 'AUTOPLAY')

    channel_node = autoplay_node.get(channel)

    server_list = channel_node.get('servers')
    if not server_list:
        server_list = channel_node['servers'] = list()

    quality_list = channel_node.get('quality')
    if not quality_list:
        quality_list = channel_node['quality'] = list()

    for item in itemlist:
        if item.server.lower() not in server_list and item.server !='':
            server_list.append(item.server.lower())
            change = True
        if item.quality not in quality_list and item.quality !='':
            quality_list.append(item.quality)
            change = True

    if change:
        change, json_data = jsontools.update_node(autoplay_node, 'autoplay', 'AUTOPLAY')

    return change


def autoplay_config(item):
    logger.info()
    global autoplay_node
    dict_values = {}
    list_controls = []
    channel_parameters = channeltools.get_channel_parameters(item.from_channel)
    channel_name = channel_parameters['title']

    if not autoplay_node:
        # Obtiene el nodo AUTOPLAY desde el json
        autoplay_node = jsontools.get_node_from_file('autoplay', 'AUTOPLAY')

    channel_node = autoplay_node.get(item.from_channel, {})
    settings_node = channel_node.get('settings', {})

    allow_option = True

    active_settings = {"id": "active", "label": config.get_localized_string(60079),
                       "color": "0xffffff99", "type": "bool", "default": False, "enabled": allow_option,
                       "visible": allow_option}
    list_controls.append(active_settings)
    dict_values['active'] = settings_node.get('active', False)

    # Idioma
    status_language = config.get_setting("filter_languages", item.from_channel)
    if not status_language:
        status_language = 0

    set_language = {"id": "language", "label": config.get_localized_string(60080), "color": "0xffffff99",
                    "type": "list", "default": 0, "enabled": "eq(-1,true)", "visible": True,
                    "lvalues": get_languages(item.from_channel)}

    list_controls.append(set_language)
    dict_values['language'] = status_language

    separador = {"id": "label", "label": "         "
                                         "_________________________________________________________________________________________",
                 "type": "label", "enabled": True, "visible": True}
    list_controls.append(separador)

    # Seccion servidores favoritos
    server_list = channel_node.get("servers", [])
    if not server_list:
        enabled = False
        server_list = ["No disponible"]
    else:
        enabled = "eq(-3,true)"

    custom_servers_settings = {"id": "custom_servers", "label": config.get_localized_string(60081), "color": "0xff66ffcc",
                               "type": "bool", "default": False, "enabled": enabled, "visible": True}
    list_controls.append(custom_servers_settings)
    if dict_values['active'] and enabled:
        dict_values['custom_servers'] = settings_node.get('custom_servers', False)
    else:
        dict_values['custom_servers'] = False

    for num in range(1, 4):
        pos1 = num + 3
        default = num - 1
        if default > len(server_list) - 1:
            default = 0
        set_servers = {"id": "server_%s" % num, "label": u"          \u2665" + config.get_localized_string(60082) % num,
                       "color": "0xfffcab14", "type": "list", "default": default,
                       "enabled": "eq(-%s,true)+eq(-%s,true)" % (pos1, num), "visible": True,
                       "lvalues": server_list}
        list_controls.append(set_servers)

        dict_values["server_%s" % num] = settings_node.get("server_%s" % num, 0)
        if settings_node.get("server_%s" % num, 0) > len(server_list) - 1:
            dict_values["server_%s" % num] = 0

    # Seccion Calidades favoritas
    quality_list = channel_node.get("quality", [])
    if not quality_list:
        enabled = False
        quality_list = ["No disponible"]
    else:
        enabled = "eq(-7,true)"

    custom_quality_settings = {"id": "custom_quality", "label": config.get_localized_string(60083), "color": "0xff66ffcc",
                               "type": "bool", "default": False, "enabled": enabled, "visible": True}
    list_controls.append(custom_quality_settings)
    if dict_values['active'] and enabled:
        dict_values['custom_quality'] = settings_node.get('custom_quality', False)
    else:
        dict_values['custom_quality'] = False

    for num in range(1, 4):
        pos1 = num + 7
        default = num - 1
        if default > len(quality_list) - 1:
            default = 0

        set_quality = {"id": "quality_%s" % num, "label": u"          \u2665 Calidad Favorita %s" % num,
                       "color": "0xfff442d9", "type": "list", "default": default,
                       "enabled": "eq(-%s,true)+eq(-%s,true)" % (pos1, num), "visible": True,
                       "lvalues": quality_list}
        list_controls.append(set_quality)
        dict_values["quality_%s" % num] = settings_node.get("quality_%s" % num, 0)
        if settings_node.get("quality_%s" % num, 0) > len(quality_list) - 1:
            dict_values["quality_%s" % num] = 0

    # Plan B
    dict_values['plan_b'] = settings_node.get('plan_b', False)
    enabled = "eq(-4,true)|eq(-8,true)"
    plan_b = {"id": "plan_b", "label": config.get_localized_string(70172),
                       "color": "0xffffff99",
                               "type": "bool", "default": False, "enabled": enabled, "visible": True}
    list_controls.append(plan_b)


    # Seccion Prioridades
    priority_list = [config.get_localized_string(70174), config.get_localized_string(70175)]
    set_priority = {"id": "priority", "label": config.get_localized_string(60085),
                    "color": "0xffffff99", "type": "list", "default": 0,
                    "enabled": True, "visible": "eq(-5,true)+eq(-9,true)+eq(-12,true)", "lvalues": priority_list}
    list_controls.append(set_priority)
    dict_values["priority"] = settings_node.get("priority", 0)



    # Abrir cuadro de dialogo
    platformtools.show_channel_settings(list_controls=list_controls, dict_values=dict_values, callback='save',
                                        item=item, caption='%s - AutoPlay' % channel_name,
                                        custom_button={'visible': True,
                                                       'function': "reset",
                                                        'close': True,
                                                        'label': 'Reset'})


def save(item, dict_data_saved):
    '''
    Guarda los datos de la ventana de configuracion

    :param item: item
    :param dict_data_saved: dict
    :return:
    '''
    logger.info()
    global autoplay_node

    if not autoplay_node:
        # Obtiene el nodo AUTOPLAY desde el json
        autoplay_node = jsontools.get_node_from_file('autoplay', 'AUTOPLAY')

    new_config = dict_data_saved
    if not new_config['active']:
        new_config['language']=0
    channel_node = autoplay_node.get(item.from_channel)
    config.set_setting("filter_languages", dict_data_saved.pop("language"), item.from_channel)
    channel_node['settings'] = dict_data_saved

    result, json_data = jsontools.update_node(autoplay_node, 'autoplay', 'AUTOPLAY')


    return result


def get_languages(channel):
    '''
    Obtiene los idiomas desde el json del canal

    :param channel: str
    :return: list
    '''
    logger.info()
    list_language = ['No filtrar']
    list_controls, dict_settings = channeltools.get_channel_controls_settings(channel)
    for control in list_controls:
        try:
            if control["id"] == 'filter_languages':
                list_language = control["lvalues"]
        except:
            pass

    return list_language


def is_active(channel):
    '''
    Devuelve un booleano q indica si esta activo o no autoplay en el canal desde el que se llama

    :return: True si esta activo autoplay para el canal desde el que se llama, False en caso contrario.
    '''
    logger.info()
    global autoplay_node

    if not config.is_xbmc():
        return False

    if not autoplay_node:
        # Obtiene el nodo AUTOPLAY desde el json
        autoplay_node = jsontools.get_node_from_file('autoplay', 'AUTOPLAY')

        # Obtine el canal desde el q se hace la llamada
        #import inspect
        #module = inspect.getmodule(inspect.currentframe().f_back)
        #canal = module.__name__.split('.')[1]
    canal = channel

    # Obtiene el nodo del canal desde autoplay_node
    channel_node = autoplay_node.get(canal, {})
    # Obtiene los ajustes des autoplay para este canal
    settings_node = channel_node.get('settings', {})

    return settings_node.get('active', False) or get_setting('autoplay')


def reset(item, dict):

    channel_name = item.from_channel
    channel = __import__('channels.%s' % channel_name, fromlist=["channels.%s" % channel_name])
    list_servers = channel.list_servers
    list_quality = channel.list_quality

    init(channel_name, list_servers, list_quality, reset=True)
    platformtools.dialog_notification('AutoPlay', config.get_localized_string(70523) % item.category)

    return

def set_status(status):
    logger.info()
    # Obtiene el nodo AUTOPLAY desde el json
    autoplay_node = jsontools.get_node_from_file('autoplay', 'AUTOPLAY')
    autoplay_node['status'] = status

    result, json_data = jsontools.update_node(autoplay_node, 'autoplay', 'AUTOPLAY')

def play_multi_channel(item, itemlist):
    logger.info()
    global PLAYED
    actual_channel = ''
    channel_videos = []
    video_dict = dict()
    set_status(True)

    for video_item in itemlist:
        if video_item.contentChannel != actual_channel:
            actual_channel = video_item.contentChannel
        elif is_active(actual_channel):
            channel_videos.append(video_item)
            video_dict[actual_channel] = channel_videos

    for channel, videos in video_dict.items():
        item.contentChannel = channel
        if not PLAYED:
            start(videos, item)
        else:
            break

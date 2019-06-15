# -*- coding: utf-8 -*-

import glob
import os
import re
import time
from threading import Thread

import xbmcaddon

from channelselector import get_thumb, auto_filter
from core import channeltools
from core import scrapertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from platformcode import platformtools

addon = xbmcaddon.Addon('metadata.themoviedb.org')
def_lang = addon.getSetting('language')

link_list = []
max_links = 30


def mainlist(item):
    logger.info()
    item.channel = "search"

    itemlist = []
    context = [{"title": config.get_localized_string(60412), "action": "setting_channel", "channel": item.channel}]
    itemlist.append(Item(channel=item.channel, action="sub_menu", title="[B]" + config.get_localized_string(70305)+ "[/B]", context=context,
                         thumbnail=get_thumb("search.png")))
    itemlist.append(Item(channel="filmontv", action="mainlist", title=config.get_localized_string(50001),
                         thumbnail=get_thumb("on_the_air.png"), viewmode="thumbnails"))  
    itemlist.append(Item(channel=item.channel, action='genres_menu', title=config.get_localized_string(70306), type='movie',
                         thumbnail=get_thumb("genres.png")))
    itemlist.append (Item(channel=item.channel, action='discover_list', title=config.get_localized_string(70307),
                          context=context, search_type='list', list_type='movie/popular',
                          thumbnail=get_thumb("popular.png")))
    itemlist.append(Item(channel=item.channel, action='discover_list', title=config.get_localized_string(70308),
                         context=context, search_type='list', list_type='movie/top_rated',
                         thumbnail=get_thumb("top_rated.png")))
    #itemlist.append(Item(channel=item.channel, action='discover_list', title=config.get_localized_string(70309), context=context,
    #         search_type='list', list_type='movie/now_playing',
    #                     thumbnail=get_thumb("now_playing.png")))
    itemlist.append(Item(channel=item.channel, action='genres_menu', title=config.get_localized_string(70310), type='tv',
                         thumbnail=get_thumb("genres.png")))
    itemlist.append(
        Item(channel=item.channel, action='discover_list', title=config.get_localized_string(70311), context=context,
             search_type='list',list_type='tv/popular', thumbnail=get_thumb("popular.png")))
    #itemlist.append(Item(channel=item.channel, action='discover_list', title=config.get_localized_string(70312), context=context,
    #                     search_type='list', list_type='tv/on_the_air', thumbnail=get_thumb("on_the_air.png")))
    itemlist.append(Item(channel=item.channel, action='discover_list', title=config.get_localized_string(70313), context=context,
                         search_type='list', list_type='tv/top_rated', thumbnail=get_thumb("top_rated.png")))


    return itemlist


def genres_menu(item):

    itemlist = []

    genres = tmdb.get_genres(item.type)

    logger.debug(genres)
    logger.debug(genres[item.type])

    for key, value in genres[item.type].items():
        itemlist.append(item.clone(title=value, action='discover_list', search_type='discover',
                                   list_type=key, page='1'))
    return sorted(itemlist, key=lambda it: it.title)

def sub_menu(item):
    logger.info()
    item.channel = "search"

    itemlist = list()
    context = [{"title": config.get_localized_string(70273),
                "action": "setting_channel",
                "channel": item.channel}]
    itemlist.append(Item(channel=item.channel, action="search",
                         title=config.get_localized_string(30980), context=context,
                         thumbnail=get_thumb("search.png")))

    thumbnail = get_thumb("search_star.png")

    itemlist.append(Item(channel='tvmoviedb', title=config.get_localized_string(70036), action="search_",
                         search={'url': 'search/person', 'language': def_lang, 'page': 1}, star=True,
                         thumbnail=thumbnail))

    itemlist.append(Item(channel=item.channel, action="search",
                         title=config.get_localized_string(59998), extra="categorias",
                         context=context,
                         thumbnail=get_thumb("search.png")))
    itemlist.append(Item(channel=item.channel, action="opciones", title=config.get_localized_string(59997),
                         thumbnail=get_thumb("search.png")))

    itemlist.append(Item(channel="tvmoviedb", action="mainlist", title=config.get_localized_string(70274),
                         thumbnail=get_thumb("search.png")))

    saved_searches_list = get_saved_searches()
    context2 = context[:]
    context2.append({"title": config.get_localized_string(59996),
                     "action": "clear_saved_searches",
                     "channel": item.channel})
    logger.info("saved_searches_list=%s" % saved_searches_list)

    if saved_searches_list:
        itemlist.append(Item(channel=item.channel, action="",
                             title=config.get_localized_string(59995), context=context2,
                             thumbnail=get_thumb("search.png")))
        for saved_search_text in saved_searches_list:
            itemlist.append(Item(channel=item.channel, action="do_search",
                                 title='    "' + saved_search_text + '"',
                                 extra=saved_search_text, context=context2,
                                 category=saved_search_text,
                                 thumbnail=get_thumb("search.png")))

    return itemlist


def opciones(item):
    itemlist = list()
    itemlist.append(Item(channel=item.channel, action="setting_channel",
                         title=config.get_localized_string(59994), folder=False,
                         thumbnail=get_thumb("search.png")))
    itemlist.append(Item(channel=item.channel, action="clear_saved_searches", title=config.get_localized_string(59996),
                         folder=False, thumbnail=get_thumb("search.png")))
    itemlist.append(Item(channel=item.channel, action="settings", title=config.get_localized_string(60531), folder=False,
                         thumbnail=get_thumb("search.png")))
    return itemlist


def settings(item):
    return platformtools.show_channel_settings(caption=config.get_localized_string(59993))


def setting_channel(item):
    if config.get_platform(True)['num_version'] >= 17.0: # A partir de Kodi 16 se puede usar multiselect, y de 17 con preselect
        return setting_channel_new(item)
    else:
        return setting_channel_old(item)

def setting_channel_new(item):
    import channelselector, xbmcgui
    from core import channeltools

    # Cargar lista de opciones (canales activos del usuario y que permitan búsqueda global)
    # ------------------------
    lista = []; ids = []; lista_lang = []; lista_ctgs = []
    channels_list = channelselector.filterchannels('all')
    for channel in channels_list:
        channel_parameters = channeltools.get_channel_parameters(channel.channel)

        # No incluir si en la configuracion del canal no existe "include_in_global_search"
        if not channel_parameters['include_in_global_search']:
            continue

        lbl = '%s' % channel_parameters['language']
        lbl += ' %s' % ', '.join(config.get_localized_category(categ) for categ in channel_parameters['categories'])

        it = xbmcgui.ListItem(channel.title, lbl)
        it.setArt({ 'thumb': channel.thumbnail, 'fanart': channel.fanart })
        lista.append(it)
        ids.append(channel.channel)
        lista_lang.append(channel_parameters['language'])
        lista_ctgs.append(channel_parameters['categories'])

    # Diálogo para pre-seleccionar
    # ----------------------------
    preselecciones = [
        config.get_localized_string(70570), 
        config.get_localized_string(70571), 
        config.get_localized_string(70572), 
        config.get_localized_string(70573), 
        # config.get_localized_string(70574), 
        # config.get_localized_string(70575),
        config.get_localized_string(70576)
    ]
    presel_values = ['skip', 'actual', 'all', 'none', 'cast', 'lat', 'ita']

    categs = ['movie', 'tvshow', 'documentary', 'anime', 'vos', 'direct', 'torrent']
    if config.get_setting('adult_mode') > 0: categs.append('adult')
    for c in categs:
        preselecciones.append(config.get_localized_string(70577) + config.get_localized_category(c))
        presel_values.append(c)

    if item.action == 'setting_channel': # Configuración de los canales incluídos en la búsqueda
        del preselecciones[0]
        del presel_values[0]
    #else: # Llamada desde "buscar en otros canales" (se puede saltar la selección e ir directo a la búsqueda)
    
    ret = platformtools.dialog_select(config.get_localized_string(59994), preselecciones)
    if ret == -1: return False # pedido cancel
    if presel_values[ret] == 'skip': return True # continuar sin modificar
    elif presel_values[ret] == 'none': preselect = []
    elif presel_values[ret] == 'all': preselect = range(len(ids))
    elif presel_values[ret] in ['cast', 'lat']:
        preselect = []
        for i, lg in enumerate(lista_lang):
            if presel_values[ret] in lg or '*' in lg:
                preselect.append(i)
    elif presel_values[ret] in ['ita']:
        preselect = []
        for i, lg in enumerate(lista_lang):
            if presel_values[ret] in lg or '*' in lg:
                preselect.append(i)
    elif presel_values[ret] == 'actual':
        preselect = []
        for i, canal in enumerate(ids):
            channel_status = config.get_setting('include_in_global_search', canal)
            if channel_status:
                preselect.append(i)
    else:
        preselect = []
        for i, ctgs in enumerate(lista_ctgs):
            if presel_values[ret] in ctgs:
                preselect.append(i)

    # Diálogo para seleccionar
    # ------------------------
    ret = xbmcgui.Dialog().multiselect(config.get_localized_string(59994), lista, preselect=preselect, useDetails=True)
    if ret == None: return False # pedido cancel
    seleccionados = [ids[i] for i in ret]

    # Guardar cambios en canales para la búsqueda
    # -------------------------------------------
    for canal in ids:
        channel_status = config.get_setting('include_in_global_search', canal)
        if channel_status is None: channel_status = True

        if channel_status and canal not in seleccionados:
            config.set_setting('include_in_global_search', False, canal)
        elif not channel_status and canal in seleccionados:
            config.set_setting('include_in_global_search', True, canal)

    return True

def setting_channel_old(item):
    channels_path = os.path.join(config.get_runtime_path(), "channels", '*.json')
    # channel_language = config.get_setting("channel_language", default="all")
    channel_language = auto_filter()

    list_controls = []
    for infile in sorted(glob.glob(channels_path)):
        channel_name = os.path.basename(infile)[:-5]
        channel_parameters = channeltools.get_channel_parameters(channel_name)

        # No incluir si es un canal inactivo
        if not channel_parameters["active"]:
            continue

        # No incluir si es un canal para adultos, y el modo adulto está desactivado
        if channel_parameters["adult"] and config.get_setting("adult_mode") == 0:
            continue

        # No incluir si el canal es en un idioma filtrado
        if channel_language != "all" and channel_language not in channel_parameters["language"] \
                and "*" not in channel_parameters["language"]:
            continue

        # No incluir si en la configuracion del canal no existe "include_in_global_search"
        include_in_global_search = channel_parameters["include_in_global_search"]

        if not include_in_global_search:
            continue
        else:
            # Se busca en la configuración del canal el valor guardado
            include_in_global_search = config.get_setting("include_in_global_search", channel_name)

        control = {'id': channel_name,
                   'type': "bool",
                   'label': channel_parameters["title"],
                   'default': include_in_global_search,
                   'enabled': True,
                   'visible': True}

        list_controls.append(control)

    if config.get_setting("custom_button_value", item.channel):
        custom_button_label = config.get_localized_string(59992)
    else:
        custom_button_label = config.get_localized_string(59991)

    return platformtools.show_channel_settings(list_controls=list_controls,
                                               caption=config.get_localized_string(59990),
                                               callback="save_settings", item=item,
                                               custom_button={'visible': True,
                                                              'function': "cb_custom_button",
                                                              'close': False,
                                                              'label': custom_button_label})


def save_settings(item, dict_values):
    progreso = platformtools.dialog_progress(config.get_localized_string(59988), config.get_localized_string(59989))
    n = len(dict_values)
    for i, v in enumerate(dict_values):
        progreso.update((i * 100) / n, config.get_localized_string(59988))
        config.set_setting("include_in_global_search", dict_values[v], v)

    progreso.close()
    return True


def cb_custom_button(item, dict_values):
    value = config.get_setting("custom_button_value", item.channel)
    if value == "":
        value = False

    for v in dict_values.keys():
        dict_values[v] = not value

    if config.set_setting("custom_button_value", not value, item.channel) == True:
        return {"label": config.get_localized_string(59992)}
    else:
        return {"label": config.get_localized_string(59991)}


def searchbycat(item):
    # Only in xbmc/kodi
    # Abre un cuadro de dialogo con las categorías en las que hacer la búsqueda

    categories = [config.get_localized_string(30122), config.get_localized_string(30123), config.get_localized_string(30124), config.get_localized_string(30125), config.get_localized_string(59975), config.get_localized_string(59976)]
    categories_id = ["movie", "tvshow", "anime", "documentary", "vos", "latino"]
    list_controls = []
    for i, category in enumerate(categories):
        control = {'id': categories_id[i],
                   'type': "bool",
                   'label': category,
                   'default': False,
                   'enabled': True,
                   'visible': True}

        list_controls.append(control)
    control = {'id': "separador",
               'type': "label",
               'label': '',
               'default': "",
               'enabled': True,
               'visible': True}
    list_controls.append(control)
    control = {'id': "torrent",
               'type': "bool",
               'label': config.get_localized_string(70275),
               'default': True,
               'enabled': True,
               'visible': True}
    list_controls.append(control)

    return platformtools.show_channel_settings(list_controls=list_controls, caption=config.get_localized_string(59974),
                                               callback="search_cb", item=item)


def search_cb(item, values=""):
    cat = []
    for c in values:
        if values[c]:
            cat.append(c)

    if not len(cat):
        return None
    else:
        logger.info(item.tostring())
        logger.info(str(cat))
        return do_search(item, cat)


# Al llamar a esta función, el sistema pedirá primero el texto a buscar
# y lo pasará en el parámetro "tecleado"
def search(item, tecleado):
    logger.info()
    tecleado = tecleado.replace("+", " ")
    item.category = tecleado

    if tecleado != "":
        save_search(tecleado)

    if item.extra == "categorias":
        item.extra = tecleado
        itemlist = searchbycat(item)
    else:
        item.extra = tecleado
        itemlist = do_search(item, [])

    return itemlist


def show_result(item):
    tecleado = None
    if item.adult and config.get_setting("adult_request_password"):
        # Solicitar contraseña
        tecleado = platformtools.dialog_input("", config.get_localized_string(60334), True)
        if tecleado is None or tecleado != config.get_setting("adult_password"):
            return []

    item.channel = item.__dict__.pop('from_channel')
    item.action = item.__dict__.pop('from_action')
    if item.__dict__.has_key('tecleado'):
        tecleado = item.__dict__.pop('tecleado')

    try:
        channel = __import__('channels.%s' % item.channel, fromlist=["channels.%s" % item.channel])
    except:
        import traceback
        logger.error(traceback.format_exc())
        return []

    if tecleado:
        # Mostrar resultados: agrupados por canales
        return channel.search(item, tecleado)
    else:
        # Mostrar resultados: todos juntos
        if item.infoPlus:                       #Si viene de una ventana de InfoPlus, hay que salir de esta forma...
            del item.infoPlus                   #si no, se mete en un bucle mostrando la misma pantalla, 
            item.title = item.title.strip()     #dando error en "handle -1"
            return getattr(channel, item.action)(item)
        try:
            from platformcode import launcher
            launcher.run(item)
        except ImportError:
            return getattr(channel, item.action)(item)


def channel_search(search_results, channel_parameters, tecleado):
    try:
        exec("from channels import " + channel_parameters["channel"] + " as module")
        mainlist = module.mainlist(Item(channel=channel_parameters["channel"]))
        search_items = [item for item in mainlist if item.action == "search"]
        if not search_items:
            search_items = [Item(channel=channel_parameters["channel"], action="search")]

        for item in search_items:
            result = module.search(item.clone(), tecleado)
            if result is None:
                result = []
            if len(result):
                if not channel_parameters["title"].capitalize() in search_results:
                    search_results[channel_parameters["title"].capitalize()] = []
                search_results[channel_parameters["title"].capitalize()].append({"item": item,
                                                                    "itemlist": result,
                                                                    "adult": channel_parameters["adult"]})

    except:
        logger.error("No se puede buscar en: %s" % channel_parameters["title"])
        import traceback
        logger.error(traceback.format_exc())


# Esta es la función que realmente realiza la búsqueda
def do_search(item, categories=None):
    logger.info("blaa categorias %s" % categories)

    if item.contextual==True:
        categories = ["Películas"]
        setting_item = Item(channel=item.channel, title=config.get_localized_string(59994), folder=False,
                            thumbnail=get_thumb("search.png"))
        if not setting_channel(setting_item):
            return False

    if categories is None:
        categories = []

    multithread = config.get_setting("multithread", "search")
    result_mode = config.get_setting("result_mode", "search")

    if item.wanted!='':
        tecleado=item.wanted
    else:
        tecleado = item.extra

    itemlist = []

    channels_path = os.path.join(config.get_runtime_path(), "channels", '*.json')
    logger.info("channels_path=%s" % channels_path)

    # channel_language = config.get_setting("channel_language", default="all")
    channel_language = auto_filter()
    logger.info("channel_language=%s" % channel_language)

    # Para Kodi es necesario esperar antes de cargar el progreso, de lo contrario
    # el cuadro de progreso queda "detras" del cuadro "cargando..." y no se le puede dar a cancelar
    time.sleep(0.5)
    progreso = platformtools.dialog_progress(config.get_localized_string(30993) % tecleado, "")
    channel_files = sorted(glob.glob(channels_path), key=lambda x: os.path.basename(x))
    import math

    threads = []
    search_results = {}
    start_time = time.time()
    list_channels_search = []

    # Extrae solo los canales a buscar
    for index, infile in enumerate(channel_files):
        try:
            basename = os.path.basename(infile)
            basename_without_extension = basename[:-5]
            logger.info("%s..." % basename_without_extension)

            channel_parameters = channeltools.get_channel_parameters(basename_without_extension)

            # No busca si es un canal inactivo
            if not channel_parameters["active"]:
                logger.info("%s -no activo-" % basename_without_extension)
                continue

            # En caso de búsqueda por categorias
            if categories:

                # Si no se ha seleccionado torrent no se muestra
                #if "torrent" not in categories and "infoPlus" not in categories:
                #    if "torrent" in channel_parameters["categories"]:
                #        logger.info("%s -torrent-" % basename_without_extension)
                #        continue

                for cat in categories:
                    if cat not in channel_parameters["categories"]:
                        logger.info("%s -no en %s-" % (basename_without_extension, cat))
                        continue

            # No busca si es un canal para adultos, y el modo adulto está desactivado
            if channel_parameters["adult"] and config.get_setting("adult_mode") == 0:
                logger.info("%s -adulto-" % basename_without_extension)
                continue

            # No busca si el canal es en un idioma filtrado
            if channel_language != "all" and channel_language not in channel_parameters["language"] \
                    and "*" not in channel_parameters["language"]:
                logger.info("%s -idioma no válido-" % basename_without_extension)
                continue

            # No busca si es un canal excluido de la búsqueda global
            include_in_global_search = channel_parameters["include_in_global_search"]
            if include_in_global_search:
                # Buscar en la configuracion del canal
                include_in_global_search = config.get_setting("include_in_global_search", basename_without_extension)

            if not include_in_global_search:
                logger.info("%s -no incluido en lista a buscar-" % basename_without_extension)
                continue
            list_channels_search.append(infile)
        except:
            logger.error("No se puede buscar en: %s" % channel_parameters["title"])
            import traceback
            logger.error(traceback.format_exc())
            continue


    for index, infile in enumerate(list_channels_search):
        try:
           # fix float porque la division se hace mal en python 2.x
            percentage = int(float((index+1))/len(list_channels_search)*float(100))
            basename = os.path.basename(infile)
            basename_without_extension = basename[:-5]
            logger.info("%s..." % basename_without_extension)
            channel_parameters = channeltools.get_channel_parameters(basename_without_extension)
            # Movido aqui el progreso, para que muestre el canal exacto que está buscando
            progreso.update(percentage,
                            config.get_localized_string(60520) % (channel_parameters["title"]))
            # Modo Multi Thread
            if progreso.iscanceled():
                progreso.close()
                logger.info("Búsqueda cancelada")
                return itemlist
            if multithread:
                t = Thread(target=channel_search, args=[search_results, channel_parameters, tecleado],
                           name=channel_parameters["title"])
                t.setDaemon(True)
                t.start()
                threads.append(t)
            # Modo single Thread
            else:
                logger.info("Intentado búsqueda en %s de %s " % (basename_without_extension, tecleado))
                channel_search(search_results, channel_parameters, tecleado)
        except:
            logger.error("No se puede buscar en: %s" % channel_parameters["title"])
            import traceback
            logger.error(traceback.format_exc())
            continue

    # Modo Multi Thread
    # Usando isAlive() no es necesario try-except,
    # ya que esta funcion (a diferencia de is_alive())
    # es compatible tanto con versiones antiguas de python como nuevas
    if multithread:
        pendent = [a for a in threads if a.isAlive()]
        if len(pendent) > 0: t = float(100) / len(pendent)
        while len(pendent) > 0:
            index = (len(threads) - len(pendent)) + 1
            percentage = int(math.ceil(index * t))

            list_pendent_names = [a.getName() for a in pendent]
            mensaje = config.get_localized_string(70282) % (", ".join(list_pendent_names))
            progreso.update(percentage, config.get_localized_string(60521) % (len(threads) - len(pendent) + 1, len(threads)),
                            mensaje)
            if progreso.iscanceled():
                logger.info("Búsqueda cancelada")
                break
            time.sleep(0.5)
            pendent = [a for a in threads if a.isAlive()]
    total = 0
    for channel in sorted(search_results.keys()):
        for element in search_results[channel]:
            total += len(element["itemlist"])
            title = channel
            # resultados agrupados por canales
            if item.contextual == True or item.action == 'search_tmdb':
                result_mode = 1
            if result_mode == 0:
                if len(search_results[channel]) > 1:
                    title += " -%s" % element["item"].title.strip()
                title += " (%s)" % len(element["itemlist"])
                title = re.sub("\[COLOR [^\]]+\]", "", title)
                title = re.sub("\[/COLOR]", "", title)
                itemlist.append(Item(title=title, channel="search", action="show_result", url=element["item"].url,
                                     extra=element["item"].extra, folder=True, adult=element["adult"],
                                     from_action="search", from_channel=element["item"].channel, tecleado=tecleado))
            # todos los resultados juntos, en la misma lista
            else:
                title = config.get_localized_string(70697) % channel
                itemlist.append(Item(title=title, channel="search", action="",
                                     folder=False, text_bold=True, from_channel=channel))
                for i in element["itemlist"]:
                    if i.action:
                        title = "    " + i.title
                        if "infoPlus" in categories:            #Se manrca vi viene de una ventana de InfoPlus
                            i.infoPlus = True
                        itemlist.append(i.clone(title=title, from_action=i.action, from_channel=i.channel,
                                                channel="search", action="show_result", adult=element["adult"]))
    title = config.get_localized_string(59972) % (
    tecleado, total, time.time() - start_time)
    itemlist.insert(0, Item(title=title, text_color='yellow'))
    progreso.close()
    #Para opcion Buscar en otros canales
    if item.contextual == True:
        return exact_results(itemlist, tecleado)
    else:
        return itemlist


def exact_results(results, wanted):
    logger.info()
    itemlist =[]

    for item in results:
        if item.action=='':
            channel=item.from_channel
        if item.action != '' and item.contentTitle==wanted:
            item.title = '%s [%s]' % (item.title, channel)
            itemlist.append(item)

    return itemlist


def save_search(text):
    saved_searches_limit = int((10, 20, 30, 40,)[int(config.get_setting("saved_searches_limit", "search"))])

    current_saved_searches_list = config.get_setting("saved_searches_list", "search")
    if current_saved_searches_list is None:
        saved_searches_list = []
    else:
        saved_searches_list = list(current_saved_searches_list)

    if text in saved_searches_list:
        saved_searches_list.remove(text)

    saved_searches_list.insert(0, text)

    config.set_setting("saved_searches_list", saved_searches_list[:saved_searches_limit], "search")


def clear_saved_searches(item):
    config.set_setting("saved_searches_list", list(), "search")
    platformtools.dialog_ok(config.get_localized_string(60329), config.get_localized_string(60424))


def get_saved_searches():
    current_saved_searches_list = config.get_setting("saved_searches_list", "search")
    if current_saved_searches_list is None:
        saved_searches_list = []
    else:
        saved_searches_list = list(current_saved_searches_list)

    return saved_searches_list


def discover_list(item):
    from platformcode import unify
    itemlist = []

    result = tmdb.discovery(item)

    tvshow = False

    logger.debug(item)

    for elem in result:
        elem['tmdb_id']=elem['id']
        if 'title' in elem:
            title = unify.normalize(elem['title']).capitalize()
            elem['year'] = scrapertools.find_single_match(elem['release_date'], '(\d{4})-\d+-\d+')
        else:
            title = unify.normalize(elem['name']).capitalize()
            tvshow = True

        new_item = Item(channel='search', title=title, infoLabels=elem, action='do_search', extra=title,
                        category=config.get_localized_string(70695), context ='')

        if tvshow:
            new_item.contentSerieName = title
        else:
            new_item.contentTitle = title

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if item.page != '' and len(itemlist)>0:
        next_page = str(int(item.page)+1)
        #if not 'similar' in item.list_type:
        #    itemlist.append(item.clone(title='Pagina Siguente', page=next_page))
        #else:
        itemlist.append(Item(channel=item.channel, action='discover_list', title=config.get_localized_string(70065),
                             search_type=item.search_type, list_type=item.list_type, type=item.type, page=next_page))

    return itemlist

def search_tmdb(item):
    logger.debug(item)

    itemlist = []
    threads = []
    logger.debug(item)
    wanted = item.contentTitle

    search = do_search(item)

    if item.contentSerieName == '':
        results = exact_results(search, wanted)
        for result in results:
            logger.debug(result)
            t = Thread(target=get_links, args=[result])
            t.start()
            threads.append(t)

            for thread in threads:
                thread.join()

            # try:
            #     get_links(result)
            # except:
            #     pass

        for link in link_list:
            if link.action == 'play' and not 'trailer' in link.title.lower() and len(itemlist) < max_links:
                itemlist.append(link)

        return sorted(itemlist, key=lambda it: it.server)
    else:
        for item in search:
            if item.contentSerieName != '' and item.contentSerieName == wanted:
                logger.debug(item)
                itemlist.append(item)
        return itemlist

def get_links (item):
    logger.info()
    results =[]
    channel = __import__('channels.%s' % item.from_channel, None, None, ["channels.%s" % item.from_channel])
    if len(link_list) <= max_links:
        link_list.extend(getattr(channel, item.from_action)(item))

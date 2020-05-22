# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# Server management
# --------------------------------------------------------------------------------

from __future__ import division
from __future__ import absolute_import
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    #from future import standard_library
    #standard_library.install_aliases()
    import urllib.parse as urlparse                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                             # Usamos el nativo de PY2 que es más rápido

from future.builtins import range
from past.utils import old_div

import re

from core import filetools
from core import httptools
from core import jsontools
from core.item import Item
from platformcode import config, logger
from platformcode import platformtools
from lib import unshortenit

dict_servers_parameters = {}
server_list = {}


def find_video_items(item=None, data=None):
    """
    Función genérica para buscar vídeos en una página, devolviendo un itemlist con los items listos para usar.
     - Si se pasa un Item como argumento, a los items resultantes mantienen los parametros del item pasado
     - Si no se pasa un Item, se crea uno nuevo, pero no contendra ningun parametro mas que los propios del servidor.

    @param item: Item al cual se quieren buscar vídeos, este debe contener la url válida
    @type item: Item
    @param data: Cadena con el contendio de la página ya descargado (si no se pasa item)
    @type data: str

    @return: devuelve el itemlist con los resultados
    @rtype: list
    """
    logger.info()
    itemlist = []

    # Descarga la página
    if data is None:
        data = httptools.downloadpage(item.url).data

    data = unshortenit.findlinks(data)

    # Crea un item si no hay item
    if item is None:
        item = Item()
    # Pasa los campos thumbnail y title a contentThumbnail y contentTitle
    else:
        if not item.contentThumbnail:
            item.contentThumbnail = item.thumbnail
        if not item.contentTitle:
            item.contentTitle = item.title

    # Busca los enlaces a los videos
    for label, url, server, thumbnail in findvideos(data):
        title = config.get_localized_string(70206) % label
        itemlist.append(
            item.clone(title=title, action="play", url=url, thumbnail=thumbnail, server=server, folder=False))

    return itemlist


def get_servers_itemlist(itemlist, fnc=None, sort=False):
    """
    Obtiene el servidor para cada uno de los items, en funcion de su url.
     - Asigna el servidor, la url modificada, el thumbnail (si el item no contiene contentThumbnail se asigna el del thumbnail)
     - Si se pasa una funcion por el argumento fnc, esta se ejecuta pasando el item como argumento,
       el resultado de esa funcion se asigna al titulo del item
       - En esta funcion podemos modificar cualquier cosa del item
       - Esta funcion siempre tiene que devolver el item.title como resultado
     - Si no se encuentra servidor para una url, se asigna "directo"
     
    @param itemlist: listado de items
    @type itemlist: list
    @param fnc: función para ejecutar con cada item (para asignar el titulo)
    @type fnc: function
    @param sort: indica si el listado resultante se ha de ordenar en funcion de la lista de servidores favoritos
    @type sort: bool
    """
    # Recorre los servidores
    for serverid in list(get_servers_list().keys()):
        server_parameters = get_server_parameters(serverid)

        # Recorre los patrones
        for pattern in server_parameters.get("find_videos", {}).get("patterns", []):
            logger.info(pattern["pattern"])
            # Recorre los resultados
            for match in re.compile(pattern["pattern"], re.DOTALL).finditer(
                    "\n".join([item.url.split('|')[0] for item in itemlist if not item.server])):
                url = pattern["url"]
                for x in range(len(match.groups())):
                    url = url.replace("\\%s" % (x + 1), match.groups()[x])

                for item in itemlist:
                    if match.group() in item.url:
                        if not item.contentThumbnail:
                            item.contentThumbnail = item.thumbnail
                        item.thumbnail = server_parameters.get("thumbnail", "")
                        item.server = serverid
                        if '|' in item.url:
                            item.url = url + '|' + item.url.split('|')[1]
                        else:
                            item.url = url

    # Eliminamos los servidores desactivados
    #itemlist = filter(lambda i: not i.server or is_server_enabled(i.server), itemlist)
    # Filtrar si es necesario
    itemlist = filter_servers(itemlist)

    for item in itemlist:
        # Asignamos "directo" en caso de que el server no se encuentre en Alfa
        if not item.server and item.url:
            item.server = "directo"

        if fnc:
            item.title = fnc(item)


    # Ordenar segun favoriteslist si es necesario
    if sort:
        itemlist = sort_servers(itemlist)

    return itemlist


def findvideos(data, skip=False):
    """
    Recorre la lista de servidores disponibles y ejecuta la funcion findvideosbyserver para cada uno de ellos
    :param data: Texto donde buscar los enlaces
    :param skip: Indica un limite para dejar de recorrer la lista de servidores. Puede ser un booleano en cuyo caso
    seria False para recorrer toda la lista (valor por defecto) o True para detenerse tras el primer servidor que
    retorne algun enlace. Tambien puede ser un entero mayor de 1, que representaria el numero maximo de enlaces a buscar.
    :return:
    """
    logger.info()
    devuelve = []
    skip = int(skip)
    servers_list = list(get_servers_list().keys())


    is_filter_servers = False

    # Ejecuta el findvideos en cada servidor activo
    for serverid in servers_list:
        '''if not is_server_enabled(serverid):
            continue'''
        if config.get_setting("filter_servers") == True and config.get_setting("black_list", server=serverid):
            is_filter_servers = True
            continue
        devuelve.extend(findvideosbyserver(data, serverid))
        if skip and len(devuelve) >= skip:
            devuelve = devuelve[:skip]
            break
    if config.get_setting("filter_servers") == False:  is_filter_servers = False
    if not devuelve and is_filter_servers:
        platformtools.dialog_ok(config.get_localized_string(60000), config.get_localized_string(60001))

    return devuelve


def findvideosbyserver(data, serverid):
    serverid = get_server_name(serverid)
    if not serverid:
        return []

    server_parameters = get_server_parameters(serverid)
    if not server_parameters["active"]:
        return []
    devuelve = []
    if "find_videos" in server_parameters:
        # Recorre los patrones
        for pattern in server_parameters["find_videos"].get("patterns", []):
            msg = "%s\npattern: %s" % (serverid, pattern["pattern"])
            # Recorre los resultados
            for match in re.compile(pattern["pattern"], re.DOTALL).finditer(data):
                url = pattern["url"]
                # Crea la url con los datos
                for x in range(len(match.groups())):
                    url = url.replace("\\%s" % (x + 1), match.groups()[x])
                msg += "\nurl encontrada: %s" % url
                value = server_parameters["name"], url, serverid, server_parameters.get("thumbnail", "")
                if value not in devuelve and url not in server_parameters["find_videos"].get("ignore_urls", []):
                    devuelve.append(value)
                logger.info(msg)

    return devuelve


def guess_server_thumbnail(serverid):
    server = get_server_name(serverid)
    server_parameters = get_server_parameters(server)
    return server_parameters.get('thumbnail', "")


def get_server_from_url(url):
    logger.info()
    servers_list = list(get_servers_list().keys())

    # Ejecuta el findvideos en cada servidor activo
    for serverid in servers_list:
        '''if not is_server_enabled(serverid):
            continue'''
        if config.get_setting("filter_servers") == True and config.get_setting("black_list", server=serverid):
            continue
        serverid = get_server_name(serverid)
        if not serverid:
            continue
        server_parameters = get_server_parameters(serverid)
        if not server_parameters["active"]:
            continue
        if "find_videos" in server_parameters:
            # Recorre los patrones
            for n, pattern in enumerate(server_parameters["find_videos"].get("patterns", [])):
                msg = "%s\npattern: %s" % (serverid, pattern["pattern"])
                if not "pattern_compiled" in pattern:
                    # logger.info('compiled ' + serverid)
                    pattern["pattern_compiled"] = re.compile(pattern["pattern"])
                    dict_servers_parameters[serverid]["find_videos"]["patterns"][n]["pattern_compiled"] = pattern["pattern_compiled"]
                # Recorre los resultados
                match = re.search(pattern["pattern_compiled"], url)
                if match:
                    url = pattern["url"]
                    # Crea la url con los datos
                    for x in range(len(match.groups())):
                        url = url.replace("\\%s" % (x + 1), match.groups()[x])
                    msg += "\nurl encontrada: %s" % url
                    value = server_parameters["name"], url, serverid, server_parameters.get("thumbnail", "")
                    if url not in server_parameters["find_videos"].get("ignore_urls", []):
                        logger.info(msg)
                        return value

    return None


def resolve_video_urls_for_playing(server, url, video_password="", muestra_dialogo=False, background_dialog=False):
    """
    Función para obtener la url real del vídeo
    @param server: Servidor donde está alojado el vídeo
    @type server: str
    @param url: url del vídeo
    @type url: str
    @param video_password: Password para el vídeo
    @type video_password: str
    @param muestra_dialogo: Muestra el diálogo de progreso
    @type muestra_dialogo: bool
    @type background_dialog: bool
    @param background_dialog: if progress dialog should be in background

    @return: devuelve la url del video
    @rtype: list
    """
    logger.info("Server: %s, Url: %s" % (server, url))

    server = server.lower()

    video_urls = []
    video_exists = True
    error_messages = []
    opciones = []

    # Si el vídeo es "directo" o "local", no hay que buscar más
    if server == "directo" or server == "local":
        if isinstance(video_password, list):
            return video_password, len(video_password) > 0, "<br/>".join(error_messages)
        logger.info("Server: %s, la url es la buena" % server)
        video_urls.append(["%s [%s]" % (urlparse.urlparse(url)[2][-4:], server), url])

    # Averigua la URL del vídeo
    else:
        if server:
            server_parameters = get_server_parameters(server)
        else:
            server_parameters = {}

        if server_parameters:
            # Muestra un diágo de progreso
            if muestra_dialogo:
                progreso = (platformtools.dialog_progress_bg if background_dialog else platformtools.dialog_progress)(config.get_localized_string(20000),
                                                         config.get_localized_string(70180) % server_parameters["name"])

            # Cuenta las opciones disponibles, para calcular el porcentaje

            orden = [
                ["free"] + [server] + [premium for premium in server_parameters["premium"] if not premium == server],
                [server] + [premium for premium in server_parameters["premium"] if not premium == server] + ["free"],
                [premium for premium in server_parameters["premium"] if not premium == server] + [server] + ["free"]
            ]

            if server_parameters["free"] == True:
                opciones.append("free")
            opciones.extend(
                [premium for premium in server_parameters["premium"] if config.get_setting("premium", server=premium)])

            priority = int(config.get_setting("resolve_priority"))
            opciones = sorted(opciones, key=lambda x: orden[priority].index(x))

            logger.info("Opciones disponibles: %s | %s" % (len(opciones), opciones))
        else:
            logger.error("No existe conector para el servidor %s" % server)
            error_messages.append(config.get_localized_string(60004) % server)
            muestra_dialogo = False

        # Importa el server
        try:
            server_module = __import__('servers.%s' % server, None, None, ["servers.%s" % server])
            logger.info("Servidor importado: %s" % server_module)
        except:
            server_module = None
            if muestra_dialogo:
                progreso.close()
            logger.error("No se ha podido importar el servidor: %s" % server)
            import traceback
            logger.error(traceback.format_exc())

        # Si tiene una función para ver si el vídeo existe, lo comprueba ahora
        if hasattr(server_module, 'test_video_exists'):
            logger.info("Invocando a %s.test_video_exists" % server)
            try:
                video_exists, message = server_module.test_video_exists(page_url=url)

                if not video_exists:
                    error_messages.append(message)
                    logger.info("test_video_exists dice que el video no existe")
                    if muestra_dialogo:
                        progreso.close()
                else:
                    logger.info("test_video_exists dice que el video SI existe")
            except:
                logger.error("No se ha podido comprobar si el video existe")
                import traceback
                logger.error(traceback.format_exc())

        # Si el video existe y el modo free está disponible, obtenemos la url
        if video_exists:
            for opcion in opciones:
                # Opcion free y premium propio usa el mismo server
                if opcion == "free" or opcion == server:
                    serverid = server_module
                    server_name = server_parameters["name"]

                # Resto de opciones premium usa un debrider
                else:
                    serverid = __import__('servers.debriders.%s' % opcion, None, None,
                                          ["servers.debriders.%s" % opcion])
                    server_name = get_server_parameters(opcion)["name"]

                # Muestra el progreso
                if muestra_dialogo:
                    progreso.update((old_div(100, len(opciones))) * opciones.index(opcion), config.get_localized_string(70180) % server_name)

                # Modo free
                if opcion == "free":
                    try:
                        logger.info("Invocando a %s.get_video_url" % server)
                        response = serverid.get_video_url(page_url=url, video_password=video_password)
                        video_urls.extend(response)
                    except:
                        logger.error("Error al obtener la url en modo free")
                        error_messages.append(config.get_localized_string(60006) % server_name)
                        import traceback
                        logger.error(traceback.format_exc())

                # Modo premium
                else:
                    try:
                        logger.info("Invocando a %s.get_video_url" % opcion)
                        response = serverid.get_video_url(page_url=url, premium=True,
                                                          user=config.get_setting("user", server=opcion),
                                                          password=config.get_setting("password", server=opcion),
                                                          video_password=video_password)
                        if response and response[0][1]:
                            video_urls.extend(response)
                        elif response and response[0][0]:
                            error_messages.append(response[0][0])
                        else:
                            error_messages.append(config.get_localized_string(60006) % server_name)
                    except:
                        logger.error("Error en el servidor: %s" % opcion)
                        error_messages.append(config.get_localized_string(60006) % server_name)
                        import traceback
                        logger.error(traceback.format_exc())

                # Si ya tenemos URLS, dejamos de buscar
                if video_urls and config.get_setting("resolve_stop") == True:
                    break

            # Cerramos el progreso
            if muestra_dialogo:
                progreso.update(100, config.get_localized_string(60008))
                progreso.close()

            # Si no hay opciones disponibles mostramos el aviso de las cuentas premium
            if video_exists and not opciones and server_parameters.get("premium"):
                listapremium = [get_server_parameters(premium)["name"] for premium in server_parameters["premium"]]
                error_messages.append(
                    config.get_localized_string(60009) % (server, " o ".join(listapremium)))

            # Si no tenemos urls ni mensaje de error, ponemos uno generico
            elif not video_urls and not error_messages:
                error_messages.append(config.get_localized_string(60006) % get_server_parameters(server)["name"])

    return video_urls, len(video_urls) > 0, "<br/>".join(error_messages)


def get_server_name(serverid):
    """
    Función obtener el nombre del servidor real a partir de una cadena.
    @param serverid: Cadena donde mirar
    @type serverid: str

    @return: Nombre del servidor
    @rtype: str
    """
    serverid = serverid.lower().split(".")[0]

    # Obtenemos el listado de servers
    server_list = list(get_servers_list().keys())

    # Si el nombre está en la lista
    if serverid in server_list:
        return serverid

    # Recorre todos los servers buscando el nombre
    for server in server_list:
        params = get_server_parameters(server)
        # Si la nombre esta en el listado de ids
        if serverid in params["id"]:
            return server
        # Si el nombre es mas de una palabra, comprueba si algun id esta dentro del nombre:
        elif len(serverid.split()) > 1:
            for id in params["id"]:
                if id in serverid:
                    return server

    # Si no se encuentra nada se devuelve una cadena vacia
    return ""


def is_server_enabled(server):
    """
    Función comprobar si un servidor está segun la configuración establecida
    @param server: Nombre del servidor
    @type server: str

    @return: resultado de la comprobación
    @rtype: bool
    """

    server = get_server_name(server)

    # El server no existe
    if not server:
        return False

    server_parameters = get_server_parameters(server)
    if server_parameters["active"] == True:
        if not config.get_setting("hidepremium"):
            return True
        elif server_parameters["free"] == True:
            return True
        elif [premium for premium in server_parameters["premium"] if config.get_setting("premium", server=premium)]:
            return True

    return False


def get_server_parameters(server):
    """
    Obtiene los datos del servidor
    @param server: Nombre del servidor
    @type server: str

    @return: datos del servidor
    @rtype: dict
    """
    # logger.info("server %s" % server)
    global dict_servers_parameters
    server = server.split('.')[0]
    if not server:
        return {}

    if server not in dict_servers_parameters:
        try:
            # Servers
            if filetools.isfile(filetools.join(config.get_runtime_path(), "servers", server + ".json")):
                path = filetools.join(config.get_runtime_path(), "servers", server + ".json")

            # Debriders
            elif filetools.isfile(filetools.join(config.get_runtime_path(), "servers", "debriders", server + ".json")):
                path = filetools.join(config.get_runtime_path(), "servers", "debriders", server + ".json")
            #
            #Cuando no está bien definido el server en el canal (no existe conector), muestra error por no haber "path" y se tiene que revisar el canal
            #
            dict_server = jsontools.load(filetools.read(path))

            # Imagenes: se admiten url y archivos locales dentro de "resources/images"
            if dict_server.get("thumbnail") and "://" not in dict_server["thumbnail"]:
                dict_server["thumbnail"] = filetools.join(config.get_runtime_path(), "resources", "media",
                                                        "servers", dict_server["thumbnail"])
            for k in ['premium', 'id']:
                dict_server[k] = dict_server.get(k, list())

                if isinstance(dict_server[k], str):
                    dict_server[k] = [dict_server[k]]

            if "find_videos" in dict_server:
                dict_server['find_videos']["patterns"] = dict_server['find_videos'].get("patterns", list())
                dict_server['find_videos']["ignore_urls"] = dict_server['find_videos'].get("ignore_urls", list())

            if "settings" in dict_server:
                dict_server['has_settings'] = True
            else:
                dict_server['has_settings'] = False

            dict_servers_parameters[server] = dict_server

        except:
            mensaje = config.get_localized_string(59986) % server
            import traceback
            logger.error(mensaje + traceback.format_exc())
            return {}

    return dict_servers_parameters[server]


def get_server_json(server_name):
    # logger.info("server_name=" + server_name)
    try:
        server_path = filetools.join(config.get_runtime_path(), "servers", server_name + ".json")
        if not filetools.exists(server_path):
            server_path = filetools.join(config.get_runtime_path(), "servers", "debriders", server_name + ".json")

        # logger.info("server_path=" + server_path)
        server_json = jsontools.load(filetools.read(server_path))
        # logger.info("server_json= %s" % server_json)

    except Exception as ex:
        template = "An exception of type %s occured. Arguments:\n%r"
        message = template % (type(ex).__name__, ex.args)
        logger.error(" %s" % message)
        server_json = None

    return server_json


def get_server_host(server_name):
    from core import scrapertools
    return [scrapertools.get_domain_from_url(pattern['url']) for pattern in get_server_json(server_name)['find_videos']['patterns']]


def get_server_controls_settings(server_name):
    dict_settings = {}

    list_controls = get_server_json(server_name).get('settings', [])
    import copy
    list_controls = copy.deepcopy(list_controls)

    # Conversion de str a bool, etc...
    for c in list_controls:
        if 'id' not in c or 'type' not in c or 'default' not in c:
            # Si algun control de la lista  no tiene id, type o default lo ignoramos
            continue

        # new dict with key(id) and value(default) from settings
        dict_settings[c['id']] = c['default']

    return list_controls, dict_settings


def get_server_setting(name, server, default=None):
    """
        Retorna el valor de configuracion del parametro solicitado.

        Devuelve el valor del parametro 'name' en la configuracion propia del servidor 'server'.

        Busca en la ruta \addon_data\plugin.video.addon\settings_servers el archivo server_data.json y lee
        el valor del parametro 'name'. Si el archivo server_data.json no existe busca en la carpeta servers el archivo 
        server.json y crea un archivo server_data.json antes de retornar el valor solicitado. Si el parametro 'name'
        tampoco existe en el el archivo server.json se devuelve el parametro default.


        @param name: nombre del parametro
        @type name: str
        @param server: nombre del servidor
        @type server: str
        @param default: valor devuelto en caso de que no exista el parametro name
        @type default: any

        @return: El valor del parametro 'name'
        @rtype: any

        """
    # Creamos la carpeta si no existe
    if not filetools.exists(filetools.join(config.get_data_path(), "settings_servers")):
        filetools.mkdir(filetools.join(config.get_data_path(), "settings_servers"))

    file_settings = filetools.join(config.get_data_path(), "settings_servers", server + "_data.json")
    dict_settings = {}
    dict_file = {}
    if filetools.exists(file_settings):
        # Obtenemos configuracion guardada de ../settings/channel_data.json
        try:
            dict_file = jsontools.load(filetools.read(file_settings))
            if isinstance(dict_file, dict) and 'settings' in dict_file:
                dict_settings = dict_file['settings']
        except EnvironmentError:
            logger.info("ERROR al leer el archivo: %s" % file_settings)

    if not dict_settings or name not in dict_settings:
        # Obtenemos controles del archivo ../servers/server.json
        try:
            list_controls, default_settings = get_server_controls_settings(server)
        except:
            default_settings = {}
        if name in default_settings:  # Si el parametro existe en el server.json creamos el server_data.json
            default_settings.update(dict_settings)
            dict_settings = default_settings
            dict_file['settings'] = dict_settings
            # Creamos el archivo ../settings/channel_data.json
            if not filetools.write(file_settings, jsontools.dump(dict_file)):
                logger.info("ERROR al salvar el archivo: %s" % file_settings)

    # Devolvemos el valor del parametro local 'name' si existe, si no se devuelve default
    return dict_settings.get(name, default)


def set_server_setting(name, value, server):
    # Creamos la carpeta si no existe
    if not filetools.exists(filetools.join(config.get_data_path(), "settings_servers")):
        filetools.mkdir(filetools.join(config.get_data_path(), "settings_servers"))

    file_settings = filetools.join(config.get_data_path(), "settings_servers", server + "_data.json")
    dict_settings = {}

    dict_file = None

    if filetools.exists(file_settings):
        # Obtenemos configuracion guardada de ../settings/channel_data.json
        try:
            dict_file = jsontools.load(filetools.read(file_settings))
            dict_settings = dict_file.get('settings', {})
        except EnvironmentError:
            logger.info("ERROR al leer el archivo: %s" % file_settings)

    dict_settings[name] = value

    # comprobamos si existe dict_file y es un diccionario, sino lo creamos
    if dict_file is None or not dict_file:
        dict_file = {}

    dict_file['settings'] = dict_settings

    # Creamos el archivo ../settings/channel_data.json
    if not filetools.write(file_settings, jsontools.dump(dict_file)):
        logger.info("ERROR al salvar el archivo: %s" % file_settings)
        return None

    return value


def get_servers_list():
    """
    Obtiene un diccionario con todos los servidores disponibles

    @return: Diccionario cuyas claves son los nombre de los servidores (nombre del json)
    y como valor un diccionario con los parametros del servidor.
    @rtype: dict
    """
    global server_list
    if not server_list:
        for server in filetools.listdir(filetools.join(config.get_runtime_path(), "servers")):
            if server.endswith(".json") and not server == "version.json":
                server_parameters = get_server_parameters(server)
                server_list[server.split(".")[0]] = server_parameters
        server_list = sort_servers(server_list)
    return server_list


def get_debriders_list():
    """
    Obtiene un diccionario con todos los debriders disponibles

    @return: Diccionario cuyas claves son los nombre de los debriders (nombre del json)
    y como valor un diccionario con los parametros del servidor.
    @rtype: dict
    """
    server_list = {}
    for server in filetools.listdir(filetools.join(config.get_runtime_path(), "servers", "debriders")):
        if server.endswith(".json"):
            server_parameters = get_server_parameters(server)
            if server_parameters["active"] == True:
                logger.info(server_parameters)
                server_list[server.split(".")[0]] = server_parameters
    return server_list


def sort_servers(servers_list):
    """
    Si esta activada la opcion "Ordenar servidores" en la configuracion de servidores y existe un listado de servidores 
    favoritos en la configuracion lo utiliza para ordenar la lista servers_list
    :param servers_list: Listado de servidores para ordenar. Los elementos de la lista servers_list pueden ser strings
    u objetos Item. En cuyo caso es necesario q tengan un atributo item.server del tipo str.
    :return: Lista del mismo tipo de objetos que servers_list ordenada en funcion de los servidores favoritos.
    """
    if servers_list and config.get_setting('favorites_servers'):
        if isinstance(servers_list[0], Item):
            servers_list = sorted(servers_list,
                                  key=lambda x: config.get_setting("favorites_servers_list", server=x.server) or 100)
        else:
            servers_list = sorted(servers_list,
                                  key=lambda x: config.get_setting("favorites_servers_list", server=x) or 100)

    return servers_list


def filter_servers(servers_list):
    """
    Si esta activada la opcion "Filtrar por servidores" en la configuracion de servidores, elimina de la lista 
    de entrada los servidores incluidos en la Lista Negra.
    :param servers_list: Listado de servidores para filtrar. Los elementos de la lista servers_list pueden ser strings
    u objetos Item. En cuyo caso es necesario q tengan un atributo item.server del tipo str.
    :return: Lista del mismo tipo de objetos que servers_list filtrada en funcion de la Lista Negra.
    """
    #Eliminamos los inactivos
    if servers_list:
        servers_list = [i for i in servers_list if not i.server or is_server_enabled(i.server)]

    
    if servers_list and config.get_setting('filter_servers'):
        if isinstance(servers_list[0], Item):
            servers_list_filter = [x for x in servers_list if not config.get_setting("black_list", server=x.server)]
        else:
            servers_list_filter = [x for x in servers_list if not config.get_setting("black_list", server=x)]

        # Si no hay enlaces despues de filtrarlos
        if servers_list_filter or not platformtools.dialog_yesno(config.get_localized_string(60000),
                                                                 config.get_localized_string(60010),
                                                                 config.get_localized_string(70281)):
            servers_list = servers_list_filter
    
    return servers_list

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Comprobación de enlaces
# -----------------------

def check_list_links(itemlist, numero='', timeout=3):
    """
    Comprueba una lista de enlaces a videos y la devuelve modificando el titulo con la verificacion.
    El parámetro numero indica cuantos enlaces hay que verificar (0:5, 1:10, 2:15, 3:20)
    El parámetro timeout indica un tope de espera para descargar la página
    """
    numero = numero if numero > 4 else ((int(numero) + 1) * 5) if numero != '' else 5
    import sys
    if sys.version_info[0] >= 3:
        from concurrent import futures
    else:
        from concurrent_py2 import futures
    with futures.ThreadPoolExecutor() as executor:
        checked = []
        for it in itemlist:
            if numero > 0 and it.server != '' and it.url != '':
                checked.append(executor.submit(check_video_link, it, timeout))
                numero -= 1
        for link in futures.as_completed(checked):
            res = link.result()
            if res:
                it = res[0]
                verificacion = res[1]
                it.title = verificacion + ' ' + it.title.strip()
                logger.info('VERIFICATION= ' + verificacion)
                it.alive = verificacion
    return itemlist

def check_video_link(item, timeout=3):
    """
        Comprueba si el enlace a un video es valido y devuelve un string de 2 posiciones con la verificacion.
        :param url, server: Link y servidor
        :return: str(2) '??':No se ha podido comprobar. 'Ok':Parece que el link funciona. 'NO':Parece que no funciona.
        """
    url = item.url
    server = item.server
    
    NK = "[COLOR 0xFFF9B613][B]" + u"\u2022".encode('utf-8') + "[/B][/COLOR]"
    OK = "[COLOR 0xFF00C289][B]" + u"\u2022".encode('utf-8') + "[/B][/COLOR]"
    KO = "[COLOR 0xFFC20000][B]" + u"\u2022".encode('utf-8') + "[/B][/COLOR]"

    # NK = "[COLOR 0xFFF9B613][B]♥[/B][/COLOR]"
    # OK = "[COLOR 0xFF00C289][B]♥[/B][/COLOR]"
    # KO = "[COLOR 0xFFC20000][B]♥[/B][/COLOR]"

    try:
        server_module = __import__('servers.%s' % server, None, None, ["servers.%s" % server])
    except:
        server_module = None
        logger.info("[check_video_link] No se puede importar el servidor! %s" % server)
        return item, NK
        
    if hasattr(server_module, 'test_video_exists'):
        ant_timeout = httptools.HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT
        httptools.HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT = timeout  # Limitar tiempo de descarga
        
        try:
            video_exists, message = server_module.test_video_exists(page_url=url)
            if not video_exists:
                logger.info("[check_video_link] No existe! %s %s %s" % (message, server, url))
                resultado = KO
            else:
                logger.info("[check_video_link] comprobacion OK %s %s" % (server, url))
                resultado = OK
        except:
            logger.info("[check_video_link] No se puede comprobar ahora! %s %s" % (server, url))
            resultado = NK

        finally:
            httptools.HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT = ant_timeout  # Restaurar tiempo de descarga
            return item, resultado

    logger.info("[check_video_link] No hay test_video_exists para servidor: %s" % server)
    return item, NK

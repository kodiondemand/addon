# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Gestor de descargas
# ------------------------------------------------------------

import os
import re
import time
import unicodedata


from core import filetools, jsontools, scraper, scrapertools, servertools, videolibrarytools, support
from core.downloader import Downloader
from core.item import Item
from platformcode import config, logger
from platformcode import platformtools

STATUS_COLORS = {0: "orange", 1: "orange", 2: "green", 3: "red"}
STATUS_CODES = type("StatusCode", (), {"stoped": 0, "canceled": 1, "completed": 2, "error": 3})
DOWNLOAD_LIST_PATH = config.get_setting("downloadlistpath")
DOWNLOAD_PATH = config.get_setting("downloadpath")
STATS_FILE = os.path.join(config.get_data_path(), "servers.json")

TITLE_FILE = "[COLOR %s][%i%%][/COLOR] %s"
TITLE_TVSHOW = "[COLOR %s][%i%%][/COLOR] %s [%s]"


def mainlist(item):
    logger.info()
    itemlist = []

    # Lista de archivos
    for file in sorted(filetools.listdir(DOWNLOAD_LIST_PATH)):
        # Saltamos todos los que no sean JSON
        if not file.endswith(".json"): continue

        # cargamos el item
        file = os.path.join(DOWNLOAD_LIST_PATH, file)
        i = Item(path=file).fromjson(filetools.read(file))
        i.thumbnail = i.contentThumbnail

        # Listado principal
        if not item.contentType == "tvshow":
            # Series
            if i.contentType == "episode":
                # Comprobamos que la serie no este ya en el itemlist
                if not filter(
                        lambda x: x.contentSerieName == i.contentSerieName and x.contentChannel == i.contentChannel,
                        itemlist):

                    title = TITLE_TVSHOW % (
                        STATUS_COLORS[i.downloadStatus], i.downloadProgress, i.contentSerieName, i.contentChannel)

                    itemlist.append(Item(title=title, channel="downloads", action="mainlist", contentType="tvshow",
                                         contentSerieName=i.contentSerieName, contentChannel=i.contentChannel,
                                         downloadStatus=i.downloadStatus, downloadProgress=[i.downloadProgress],
                                         fanart=i.fanart, thumbnail=i.thumbnail))

                else:
                    s = \
                        filter(
                            lambda x: x.contentSerieName == i.contentSerieName and x.contentChannel == i.contentChannel,
                            itemlist)[0]
                    s.downloadProgress.append(i.downloadProgress)
                    downloadProgress = sum(s.downloadProgress) / len(s.downloadProgress)

                    if not s.downloadStatus in [STATUS_CODES.error, STATUS_CODES.canceled] and not i.downloadStatus in [
                        STATUS_CODES.completed, STATUS_CODES.stoped]:
                        s.downloadStatus = i.downloadStatus

                    s.title = TITLE_TVSHOW % (
                        STATUS_COLORS[s.downloadStatus], downloadProgress, i.contentSerieName, i.contentChannel)

            # Peliculas
            elif i.contentType == "movie" or i.contentType == "video":
                i.title = TITLE_FILE % (STATUS_COLORS[i.downloadStatus], i.downloadProgress, i.contentTitle)
                itemlist.append(i)

        # Listado dentro de una serie
        else:
            if i.contentType == "episode" and i.contentSerieName == item.contentSerieName and i.contentChannel == item.contentChannel:
                i.title = TITLE_FILE % (STATUS_COLORS[i.downloadStatus], i.downloadProgress,
                                        "%dx%0.2d: %s" % (i.contentSeason, i.contentEpisodeNumber, i.contentTitle))
                itemlist.append(i)

    estados = [i.downloadStatus for i in itemlist]

       # Si hay alguno completado
    if 2 in estados:
        itemlist.insert(0, Item(channel=item.channel, action="clean_ready", title=config.get_localized_string(70218),
                                contentType=item.contentType, contentChannel=item.contentChannel,
                                contentSerieName=item.contentSerieName, text_color="sandybrown"))

    # Si hay alguno con error
    if 3 in estados:
        itemlist.insert(0, Item(channel=item.channel, action="restart_error", title=config.get_localized_string(70219),
                                contentType=item.contentType, contentChannel=item.contentChannel,
                                contentSerieName=item.contentSerieName, text_color="orange"))

    # Si hay alguno pendiente
    if 1 in estados or 0 in estados:
        itemlist.insert(0, Item(channel=item.channel, action="download_all", title=support.typo(config.get_localized_string(70220),'bold'),
                                contentType=item.contentType, contentChannel=item.contentChannel,
                                contentSerieName=item.contentSerieName))

    if len(itemlist):
        itemlist.insert(0, Item(channel=item.channel, action="clean_all", title=support.typo(config.get_localized_string(70221),'bold'),
                                contentType=item.contentType, contentChannel=item.contentChannel,
                                contentSerieName=item.contentSerieName))

    if not item.contentType == "tvshow" and config.get_setting("browser", "downloads") == True:
        itemlist.insert(0, Item(channel=item.channel, action="browser", title=support.typo(config.get_localized_string(70222),'bold'),url=DOWNLOAD_PATH))

    if not item.contentType == "tvshow":
        itemlist.insert(0, Item(channel=item.channel, action="settings", title= support.typo(config.get_localized_string(70223),'bold color kod')))

    return itemlist


def settings(item):
    ret = platformtools.show_channel_settings(caption=config.get_localized_string(70224))
    platformtools.itemlist_refresh()
    return ret


def browser(item):
    logger.info()
    itemlist = []

    for file in filetools.listdir(item.url):
        if file == "list": continue
        if filetools.isdir(filetools.join(item.url, file)):
            itemlist.append(
                Item(channel=item.channel, title=file, action=item.action, url=filetools.join(item.url, file)))
        else:
            itemlist.append(Item(channel=item.channel, title=file, action="play", url=filetools.join(item.url, file)))

    return itemlist


def clean_all(item):
    logger.info()

    for fichero in sorted(filetools.listdir(DOWNLOAD_LIST_PATH)):
        if fichero.endswith(".json"):
            download_item = Item().fromjson(filetools.read(os.path.join(DOWNLOAD_LIST_PATH, fichero)))
            if not item.contentType == "tvshow" or (
                            item.contentSerieName == download_item.contentSerieName and item.contentChannel == download_item.contentChannel):
                filetools.remove(os.path.join(DOWNLOAD_LIST_PATH, fichero))

    platformtools.itemlist_refresh()


def clean_ready(item):
    logger.info()
    for fichero in sorted(filetools.listdir(DOWNLOAD_LIST_PATH)):
        if fichero.endswith(".json"):
            download_item = Item().fromjson(filetools.read(os.path.join(DOWNLOAD_LIST_PATH, fichero)))
            if not item.contentType == "tvshow" or (
                            item.contentSerieName == download_item.contentSerieName and item.contentChannel == download_item.contentChannel):
                if download_item.downloadStatus == STATUS_CODES.completed:
                    filetools.remove(os.path.join(DOWNLOAD_LIST_PATH, fichero))

    platformtools.itemlist_refresh()


def restart_error(item):
    logger.info()
    for fichero in sorted(filetools.listdir(DOWNLOAD_LIST_PATH)):
        if fichero.endswith(".json"):
            download_item = Item().fromjson(filetools.read(os.path.join(DOWNLOAD_LIST_PATH, fichero)))

            if not item.contentType == "tvshow" or (
                            item.contentSerieName == download_item.contentSerieName and item.contentChannel == download_item.contentChannel):
                if download_item.downloadStatus == STATUS_CODES.error:
                    if filetools.isfile(
                            os.path.join(config.get_setting("downloadpath"), download_item.downloadFilename)):
                        filetools.remove(
                            os.path.join(config.get_setting("downloadpath"), download_item.downloadFilename))

                    update_json(item.path,
                                {"downloadStatus": STATUS_CODES.stoped, "downloadComplete": 0, "downloadProgress": 0})

    platformtools.itemlist_refresh()


def download_all(item):
    time.sleep(0.5)
    for fichero in sorted(filetools.listdir(DOWNLOAD_LIST_PATH)):
        if fichero.endswith(".json"):
            download_item = Item(path=os.path.join(DOWNLOAD_LIST_PATH, fichero)).fromjson(
                filetools.read(os.path.join(DOWNLOAD_LIST_PATH, fichero)))

            if not item.contentType == "tvshow" or (
                            item.contentSerieName == download_item.contentSerieName and item.contentChannel == download_item.contentChannel):
                if download_item.downloadStatus in [STATUS_CODES.stoped, STATUS_CODES.canceled]:
                    res = start_download(download_item)
                    platformtools.itemlist_refresh()
                    # Si se ha cancelado paramos
                    if res == STATUS_CODES.canceled: break


def menu(item):
    logger.info()
    if item.downloadServer:
        servidor = item.downloadServer.get("server", "Auto")
    else:
        servidor = "Auto"
    # Opciones disponibles para el menu
    op = [config.get_localized_string(70225), config.get_localized_string(70226), config.get_localized_string(70227),
          "Modificar servidor: %s" % (servidor.capitalize())]

    opciones = []

    # Opciones para el menu
    if item.downloadStatus == 0:  # Sin descargar
        opciones.append(op[0])  # Descargar
        if not item.server: opciones.append(op[3])  # Elegir Servidor
        opciones.append(op[1])  # Eliminar de la lista

    if item.downloadStatus == 1:  # descarga parcial
        opciones.append(op[0])  # Descargar
        if not item.server: opciones.append(op[3])  # Elegir Servidor
        opciones.append(op[2])  # Reiniciar descarga
        opciones.append(op[1])  # Eliminar de la lista

    if item.downloadStatus == 2:  # descarga completada
        opciones.append(op[1])  # Eliminar de la lista
        opciones.append(op[2])  # Reiniciar descarga

    if item.downloadStatus == 3:  # descarga con error
        opciones.append(op[2])  # Reiniciar descarga
        opciones.append(op[1])  # Eliminar de la lista

    # Mostramos el dialogo
    seleccion = platformtools.dialog_select(config.get_localized_string(30163), opciones)

    # -1 es cancelar
    if seleccion == -1: return

    logger.info("opcion=%s" % (opciones[seleccion]))
    # Opcion Eliminar
    if opciones[seleccion] == op[1]:
        filetools.remove(item.path)

    # Opcion inicaiar descarga
    if opciones[seleccion] == op[0]:
        start_download(item)

    # Elegir Servidor
    if opciones[seleccion] == op[3]:
        select_server(item)

    # Reiniciar descarga
    if opciones[seleccion] == op[2]:
        if filetools.isfile(os.path.join(config.get_setting("downloadpath"), item.downloadFilename)):
            filetools.remove(os.path.join(config.get_setting("downloadpath"), item.downloadFilename))

        update_json(item.path, {"downloadStatus": STATUS_CODES.stoped, "downloadComplete": 0, "downloadProgress": 0,
                                "downloadServer": {}})

    platformtools.itemlist_refresh()


def move_to_libray(item):
    download_path = filetools.join(config.get_setting("downloadpath"), item.downloadFilename)
    library_path = filetools.join(config.get_videolibrary_path(), *filetools.split(item.downloadFilename))
    final_path = download_path

    if config.get_setting("library_add", "downloads") == True and config.get_setting("library_move", "downloads") == True:
        if not filetools.isdir(filetools.dirname(library_path)):
            filetools.mkdir(filetools.dirname(library_path))

        if filetools.isfile(library_path) and filetools.isfile(download_path):
            filetools.remove(library_path)

        if filetools.isfile(download_path):
            if filetools.move(download_path, library_path):
                final_path = library_path

            if len(filetools.listdir(filetools.dirname(download_path))) == 0:
                filetools.rmdir(filetools.dirname(download_path))

    if config.get_setting("library_add", "downloads") == True:
        if filetools.isfile(final_path):
            if item.contentType == "movie" and item.infoLabels["tmdb_id"]:
                library_item = Item(title=config.get_localized_string(70228) % item.downloadFilename, channel="downloads",
                                    action="findvideos", infoLabels=item.infoLabels, url=final_path)
                videolibrarytools.save_movie(library_item)

            elif item.contentType == "episode" and item.infoLabels["tmdb_id"]:
                library_item = Item(title=config.get_localized_string(70228) % item.downloadFilename, channel="downloads",
                                    action="findvideos", infoLabels=item.infoLabels, url=final_path)
                tvshow = Item(channel="downloads", contentType="tvshow",
                              infoLabels={"tmdb_id": item.infoLabels["tmdb_id"]})
                videolibrarytools.save_tvshow(tvshow, [library_item])


def update_json(path, params):
    item = Item().fromjson(filetools.read(path))
    item.__dict__.update(params)
    filetools.write(path, item.tojson())


def save_server_statistics(server, speed, success):
    if os.path.isfile(STATS_FILE):
        servers = jsontools.load(open(STATS_FILE, "rb").read())
    else:
        servers = {}

    if not server in servers:
        servers[server] = {"success": [], "count": 0, "speeds": [], "last": 0}

    servers[server]["count"] += 1
    servers[server]["success"].append(bool(success))
    servers[server]["success"] = servers[server]["success"][-5:]
    servers[server]["last"] = time.time()
    if success:
        servers[server]["speeds"].append(speed)
        servers[server]["speeds"] = servers[server]["speeds"][-5:]

    open(STATS_FILE, "wb").write(jsontools.dump(servers))
    return


def get_server_position(server):
    if os.path.isfile(STATS_FILE):
        servers = jsontools.load(open(STATS_FILE, "rb").read())
    else:
        servers = {}

    if server in servers:
        pos = [s for s in sorted(servers, key=lambda x: (sum(servers[x]["speeds"]) / (len(servers[x]["speeds"]) or 1),
                                                         float(sum(servers[x]["success"])) / (
                                                             len(servers[x]["success"]) or 1)), reverse=True)]
        return pos.index(server) + 1
    else:
        return 0


def get_match_list(data, match_list, order_list=None, only_ascii=False, ignorecase=False):
    """
    Busca coincidencias en una cadena de texto, con un diccionario de "ID" / "Listado de cadenas de busqueda":
     { "ID1" : ["Cadena 1", "Cadena 2", "Cadena 3"],
       "ID2" : ["Cadena 4", "Cadena 5", "Cadena 6"]
     }
     
     El diccionario no pude contener una misma cadena de busqueda en varías IDs.
     
     La busqueda se realiza por orden de tamaño de cadena de busqueda (de mas larga a mas corta) si una cadena coincide,
     se elimina de la cadena a buscar para las siguientes, para que no se detecten dos categorias si una cadena es parte de otra:
     por ejemplo: "Idioma Español" y "Español" si la primera aparece en la cadena "Pablo sabe hablar el Idioma Español" 
     coincidira con "Idioma Español" pero no con "Español" ya que la coincidencia mas larga tiene prioridad.
     
    """
    match_dict = dict()
    matches = []

    # Pasamos la cadena a unicode
    data = unicode(data, "utf8")

    # Pasamos el diccionario a {"Cadena 1": "ID1", "Cadena 2", "ID1", "Cadena 4", "ID2"} y los pasamos a unicode
    for key in match_list:
        if order_list and not key in order_list:
            raise Exception("key '%s' not in match_list" % key)
        for value in match_list[key]:
            if value in match_dict:
                raise Exception("Duplicate word in list: '%s'" % value)
            match_dict[unicode(value, "utf8")] = key

    # Si ignorecase = True, lo pasamos todo a mayusculas
    if ignorecase:
        data = data.upper()
        match_dict = dict((key.upper(), match_dict[key]) for key in match_dict)

    # Si ascii = True, eliminamos todos los accentos y Ñ
    if only_ascii:
        data = ''.join((c for c in unicodedata.normalize('NFD', data) if unicodedata.category(c) != 'Mn'))
        match_dict = dict((''.join((c for c in unicodedata.normalize('NFD', key) if unicodedata.category(c) != 'Mn')),
                           match_dict[key]) for key in match_dict)

    # Ordenamos el listado de mayor tamaño a menor y buscamos.
    for match in sorted(match_dict, key=lambda x: len(x), reverse=True):
        s = data
        for a in matches:
            s = s.replace(a, "")
        if match in s:
            matches.append(match)
    if matches:
        if order_list:
            return type("Mtch_list", (),
                        {"key": match_dict[matches[-1]], "index": order_list.index(match_dict[matches[-1]])})
        else:
            return type("Mtch_list", (), {"key": match_dict[matches[-1]], "index": None})
    else:
        if order_list:
            return type("Mtch_list", (), {"key": None, "index": len(order_list)})
        else:
            return type("Mtch_list", (), {"key": None, "index": None})


def sort_method(item):
    """
    Puntua cada item en funcion de varios parametros:     
    @type item: item
    @param item: elemento que se va a valorar.
    @return:  puntuacion otenida
    @rtype: int
    """
    lang_orders = {}
    lang_orders[0] = ["ES", "LAT", "SUB", "ENG", "VOSE"]
    lang_orders[1] = ["ES", "SUB", "LAT", "ENG", "VOSE"]
    lang_orders[2] = ["ENG", "SUB", "VOSE", "ESP", "LAT"]
    lang_orders[3] = ["VOSE", "ENG", "SUB", "ESP", "LAT"]

    quality_orders = {}
    quality_orders[0] = ["BLURAY", "FULLHD", "HD", "480P", "360P", "240P"]
    quality_orders[1] = ["FULLHD", "HD", "480P", "360P", "240P", "BLURAY"]
    quality_orders[2] = ["HD", "480P", "360P", "240P", "FULLHD", "BLURAY"]
    quality_orders[3] = ["480P", "360P", "240P", "BLURAY", "FULLHD", "HD"]

    order_list_idiomas = lang_orders[int(config.get_setting("language", "downloads"))]
    match_list_idimas = {"ES": ["CAST", "ESP", "Castellano", "Español", "Audio Español"],
                         "LAT": ["LAT", "Latino"],
                         "SUB": ["Subtitulo Español", "Subtitulado", "SUB"],
                         "ENG": ["EN", "ENG", "Inglés", "Ingles", "English"],
                         "VOSE": ["VOSE"]}

    order_list_calidad = ["BLURAY", "FULLHD", "HD", "480P", "360P", "240P"]
    order_list_calidad = quality_orders[int(config.get_setting("quality", "downloads"))]
    match_list_calidad = {"BLURAY": ["BR", "BLURAY"],
                          "FULLHD": ["FULLHD", "FULL HD", "1080", "HD1080", "HD 1080"],
                          "HD": ["HD", "HD REAL", "HD 720", "720", "HDTV"],
                          "480P": ["SD", "480P"],
                          "360P": ["360P"],
                          "240P": ["240P"]}

    value = (get_match_list(item.title, match_list_idimas, order_list_idiomas, ignorecase=True, only_ascii=True).index, \
             get_match_list(item.title, match_list_calidad, order_list_calidad, ignorecase=True, only_ascii=True).index)

    if config.get_setting("server_speed", "downloads"):
        value += tuple([get_server_position(item.server)])

    return value


def download_from_url(url, item):
    logger.info("Intentando descargar: %s" % (url))
    if url.lower().endswith(".m3u8") or url.lower().startswith("rtmp"):
        save_server_statistics(item.server, 0, False)
        return {"downloadStatus": STATUS_CODES.error}

    # Obtenemos la ruta de descarga y el nombre del archivo
    item.downloadFilename = item.downloadFilename.replace('/','-')
    download_path = filetools.dirname(filetools.join(DOWNLOAD_PATH, item.downloadFilename))
    file_name = filetools.basename(filetools.join(DOWNLOAD_PATH, item.downloadFilename))

    # Creamos la carpeta si no existe

    if not filetools.exists(download_path):
        filetools.mkdir(download_path)

    # Lanzamos la descarga
    d = Downloader(url, download_path, file_name,
                   max_connections=1 + int(config.get_setting("max_connections", "downloads")),
                   block_size=2 ** (17 + int(config.get_setting("block_size", "downloads"))),
                   part_size=2 ** (20 + int(config.get_setting("part_size", "downloads"))),
                   max_buffer=2 * int(config.get_setting("max_buffer", "downloads")))
    d.start_dialog(config.get_localized_string(60332))

    # Descarga detenida. Obtenemos el estado:
    # Se ha producido un error en la descarga   
    if d.state == d.states.error:
        logger.info("Error al intentar descargar %s" % (url))
        status = STATUS_CODES.error

    # La descarga se ha detenifdo
    elif d.state == d.states.stopped:
        logger.info("Descarga detenida")
        status = STATUS_CODES.canceled

    # La descarga ha finalizado
    elif d.state == d.states.completed:
        logger.info("Descargado correctamente")
        status = STATUS_CODES.completed

        if item.downloadSize and item.downloadSize != d.size[0]:
            status = STATUS_CODES.error

    save_server_statistics(item.server, d.speed[0], d.state != d.states.error)

    dir = os.path.dirname(item.downloadFilename)
    file = filetools.join(dir, d.filename)

    if status == STATUS_CODES.completed:
        move_to_libray(item.clone(downloadFilename=file))

    return {"downloadUrl": d.download_url, "downloadStatus": status, "downloadSize": d.size[0],
            "downloadProgress": d.progress, "downloadCompleted": d.downloaded[0], "downloadFilename": file}


def download_from_server(item):
    logger.info(item.tostring())
    unsupported_servers = ["torrent"]

    progreso = platformtools.dialog_progress(config.get_localized_string(30101), config.get_localized_string(70178) % item.server)
    channel = __import__('channels.%s' % item.contentChannel, None, None, ["channels.%s" % item.contentChannel])
    if hasattr(channel, "play") and not item.play_menu:

        progreso.update(50, config.get_localized_string(70178) % item.server, config.get_localized_string(60003) % item.contentChannel)
        try:
            itemlist = getattr(channel, "play")(item.clone(channel=item.contentChannel, action=item.contentAction))
        except:
            logger.error("Error en el canal %s" % item.contentChannel)
        else:
            if len(itemlist) and isinstance(itemlist[0], Item):
                download_item = item.clone(**itemlist[0].__dict__)
                download_item.contentAction = download_item.action
                download_item.infoLabels = item.infoLabels
                item = download_item
            elif len(itemlist) and isinstance(itemlist[0], list):
                item.video_urls = itemlist
                if not item.server: item.server = "directo"
            else:
                logger.info("No hay nada que reproducir")
                return {"downloadStatus": STATUS_CODES.error}
    progreso.close()
    logger.info("contentAction: %s | contentChannel: %s | server: %s | url: %s" % (
        item.contentAction, item.contentChannel, item.server, item.url))

    if not item.server or not item.url or not item.contentAction == "play" or item.server in unsupported_servers:
        logger.error("El Item no contiene los parametros necesarios.")
        return {"downloadStatus": STATUS_CODES.error}

    if not item.video_urls:
        video_urls, puedes, motivo = servertools.resolve_video_urls_for_playing(item.server, item.url, item.password,
                                                                                True)
    else:
        video_urls, puedes, motivo = item.video_urls, True, ""

        # Si no esta disponible, salimos
    if not puedes:
        logger.info("El vídeo **NO** está disponible")
        return {"downloadStatus": STATUS_CODES.error}

    else:
        logger.info("El vídeo **SI** está disponible")

        result = {}

        # Recorre todas las opciones hasta que consiga descargar una correctamente
        for video_url in reversed(video_urls):

            result = download_from_url(video_url[1], item)

            if result["downloadStatus"] in [STATUS_CODES.canceled, STATUS_CODES.completed]:
                break

            # Error en la descarga, continuamos con la siguiente opcion
            if result["downloadStatus"] == STATUS_CODES.error:
                continue

        # Devolvemos el estado
        return result


def download_from_best_server(item):
    logger.info(
        "contentAction: %s | contentChannel: %s | url: %s" % (item.contentAction, item.contentChannel, item.url))

    result = {"downloadStatus": STATUS_CODES.error}

    progreso = platformtools.dialog_progress(config.get_localized_string(30101), config.get_localized_string(70179))
    channel = __import__('channels.%s' % item.contentChannel, None, None, ["channels.%s" % item.contentChannel])

    progreso.update(50, config.get_localized_string(70184), config.get_localized_string(70180) % item.contentChannel)

    if hasattr(channel, item.contentAction):
        play_items = getattr(channel, item.contentAction)(
            item.clone(action=item.contentAction, channel=item.contentChannel))
    else:
        play_items = servertools.find_video_items(item.clone(action=item.contentAction, channel=item.contentChannel))

    play_items = filter(lambda x: x.action == "play" and not "trailer" in x.title.lower(), play_items)

    progreso.update(100, config.get_localized_string(70183), config.get_localized_string(70181) % len(play_items),
                    config.get_localized_string(70182))

    if config.get_setting("server_reorder", "downloads") == 1:
        play_items.sort(key=sort_method)

    if progreso.iscanceled():
        return {"downloadStatus": STATUS_CODES.canceled}

    progreso.close()

    # Recorremos el listado de servers, hasta encontrar uno que funcione
    for play_item in play_items:
        play_item = item.clone(**play_item.__dict__)
        play_item.contentAction = play_item.action
        play_item.infoLabels = item.infoLabels

        result = download_from_server(play_item)

        if progreso.iscanceled():
            result["downloadStatus"] = STATUS_CODES.canceled

        # Tanto si se cancela la descarga como si se completa dejamos de probar mas opciones
        if result["downloadStatus"] in [STATUS_CODES.canceled, STATUS_CODES.completed]:
            result["downloadServer"] = {"url": play_item.url, "server": play_item.server}
            break

    return result


def select_server(item):
    logger.info(
        "contentAction: %s | contentChannel: %s | url: %s" % (item.contentAction, item.contentChannel, item.url))

    progreso = platformtools.dialog_progress(config.get_localized_string(30101), config.get_localized_string(70179))
    channel = __import__('channels.%s' % item.contentChannel, None, None, ["channels.%s" % item.contentChannel])
    progreso.update(50, config.get_localized_string(70184), config.get_localized_string(70180) % item.contentChannel)

    if hasattr(channel, item.contentAction):
        play_items = getattr(channel, item.contentAction)(
            item.clone(action=item.contentAction, channel=item.contentChannel))
    else:
        play_items = servertools.find_video_items(item.clone(action=item.contentAction, channel=item.contentChannel))

    play_items = filter(lambda x: x.action == "play" and not "trailer" in x.title.lower(), play_items)

    progreso.update(100, config.get_localized_string(70183), config.get_localized_string(70181) % len(play_items),
                    config.get_localized_string(70182))

    for x, i in enumerate(play_items):
        if not i.server and hasattr(channel, "play"):
            play_items[x] = getattr(channel, "play")(i)

    seleccion = platformtools.dialog_select(config.get_localized_string(70192), ["Auto"] + [s.title for s in play_items])
    if seleccion > 1:
        update_json(item.path, {
            "downloadServer": {"url": play_items[seleccion - 1].url, "server": play_items[seleccion - 1].server}})
    elif seleccion == 0:
        update_json(item.path, {"downloadServer": {}})

    platformtools.itemlist_refresh()


def start_download(item):
    logger.info(
        "contentAction: %s | contentChannel: %s | url: %s" % (item.contentAction, item.contentChannel, item.url))

    # Ya tenemnos server, solo falta descargar
    if item.contentAction == "play":
        ret = download_from_server(item)
        update_json(item.path, ret)
        return ret["downloadStatus"]

    elif item.downloadServer and item.downloadServer.get("server"):
        ret = download_from_server(
            item.clone(server=item.downloadServer.get("server"), url=item.downloadServer.get("url"),
                       contentAction="play"))
        update_json(item.path, ret)
        return ret["downloadStatus"]
    # No tenemos server, necesitamos buscar el mejor
    else:
        ret = download_from_best_server(item)
        update_json(item.path, ret)
        return ret["downloadStatus"]


def get_episodes(item):
    logger.info("contentAction: %s | contentChannel: %s | contentType: %s" % (
        item.contentAction, item.contentChannel, item.contentType))

    # El item que pretendemos descargar YA es un episodio
    if item.contentType == "episode":
        episodes = [item.clone()]

    # El item es uma serie o temporada
    elif item.contentType in ["tvshow", "season"]:
        # importamos el canal
        channel = __import__('channels.%s' % item.contentChannel, None, None, ["channels.%s" % item.contentChannel])
        # Obtenemos el listado de episodios
        episodes = getattr(channel, item.contentAction)(item)

    itemlist = []

    # Tenemos las lista, ahora vamos a comprobar
    for episode in episodes:

        # Si partiamos de un item que ya era episodio estos datos ya están bien, no hay que modificarlos
        if item.contentType != "episode":
            episode.contentAction = episode.action
            episode.contentChannel = episode.channel

        # Si el resultado es una temporada, no nos vale, tenemos que descargar los episodios de cada temporada
        if episode.contentType == "season":
            itemlist.extend(get_episodes(episode))

        # Si el resultado es un episodio ya es lo que necesitamos, lo preparamos para añadirlo a la descarga
        if episode.contentType == "episode":

            # Pasamos el id al episodio
            if not episode.infoLabels["tmdb_id"]:
                episode.infoLabels["tmdb_id"] = item.infoLabels["tmdb_id"]

            # Episodio, Temporada y Titulo
            if not episode.contentSeason or not episode.contentEpisodeNumber:
                season_and_episode = scrapertools.get_season_and_episode(episode.title)
                if season_and_episode:
                    episode.contentSeason = season_and_episode.split("x")[0]
                    episode.contentEpisodeNumber = season_and_episode.split("x")[1]

            # Buscamos en tmdb
            if item.infoLabels["tmdb_id"]:
                scraper.find_and_set_infoLabels(episode)

            # Episodio, Temporada y Titulo
            if not episode.contentTitle:
                episode.contentTitle = re.sub("\[[^\]]+\]|\([^\)]+\)|\d*x\d*\s*-", "", episode.title).strip()

            episode.downloadFilename = filetools.validate_path(os.path.join(item.downloadFilename, "%dx%0.2d - %s" % (
                episode.contentSeason, episode.contentEpisodeNumber, episode.contentTitle.strip())))

            itemlist.append(episode)
        # Cualquier otro resultado no nos vale, lo ignoramos
        else:
            logger.info("Omitiendo item no válido: %s" % episode.tostring())

    return itemlist


def write_json(item):
    logger.info()

    item.action = "menu"
    item.channel = "downloads"
    item.downloadStatus = STATUS_CODES.stoped
    item.downloadProgress = 0
    item.downloadSize = 0
    item.downloadCompleted = 0
    if not item.contentThumbnail:
        item.contentThumbnail = item.thumbnail

    for name in ["text_bold", "text_color", "text_italic", "context", "totalItems", "viewmode", "title", "fulltitle",
                 "thumbnail"]:
        if item.__dict__.has_key(name):
            item.__dict__.pop(name)

    path = os.path.join(config.get_setting("downloadlistpath"), str(time.time()) + ".json")
    filetools.write(path, item.tojson())
    item.path = path
    time.sleep(0.1)


def save_download(item):
    logger.info()

    # Menu contextual
    if item.from_action and item.from_channel:
        item.channel = item.from_channel
        item.action = item.from_action
        del item.from_action
        del item.from_channel

    item.contentChannel = item.channel
    item.contentAction = item.action

    if item.contentType in ["tvshow", "episode", "season"]:
        save_download_tvshow(item)

    elif item.contentType == "movie":
        save_download_movie(item)

    else:
        save_download_video(item)


def save_download_video(item):
    logger.info("contentAction: %s | contentChannel: %s | contentTitle: %s" % (
        item.contentAction, item.contentChannel, item.contentTitle))

    set_movie_title(item)

    item.downloadFilename = filetools.validate_path("%s [%s]" % (item.contentTitle.strip(), item.contentChannel))

    write_json(item)

    if not platformtools.dialog_yesno(config.get_localized_string(30101), config.get_localized_string(70189)):
        platformtools.dialog_ok(config.get_localized_string(30101), item.contentTitle,
                                config.get_localized_string(30109))
    else:
        start_download(item)


def save_download_movie(item):
    logger.info("contentAction: %s | contentChannel: %s | contentTitle: %s" % (
        item.contentAction, item.contentChannel, item.contentTitle))

    progreso = platformtools.dialog_progress(config.get_localized_string(30101), config.get_localized_string(70191))

    set_movie_title(item)

    result = scraper.find_and_set_infoLabels(item)
    if not result:
        progreso.close()
        return save_download_video(item)

    progreso.update(0, config.get_localized_string(60062))

    item.downloadFilename = filetools.validate_path("%s [%s]" % (item.contentTitle.strip(), item.contentChannel))

    write_json(item)

    progreso.close()

    if not platformtools.dialog_yesno(config.get_localized_string(30101), config.get_localized_string(70189)):
        platformtools.dialog_ok(config.get_localized_string(30101), item.contentTitle,
                                config.get_localized_string(30109))
    else:
        start_download(item)


def save_download_tvshow(item):
    logger.info("contentAction: %s | contentChannel: %s | contentType: %s | contentSerieName: %s" % (
        item.contentAction, item.contentChannel, item.contentType, item.contentSerieName))

    progreso = platformtools.dialog_progress(config.get_localized_string(30101), config.get_localized_string(70188))

    scraper.find_and_set_infoLabels(item)

    item.downloadFilename = filetools.validate_path("%s [%s]" % (item.contentSerieName, item.contentChannel))

    progreso.update(0, config.get_localized_string(70186), config.get_localized_string(70187) % item.contentChannel)

    episodes = get_episodes(item)

    progreso.update(0, config.get_localized_string(70190), " ")

    for x, i in enumerate(episodes):
        progreso.update(x * 100 / len(episodes),
                        "%dx%0.2d: %s" % (i.contentSeason, i.contentEpisodeNumber, i.contentTitle))
        write_json(i)
    progreso.close()

    if not platformtools.dialog_yesno(config.get_localized_string(30101), config.get_localized_string(70189)):
        platformtools.dialog_ok(config.get_localized_string(30101),
                                str(len(episodes)) + " capitulos de: " + item.contentSerieName,
                                config.get_localized_string(30109))
    else:
        for i in episodes:
            res = start_download(i)
            if res == STATUS_CODES.canceled:
                break


def set_movie_title(item):
    if not item.contentTitle:
        item.contentTitle = re.sub("\[[^\]]+\]|\([^\)]+\)", "", item.fulltitle).strip()

    if not item.contentTitle:
        item.contentTitle = re.sub("\[[^\]]+\]|\([^\)]+\)", "", item.title).strip()

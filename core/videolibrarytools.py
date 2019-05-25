# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Common Library Tools
# ------------------------------------------------------------

import errno
import math
import traceback

from core import filetools
from core import scraper
from core import scrapertools
from core.item import Item
from lib import generictools
from platformcode import config, logger
from platformcode import platformtools

FOLDER_MOVIES = config.get_setting("folder_movies")
FOLDER_TVSHOWS = config.get_setting("folder_tvshows")
VIDEOLIBRARY_PATH = config.get_videolibrary_path()
MOVIES_PATH = filetools.join(VIDEOLIBRARY_PATH, FOLDER_MOVIES)
TVSHOWS_PATH = filetools.join(VIDEOLIBRARY_PATH, FOLDER_TVSHOWS)

if not FOLDER_MOVIES or not FOLDER_TVSHOWS or not VIDEOLIBRARY_PATH \
        or not filetools.exists(MOVIES_PATH) or not filetools.exists(TVSHOWS_PATH):
    config.verify_directories_created()

addon_name = "plugin://plugin.video.%s/" % config.PLUGIN_NAME


def read_nfo(path_nfo, item=None):
    """
    Metodo para leer archivos nfo.
        Los arcivos nfo tienen la siguiente extructura: url_scraper | xml + item_json
        [url_scraper] y [xml] son opcionales, pero solo uno de ellos ha de existir siempre.
    @param path_nfo: ruta absoluta al archivo nfo
    @type path_nfo: str
    @param item: Si se pasa este parametro el item devuelto sera una copia de este con
        los valores de 'infoLabels', 'library_playcounts' y 'path' leidos del nfo
    @type: Item
    @return: Una tupla formada por la cabecera (head_nfo ='url_scraper'|'xml') y el objeto 'item_json'
    @rtype: tuple (str, Item)
    """
    head_nfo = ""
    it = None

    data = filetools.read(path_nfo)

    if data:
        head_nfo = data.splitlines()[0] + "\n"
        data = "\n".join(data.splitlines()[1:])

        it_nfo = Item().fromjson(data)

        if item:
            it = item.clone()
            it.infoLabels = it_nfo.infoLabels
            if 'library_playcounts' in it_nfo:
                it.library_playcounts = it_nfo.library_playcounts
            if it_nfo.path:
                it.path = it_nfo.path
        else:
            it = it_nfo

        if 'fanart' in it.infoLabels:
            it.fanart = it.infoLabels['fanart']

    return head_nfo, it


def save_movie(item):
    """
    guarda en la libreria de peliculas el elemento item, con los valores que contiene.
    @type item: item
    @param item: elemento que se va a guardar.
    @rtype insertados: int
    @return:  el número de elementos insertados
    @rtype sobreescritos: int
    @return:  el número de elementos sobreescritos
    @rtype fallidos: int
    @return:  el número de elementos fallidos o -1 si ha fallado todo
    """
    logger.info()
    # logger.debug(item.tostring('\n'))
    insertados = 0
    sobreescritos = 0
    fallidos = 0
    path = ""

    # Itentamos obtener el titulo correcto:
    # 1. contentTitle: Este deberia ser el sitio correcto, ya que title suele contener "Añadir a la videoteca..."
    # 2. fulltitle
    # 3. title
    if not item.contentTitle:
        # Colocamos el titulo correcto en su sitio para que scraper lo localize
        if item.fulltitle:
            item.contentTitle = item.fulltitle
        else:
            item.contentTitle = item.title

    # Si llegados a este punto no tenemos titulo, salimos
    if not item.contentTitle or not item.channel:
        logger.debug("NO ENCONTRADO contentTitle")
        return 0, 0, -1  # Salimos sin guardar

    scraper_return = scraper.find_and_set_infoLabels(item)

    # Llegados a este punto podemos tener:
    #  scraper_return = True: Un item con infoLabels con la información actualizada de la peli
    #  scraper_return = False: Un item sin información de la peli (se ha dado a cancelar en la ventana)
    #  item.infoLabels['code'] == "" : No se ha encontrado el identificador de IMDB necesario para continuar, salimos
    if not scraper_return or not item.infoLabels['code']:
        # TODO de momento si no hay resultado no añadimos nada,
        # aunq podriamos abrir un cuadro para introducir el identificador/nombre a mano
        logger.debug("NO ENCONTRADO EN SCRAPER O NO TIENE code")
        return 0, 0, -1

    _id = item.infoLabels['code'][0]

    # progress dialog
    p_dialog = platformtools.dialog_progress(config.get_localized_string(20000), config.get_localized_string(60062))

    if config.get_setting("original_title_folder", "videolibrary") == 1 and item.infoLabels['originaltitle']:
        base_name = item.infoLabels['originaltitle']
    else:
        base_name = item.contentTitle

    base_name = unicode(filetools.validate_path(base_name.replace('/', '-')), "utf8").encode("utf8")

    if config.get_setting("lowerize_title", "videolibrary") == 0:
        base_name = base_name.lower()

    for raiz, subcarpetas, ficheros in filetools.walk(MOVIES_PATH):
        for c in subcarpetas:
            code = scrapertools.find_single_match(c, '\[(.*?)\]')
            if code and code in item.infoLabels['code']:
                path = filetools.join(raiz, c)
                _id = code
                break

    if not path:
        # Crear carpeta
        path = filetools.join(MOVIES_PATH, ("%s [%s]" % (base_name, _id)).strip())
        logger.info("Creando directorio pelicula:" + path)
        if not filetools.mkdir(path):
            logger.debug("No se ha podido crear el directorio")
            return 0, 0, -1

    nfo_path = filetools.join(path, "%s [%s].nfo" % (base_name, _id))
    strm_path = filetools.join(path, "%s.strm" % base_name)
    json_path = filetools.join(path, ("%s [%s].json" % (base_name, item.channel.lower())))

    nfo_exists = filetools.exists(nfo_path)
    strm_exists = filetools.exists(strm_path)
    json_exists = filetools.exists(json_path)

    if not nfo_exists:
        # Creamos .nfo si no existe
        logger.info("Creando .nfo: " + nfo_path)
        head_nfo = scraper.get_nfo(item)

        item_nfo = Item(title=item.contentTitle, channel="videolibrary", action='findvideos',
                        library_playcounts={"%s [%s]" % (base_name, _id): 0}, infoLabels=item.infoLabels,
                        library_urls={})

    else:
        # Si existe .nfo, pero estamos añadiendo un nuevo canal lo abrimos
        head_nfo, item_nfo = read_nfo(nfo_path)

    if not strm_exists:
        # Crear base_name.strm si no existe
        item_strm = Item(channel='videolibrary', action='play_from_library',
                         strm_path=strm_path.replace(MOVIES_PATH, ""), contentType='movie',
                         contentTitle=item.contentTitle)
        strm_exists = filetools.write(strm_path, '%s?%s' % (addon_name, item_strm.tourl()))
        item_nfo.strm_path = strm_path.replace(MOVIES_PATH, "")

    # Solo si existen item_nfo y .strm continuamos
    if item_nfo and strm_exists:

        if json_exists:
            logger.info("El fichero existe. Se sobreescribe")
            sobreescritos += 1
        else:
            insertados += 1

        # Si se ha marcado la opción de url de emergencia, se añade ésta a la película después de haber ejecutado Findvideos del canal
        try:
            channel = generictools.verify_channel(item.channel)
            if config.get_setting("emergency_urls", channel) in [1, 3]:
                item = emergency_urls(item, None, json_path)
                if item_nfo.emergency_urls and not isinstance(item_nfo.emergency_urls, dict):
                    del item_nfo.emergency_urls
                if not item_nfo.emergency_urls:
                    item_nfo.emergency_urls = dict()
                item_nfo.emergency_urls.update({item.channel: True})
        except:
            logger.error("No se ha podido guardar las urls de emergencia de %s en la videoteca" % item.contentTitle)
            logger.error(traceback.format_exc())
        
        if filetools.write(json_path, item.tojson()):
            p_dialog.update(100, 'Añadiendo película...', item.contentTitle)
            item_nfo.library_urls[item.channel] = item.url

            if filetools.write(nfo_path, head_nfo + item_nfo.tojson()):
                # actualizamos la videoteca de Kodi con la pelicula
                if config.is_xbmc():
                    from platformcode import xbmc_videolibrary
                    xbmc_videolibrary.update(FOLDER_MOVIES, filetools.basename(path) + "/")

                p_dialog.close()
                return insertados, sobreescritos, fallidos

    # Si llegamos a este punto es por q algo ha fallado
    logger.error("No se ha podido guardar %s en la videoteca" % item.contentTitle)
    p_dialog.update(100, config.get_localized_string(60063), item.contentTitle)
    p_dialog.close()
    return 0, 0, -1


def save_tvshow(item, episodelist):
    """
    guarda en la libreria de series la serie con todos los capitulos incluidos en la lista episodelist
    @type item: item
    @param item: item que representa la serie a guardar
    @type episodelist: list
    @param episodelist: listado de items que representan los episodios que se van a guardar.
    @rtype insertados: int
    @return:  el número de episodios insertados
    @rtype sobreescritos: int
    @return:  el número de episodios sobreescritos
    @rtype fallidos: int
    @return:  el número de episodios fallidos o -1 si ha fallado toda la serie
    @rtype path: str
    @return:  directorio serie
    """
    logger.info()
    # logger.debug(item.tostring('\n'))
    path = ""

    # Si llegados a este punto no tenemos titulo o code, salimos
    if not (item.contentSerieName or item.infoLabels['code']) or not item.channel:
        logger.debug("NO ENCONTRADO contentSerieName NI code")
        return 0, 0, -1, path  # Salimos sin guardar

    scraper_return = scraper.find_and_set_infoLabels(item)
    # Llegados a este punto podemos tener:
    #  scraper_return = True: Un item con infoLabels con la información actualizada de la serie
    #  scraper_return = False: Un item sin información de la peli (se ha dado a cancelar en la ventana)
    #  item.infoLabels['code'] == "" : No se ha encontrado el identificador de IMDB necesario para continuar, salimos
    if not scraper_return or not item.infoLabels['code']:
        # TODO de momento si no hay resultado no añadimos nada,
        # aunq podriamos abrir un cuadro para introducir el identificador/nombre a mano
        logger.debug("NO ENCONTRADO EN SCRAPER O NO TIENE code")
        return 0, 0, -1, path

    _id = item.infoLabels['code'][0]

    if config.get_setting("original_title_folder", "videolibrary") == 1 and item.infoLabels['originaltitle']:
        base_name = item.infoLabels['originaltitle']
    elif item.infoLabels['tvshowtitle']:
        base_name = item.infoLabels['tvshowtitle']
    elif item.infoLabels['title']:
        base_name = item.infoLabels['title']
    else:
        base_name = item.contentSerieName

    base_name = unicode(filetools.validate_path(base_name.replace('/', '-')), "utf8").encode("utf8")

    if config.get_setting("lowerize_title", "videolibrary") == 0:
        base_name = base_name.lower()

    for raiz, subcarpetas, ficheros in filetools.walk(TVSHOWS_PATH):
        for c in subcarpetas:
            code = scrapertools.find_single_match(c, '\[(.*?)\]')
            if code and code in item.infoLabels['code']:
                path = filetools.join(raiz, c)
                _id = code
                break

    if not path:
        path = filetools.join(TVSHOWS_PATH, ("%s [%s]" % (base_name, _id)).strip())
        logger.info("Creando directorio serie: " + path)
        try:
            filetools.mkdir(path)
        except OSError, exception:
            if exception.errno != errno.EEXIST:
                raise

    tvshow_path = filetools.join(path, "tvshow.nfo")
    if not filetools.exists(tvshow_path):
        # Creamos tvshow.nfo, si no existe, con la head_nfo, info de la serie y marcas de episodios vistos
        logger.info("Creando tvshow.nfo: " + tvshow_path)
        head_nfo = scraper.get_nfo(item)
        item.infoLabels['mediatype'] = "tvshow"
        item.infoLabels['title'] = item.contentSerieName
        item_tvshow = Item(title=item.contentSerieName, channel="videolibrary", action="get_seasons",
                           fanart=item.infoLabels['fanart'], thumbnail=item.infoLabels['thumbnail'],
                           infoLabels=item.infoLabels, path=path.replace(TVSHOWS_PATH, ""))
        item_tvshow.library_playcounts = {}
        item_tvshow.library_urls = {item.channel: item.url}

    else:
        # Si existe tvshow.nfo, pero estamos añadiendo un nuevo canal actualizamos el listado de urls
        head_nfo, item_tvshow = read_nfo(tvshow_path)
        item_tvshow.channel = "videolibrary"
        item_tvshow.action = "get_seasons"
        item_tvshow.library_urls[item.channel] = item.url

    # FILTERTOOLS
    # si el canal tiene filtro de idiomas, añadimos el canal y el show
    if episodelist and "list_language" in episodelist[0]:
        # si ya hemos añadido un canal previamente con filtro, añadimos o actualizamos el canal y show
        if "library_filter_show" in item_tvshow:
            if item.title_from_channel:
                item_tvshow.library_filter_show[item.channel] = item.title_from_channel
            else:
                item_tvshow.library_filter_show[item.channel] = item.show
        # no habia ningún canal con filtro y lo generamos por primera vez
        else:
            if item.title_from_channel:
                item_tvshow.library_filter_show = {item.channel: item.title_from_channel}
            else:
                item_tvshow.library_filter_show = {item.channel: item.show}

    if item.channel != "downloads":
        item_tvshow.active = 1  # para que se actualice a diario cuando se llame a videolibrary_service

    filetools.write(tvshow_path, head_nfo + item_tvshow.tojson())

    if not episodelist:
        # La lista de episodios esta vacia
        return 0, 0, 0, path

    # Guardar los episodios
    '''import time
    start_time = time.time()'''
    insertados, sobreescritos, fallidos = save_episodes(path, episodelist, item)
    '''msg = "Insertados: %d | Sobreescritos: %d | Fallidos: %d | Tiempo: %2.2f segundos" % \
          (insertados, sobreescritos, fallidos, time.time() - start_time)
    logger.debug(msg)'''

    return insertados, sobreescritos, fallidos, path


def save_episodes(path, episodelist, serie, silent=False, overwrite=True):
    """
    guarda en la ruta indicada todos los capitulos incluidos en la lista episodelist
    @type path: str
    @param path: ruta donde guardar los episodios
    @type episodelist: list
    @param episodelist: listado de items que representan los episodios que se van a guardar.
    @type serie: item
    @param serie: serie de la que se van a guardar los episodios
    @type silent: bool
    @param silent: establece si se muestra la notificación
    @param overwrite: permite sobreescribir los ficheros existentes
    @type overwrite: bool
    @rtype insertados: int
    @return:  el número de episodios insertados
    @rtype sobreescritos: int
    @return:  el número de episodios sobreescritos
    @rtype fallidos: int
    @return:  el número de episodios fallidos
    """
    logger.info()

    # No hay lista de episodios, no hay nada que guardar
    if not len(episodelist):
        logger.info("No hay lista de episodios, salimos sin crear strm")
        return 0, 0, 0

    insertados = 0
    sobreescritos = 0
    fallidos = 0
    news_in_playcounts = {}

    # Listamos todos los ficheros de la serie, asi evitamos tener que comprobar si existe uno por uno
    raiz, carpetas_series, ficheros = filetools.walk(path).next()
    ficheros = [filetools.join(path, f) for f in ficheros]

    nostrm_episodelist = []
    for root, folders, files in filetools.walk(path):
        for file in files:
            season_episode = scrapertools.get_season_and_episode(file)
            if season_episode == "" or filetools.exists(filetools.join(path, "%s.strm" % season_episode)):
                continue
            nostrm_episodelist.append(season_episode)
    nostrm_episodelist = sorted(set(nostrm_episodelist))

    # Silent es para no mostrar progreso (para videolibrary_service)
    if not silent:
        # progress dialog
        p_dialog = platformtools.dialog_progress(config.get_localized_string(20000), config.get_localized_string(60064))
        p_dialog.update(0, config.get_localized_string(60065))

    channel_alt = generictools.verify_channel(serie.channel)            #Preparamos para añadir las urls de emergencia
    emergency_urls_stat = config.get_setting("emergency_urls", channel_alt)         #El canal quiere urls de emergencia?
    emergency_urls_succ = False
    channel = __import__('channels.%s' % channel_alt, fromlist=["channels.%s" % channel_alt])
    if serie.torrent_caching_fail:                              #Si el proceso de conversión ha fallado, no se cachean
        emergency_urls_stat = 0
        del serie.torrent_caching_fail
    
    new_episodelist = []
    # Obtenemos el numero de temporada y episodio y descartamos los q no lo sean
    tags = []
    if config.get_setting("enable_filter", "videolibrary"):
        tags = [x.strip() for x in config.get_setting("filters", "videolibrary").lower().split(",")]
    for e in episodelist:
        if tags != [] and tags != None and any(tag in e.title.lower() for tag in tags):
            continue
        
        try:
            season_episode = scrapertools.get_season_and_episode(e.title)
        
            # Si se ha marcado la opción de url de emergencia, se añade ésta a cada episodio después de haber ejecutado Findvideos del canal
            if e.emergency_urls and isinstance(e.emergency_urls, dict): del e.emergency_urls    #Borramos trazas anteriores
            json_path = filetools.join(path, ("%s [%s].json" % (season_episode, e.channel)).lower())    #Path del .json del episodio
            if emergency_urls_stat == 1 and not e.emergency_urls and e.contentType == 'episode':     #Guardamos urls de emergencia?
                if not silent:
                    p_dialog.update(0, 'Cacheando enlaces y archivos .torrent...', e.title)     #progress dialog
                if json_path in ficheros:                                   #Si existe el .json sacamos de ahí las urls
                    if overwrite:                                           #pero solo si se se sobrescriben los .json
                        json_epi = Item().fromjson(filetools.read(json_path))                   #Leemos el .json
                        if json_epi.emergency_urls:                         #si existen las urls de emergencia...
                            e.emergency_urls = json_epi.emergency_urls                          #... las copiamos
                        else:                                                                   #y si no...
                            e = emergency_urls(e, channel, json_path)                           #... las generamos
                else:
                    e = emergency_urls(e, channel, json_path)               #Si el episodio no existe, generamos las urls
                if e.emergency_urls:                                                            #Si ya tenemos urls...
                    emergency_urls_succ = True                              #... es un éxito y vamos a marcar el .nfo
            elif emergency_urls_stat == 2 and e.contentType == 'episode':                       #Borramos urls de emergencia?
                if e.emergency_urls: del e.emergency_urls
                emergency_urls_succ = True                                  #... es un éxito y vamos a marcar el .nfo
            elif emergency_urls_stat == 3 and e.contentType == 'episode':   #Actualizamos urls de emergencia?
                if not silent:
                    p_dialog.update(0, 'Cacheando enlaces y archivos .torrent...', e.title)     #progress dialog
                e = emergency_urls(e, channel, json_path)                                       #generamos las urls
                if e.emergency_urls:                                                            #Si ya tenemos urls...
                    emergency_urls_succ = True                              #... es un éxito y vamos a marcar el .nfo
            
            if not e.infoLabels["tmdb_id"] or (serie.infoLabels["tmdb_id"] and e.infoLabels["tmdb_id"] != serie.infoLabels["tmdb_id"]):                         #en series multicanal, prevalece el infolabels...
                e.infoLabels = serie.infoLabels                             #... del canal actual y no el del original
            e.contentSeason, e.contentEpisodeNumber = season_episode.split("x")
            new_episodelist.append(e)
        except:
            if e.contentType == 'episode':
                logger.error("No se ha podido guardar las urls de emergencia de %s en la videoteca" % e.contentTitle)
                logger.error(traceback.format_exc())
            continue

    # No hay lista de episodios, no hay nada que guardar
    if not len(new_episodelist):
        logger.info("No hay lista de episodios, salimos sin crear strm")
        return 0, 0, 0

    # fix float porque la division se hace mal en python 2.x
    t = float(100) / len(new_episodelist)

    for i, e in enumerate(scraper.sort_episode_list(new_episodelist)):
        if not silent:
            p_dialog.update(int(math.ceil((i + 1) * t)), config.get_localized_string(60064), e.title)

        season_episode = "%sx%s" % (e.contentSeason, str(e.contentEpisodeNumber).zfill(2))
        strm_path = filetools.join(path, "%s.strm" % season_episode)
        nfo_path = filetools.join(path, "%s.nfo" % season_episode)
        json_path = filetools.join(path, ("%s [%s].json" % (season_episode, e.channel)).lower())

        if season_episode in nostrm_episodelist:
            continue
        strm_exists = strm_path in ficheros
        nfo_exists = nfo_path in ficheros
        json_exists = json_path in ficheros

        if not strm_exists:
            # Si no existe season_episode.strm añadirlo
            item_strm = Item(action='play_from_library', channel='videolibrary',
                             strm_path=strm_path.replace(TVSHOWS_PATH, ""), infoLabels={})
            item_strm.contentSeason = e.contentSeason
            item_strm.contentEpisodeNumber = e.contentEpisodeNumber
            item_strm.contentType = e.contentType
            item_strm.contentTitle = season_episode

            # FILTERTOOLS
            if item_strm.list_language:
                # si tvshow.nfo tiene filtro se le pasa al item_strm que se va a generar
                if "library_filter_show" in serie:
                    item_strm.library_filter_show = serie.library_filter_show

                if item_strm.library_filter_show == "":
                    logger.error("Se ha producido un error al obtener el nombre de la serie a filtrar")

            # logger.debug("item_strm" + item_strm.tostring('\n'))
            # logger.debug("serie " + serie.tostring('\n'))
            strm_exists = filetools.write(strm_path, '%s?%s' % (addon_name, item_strm.tourl()))

        item_nfo = None
        if not nfo_exists and e.infoLabels["code"]:
            # Si no existe season_episode.nfo añadirlo
            scraper.find_and_set_infoLabels(e)
            head_nfo = scraper.get_nfo(e)

            item_nfo = e.clone(channel="videolibrary", url="", action='findvideos',
                               strm_path=strm_path.replace(TVSHOWS_PATH, ""))
            if item_nfo.emergency_urls:
                del item_nfo.emergency_urls                     #Solo se mantiene en el .json del episodio

            nfo_exists = filetools.write(nfo_path, head_nfo + item_nfo.tojson())

        # Solo si existen season_episode.nfo y season_episode.strm continuamos
        if nfo_exists and strm_exists:
            if not json_exists or overwrite:
                # Obtenemos infoLabel del episodio
                if not item_nfo:
                    head_nfo, item_nfo = read_nfo(nfo_path)

                if not e.infoLabels["tmdb_id"] or (item_nfo.infoLabels["tmdb_id"] and e.infoLabels["tmdb_id"] != item_nfo.infoLabels["tmdb_id"]):                         #en series multicanal, prevalece el infolabels...
                    e.infoLabels = item_nfo.infoLabels          #... del canal actual y no el del original

                if filetools.write(json_path, e.tojson()):
                    if not json_exists:
                        logger.info("Insertado: %s" % json_path)
                        insertados += 1
                        # Marcamos episodio como no visto
                        news_in_playcounts[season_episode] = 0
                        # Marcamos la temporada como no vista
                        news_in_playcounts["season %s" % e.contentSeason] = 0
                        # Marcamos la serie como no vista
                        # logger.debug("serie " + serie.tostring('\n'))
                        news_in_playcounts[serie.contentSerieName] = 0

                    else:
                        logger.info("Sobreescrito: %s" % json_path)
                        sobreescritos += 1
                else:
                    logger.info("Fallido: %s" % json_path)
                    fallidos += 1

        else:
            logger.info("Fallido: %s" % json_path)
            fallidos += 1

        if not silent and p_dialog.iscanceled():
            break

    if not silent:
        p_dialog.close()

    if news_in_playcounts:
        # Si hay nuevos episodios los marcamos como no vistos en tvshow.nfo ...
        tvshow_path = filetools.join(path, "tvshow.nfo")
        try:
            import datetime
            head_nfo, tvshow_item = read_nfo(tvshow_path)
            tvshow_item.library_playcounts.update(news_in_playcounts)
            
            #Si la operación de insertar/borrar urls de emergencia en los .jsons de los episodios ha tenido éxito, se marca el .nfo
            if emergency_urls_succ:
                if tvshow_item.emergency_urls and not isinstance(tvshow_item.emergency_urls, dict):
                    del tvshow_item.emergency_urls
                if emergency_urls_stat in [1, 3]:                                       #Operación de guardar/actualizar enlaces
                    if not tvshow_item.emergency_urls:
                        tvshow_item.emergency_urls = dict()
                    tvshow_item.emergency_urls.update({serie.channel: True})
                elif emergency_urls_stat == 2:                                          #Operación de Borrar enlaces
                    if tvshow_item.emergency_urls and tvshow_item.emergency_urls.get(serie.channel, False):
                        tvshow_item.emergency_urls.pop(serie.channel, None)             #borramos la entrada del .nfo
                        
            if tvshow_item.active == 30:
                tvshow_item.active = 1
            update_last = datetime.date.today()
            tvshow_item.update_last = update_last.strftime('%Y-%m-%d')
            update_next = datetime.date.today() + datetime.timedelta(days=int(tvshow_item.active))
            tvshow_item.update_next = update_next.strftime('%Y-%m-%d')

            filetools.write(tvshow_path, head_nfo + tvshow_item.tojson())
        except:
            logger.error("Error al actualizar tvshow.nfo")
            logger.error("No se ha podido guardar las urls de emergencia de %s en la videoteca" % tvshow_item.contentSerieName)
            logger.error(traceback.format_exc())
            fallidos = -1
        else:
            # ... si ha sido correcto actualizamos la videoteca de Kodi
            if config.is_xbmc() and not silent:
                from platformcode import xbmc_videolibrary
                xbmc_videolibrary.update(FOLDER_TVSHOWS, filetools.basename(path))

    if fallidos == len(episodelist):
        fallidos = -1

    logger.debug("%s [%s]: insertados= %s, sobreescritos= %s, fallidos= %s" %
                 (serie.contentSerieName, serie.channel, insertados, sobreescritos, fallidos))
    return insertados, sobreescritos, fallidos


def add_movie(item):
    """
        guarda una pelicula en la libreria de cine. La pelicula puede ser un enlace dentro de un canal o un video
        descargado previamente.

        Para añadir episodios descargados en local, el item debe tener exclusivamente:
            - contentTitle: titulo de la pelicula
            - title: titulo a mostrar junto al listado de enlaces -findvideos- ("Reproducir video local HD")
            - infoLabels["tmdb_id"] o infoLabels["imdb_id"]
            - contentType == "movie"
            - channel = "downloads"
            - url : ruta local al video

        @type item: item
        @param item: elemento que se va a guardar.
    """
    logger.info()

    #Para desambiguar títulos, se provoca que TMDB pregunte por el título realmente deseado
    #El usuario puede seleccionar el título entre los ofrecidos en la primera pantalla
    #o puede cancelar e introducir un nuevo título en la segunda pantalla
    #Si lo hace en "Introducir otro nombre", TMDB buscará automáticamente el nuevo título
    #Si lo hace en "Completar Información", cambia parcialmente al nuevo título, pero no busca en TMDB.  Hay que hacerlo
    #Si se cancela la segunda pantalla, la variable "scraper_return" estará en False.  El usuario no quiere seguir
    
    item = generictools.update_title(item) #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels
    #if item.tmdb_stat:
    #    del item.tmdb_stat          #Limpiamos el status para que no se grabe en la Videoteca
    
    new_item = item.clone(action="findvideos")
    insertados, sobreescritos, fallidos = save_movie(new_item)

    if fallidos == 0:
        platformtools.dialog_ok(config.get_localized_string(30131), new_item.contentTitle,
                                config.get_localized_string(30135))  # 'se ha añadido a la videoteca'
    else:
        platformtools.dialog_ok(config.get_localized_string(30131),
                                config.get_localized_string(60066))  #"ERROR, la pelicula NO se ha añadido a la videoteca")


def add_tvshow(item, channel=None):
    """
        Guarda contenido en la libreria de series. Este contenido puede ser uno de estos dos:
            - La serie con todos los capitulos incluidos en la lista episodelist.
            - Un solo capitulo descargado previamente en local.

        Para añadir episodios descargados en local, el item debe tener exclusivamente:
            - contentSerieName (o show): Titulo de la serie
            - contentTitle: titulo del episodio para extraer season_and_episode ("1x01 Piloto")
            - title: titulo a mostrar junto al listado de enlaces -findvideos- ("Reproducir video local")
            - infoLabels["tmdb_id"] o infoLabels["imdb_id"]
            - contentType != "movie"
            - channel = "downloads"
            - url : ruta local al video

        @type item: item
        @param item: item que representa la serie a guardar
        @type channel: modulo
        @param channel: canal desde el que se guardara la serie.
            Por defecto se importara item.from_channel o item.channel

    """
    logger.info("show=#" + item.show + "#")

    if item.channel == "downloads":
        itemlist = [item.clone()]

    else:
        # Esta marca es porque el item tiene algo más aparte en el atributo "extra"
        item.action = item.extra
        if isinstance(item.extra, str) and "###" in item.extra:
            item.action = item.extra.split("###")[0]
            item.extra = item.extra.split("###")[1]

        if item.from_action:
            item.__dict__["action"] = item.__dict__.pop("from_action")
        if item.from_channel:
            item.__dict__["channel"] = item.__dict__.pop("from_channel")

        if not channel:
            try:
                channel = __import__('channels.%s' % item.channel, fromlist=["channels.%s" % item.channel])
            except ImportError:
                exec "import channels." + item.channel + " as channel"

        #Para desambiguar títulos, se provoca que TMDB pregunte por el título realmente deseado
        #El usuario puede seleccionar el título entre los ofrecidos en la primera pantalla
        #o puede cancelar e introducir un nuevo título en la segunda pantalla
        #Si lo hace en "Introducir otro nombre", TMDB buscará automáticamente el nuevo título
        #Si lo hace en "Completar Información", cambia parcialmente al nuevo título, pero no busca en TMDB.  Hay que hacerlo
        #Si se cancela la segunda pantalla, la variable "scraper_return" estará en False.  El usuario no quiere seguir
        
        item = generictools.update_title(item) #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels
        #if item.tmdb_stat:
        #    del item.tmdb_stat          #Limpiamos el status para que no se grabe en la Videoteca
                
        # Obtiene el listado de episodios
        itemlist = getattr(channel, item.action)(item)
        
    insertados, sobreescritos, fallidos, path = save_tvshow(item, itemlist)

    if not insertados and not sobreescritos and not fallidos:
        platformtools.dialog_ok(config.get_localized_string(30131), config.get_localized_string(60067))
        logger.error("La serie %s no se ha podido añadir a la videoteca. No se ha podido obtener ningun episodio"
                     % item.show)

    elif fallidos == -1:
        platformtools.dialog_ok(config.get_localized_string(30131), config.get_localized_string(60068))
        logger.error("La serie %s no se ha podido añadir a la videoteca" % item.show)

    elif fallidos > 0:
        platformtools.dialog_ok(config.get_localized_string(30131), config.get_localized_string(60069))
        logger.error("No se han podido añadir %s episodios de la serie %s a la videoteca" % (fallidos, item.show))

    else:
        platformtools.dialog_ok(config.get_localized_string(30131), config.get_localized_string(60070))
        logger.info("Se han añadido %s episodios de la serie %s a la videoteca" %
                    (insertados, item.show))
        if config.is_xbmc():
            if config.get_setting("sync_trakt_new_tvshow", "videolibrary"):
                import xbmc
                from platformcode import xbmc_videolibrary
                if config.get_setting("sync_trakt_new_tvshow_wait", "videolibrary"):
                    # Comprobar que no se esta buscando contenido en la videoteca de Kodi
                    while xbmc.getCondVisibility('Library.IsScanningVideo()'):
                        xbmc.sleep(1000)
                # Se lanza la sincronizacion para la videoteca de Kodi
                xbmc_videolibrary.sync_trakt_kodi()
                # Se lanza la sincronización para la videoteca del addon
                xbmc_videolibrary.sync_trakt_addon(path)


def emergency_urls(item, channel=None, path=None):
    logger.info()
    import re
    """ 
    Llamamos a Findvideos del canal con la variable "item.videolibray_emergency_urls = True" para obtener la variable
    "item.emergency_urls" con la lista de listas de tuplas de los enlaces torrent y de servidores directos para ese episodio o película
    En la lista [0] siempre deben ir los enlaces torrents, si los hay.  Si se desea cachear los .torrents, la búsqueda va contra esa lista.
    En la lista dos irán los enlaces de servidores directos, pero también pueden ir enlaces magnet (que no son cacheables)
    """
    #lanazamos un "lookup" en el "findvideos" del canal para obtener los enlaces de emergencia
    try:
        if channel == None:                             #Si el llamador no ha aportado la estructura de channel, se crea
            channel = generictools.verify_channel(item.channel)             #Se verifica si es un clon, que devuelva "newpct1"
            channel = __import__('channels.%s' % channel, fromlist=["channels.%s" % channel])
        if hasattr(channel, 'findvideos'):                                  #Si el canal tiene "findvideos"...
            item.videolibray_emergency_urls = True                          #... se marca como "lookup"
            channel_save = item.channel                 #... guarda el canal original por si hay fail-over en Newpct1
            item_res = getattr(channel, 'findvideos')(item)                 #... se procesa Findvideos
            item_res.channel = channel_save             #... restaura el canal original por si hay fail-over en Newpct1
            item_res.category = channel_save.capitalize()                   #... y la categoría
            del item_res.videolibray_emergency_urls                         #... y se borra la marca de lookup
    except:
        logger.error('ERROR al procesar el título en Findvideos del Canal: ' + item.channel + ' / ' + item.title)
        logger.error(traceback.format_exc())
        item_res = item.clone()                         #Si ha habido un error, se devuelve el Item original
        if item_res.videolibray_emergency_urls:
            del item_res.videolibray_emergency_urls                         #... y se borra la marca de lookup
    
    #Si el usuario ha activado la opción "emergency_urls_torrents", se descargarán los archivos .torrent de cada título
    else:                                                                   #Si se han cacheado con éxito los enlaces...
        try:
            referer = None
            post = None
            channel_bis = generictools.verify_channel(item.channel)
            if config.get_setting("emergency_urls_torrents", channel_bis) and item_res.emergency_urls and path != None:
                videolibrary_path = config.get_videolibrary_path()          #detectamos el path absoluto del título
                movies = config.get_setting("folder_movies")
                series = config.get_setting("folder_tvshows")
                if movies in path: 
                    folder = movies
                else:
                    folder = series
                videolibrary_path = filetools.join(videolibrary_path, folder)
                i = 1
                if item_res.referer: referer = item_res.referer
                if item_res.post: post = item_res.post
                for url in item_res.emergency_urls[0]:                      #Recorremos las urls de emergencia...
                    torrents_path = re.sub(r'(?:\.\w+$)', '_%s.torrent' % str(i).zfill(2), path)
                    path_real = caching_torrents(url, referer, post, torrents_path=torrents_path)      #...  para descargar los .torrents
                    if path_real:                                           #Si ha tenido éxito...
                        item_res.emergency_urls[0][i-1] = path_real.replace(videolibrary_path, '')  #se guarda el "path" relativo
                    i += 1
                    
                #Restauramos variables originales
                if item.referer:
                    item_res.referer = item.referer
                elif item_res.referer:
                    del item_res.referer
                if item.referer:
                    item_res.referer = item.referer
                elif item_res.referer:
                    del item_res.referer
                item_res.url = item.url
                
        except:
            logger.error('ERROR al cachear el .torrent de: ' + item.channel + ' / ' + item.title)
            logger.error(traceback.format_exc())
            item_res = item.clone()                             #Si ha habido un error, se devuelve el Item original

    #logger.debug(item_res.emergency_urls)
    return item_res                                             #Devolvemos el Item actualizado con los enlaces de emergencia
    
    
def caching_torrents(url, referer=None, post=None, torrents_path=None, timeout=10, lookup=False, data_torrent=False):
    if torrents_path != None:
        logger.info("path = " + torrents_path)
    else:
        logger.info()
    if referer and post:
        logger.info('REFERER: ' + referer)
    from core import httptools
    torrent_file = ''
    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Referer': referer} #Necesario para el Post del .Torrent
    
    """
    Descarga en el path recibido el .torrent de la url recibida, y pasa el decode
    Devuelve el path real del .torrent, o el path vacío si la operación no ha tenido éxito
    """
    
    videolibrary_path = config.get_videolibrary_path()              #Calculamos el path absoluto a partir de la Videoteca
    if torrents_path == None:
        if not videolibrary_path:
            torrents_path = ''
            if data_torrent:
                return (torrents_path, torrent_file)
            return torrents_path                                        #Si hay un error, devolvemos el "path" vacío
        torrents_path = filetools.join(videolibrary_path, 'temp_torrents_Alfa', 'cliente_torrent_Alfa.torrent')    #path de descarga temporal
    if '.torrent' not in torrents_path:
        torrents_path += '.torrent'                                     #path para dejar el .torrent
    torrents_path_encode = filetools.encode(torrents_path)              #encode utf-8 del path
    
    if url.endswith(".rar") or url.startswith("magnet:"):               #No es un archivo .torrent
        logger.error('No es un archivo Torrent: ' + url)
        torrents_path = ''
        if data_torrent:
            return (torrents_path, torrent_file)
        return torrents_path                                            #Si hay un error, devolvemos el "path" vacío
    
    try:
        #Descargamos el .torrent
        if referer and post:                                            #Descarga con POST
            response = httptools.downloadpage(url, headers=headers, post=post, follow_redirects=False, timeout=timeout)
        else:                                                           #Descarga sin post
            response = httptools.downloadpage(url, timeout=timeout)
        if not response.sucess:
            logger.error('Archivo .torrent no encontrado: ' + url)
            torrents_path = ''
            if data_torrent:
                return (torrents_path, torrent_file)
            return torrents_path                                        #Si hay un error, devolvemos el "path" vacío
        torrent_file = response.data

        if "used CloudFlare" in torrent_file:                           #Si tiene CloudFlare, usamos este proceso
            response = httptools.downloadpage("http://anonymouse.org/cgi-bin/anon-www.cgi/" + url.strip(), timeout=timeout)
            if not response.sucess:
                logger.error('Archivo .torrent no encontrado: ' + url)
                torrents_path = ''
                if data_torrent:
                    return (torrents_path, torrent_file)
                return torrents_path                                    #Si hay un error, devolvemos el "path" vacío
            torrent_file = response.data
        
        #Si es un archivo .ZIP tratamos de extraer el contenido
        if torrent_file.startswith("PK"):
            logger.info('Es un archivo .ZIP: ' + url)
            
            torrents_path_zip = filetools.join(videolibrary_path, 'temp_torrents_zip')  #Carpeta de trabajo
            torrents_path_zip = filetools.encode(torrents_path_zip)
            torrents_path_zip_file = filetools.join(torrents_path_zip, 'temp_torrents_zip.zip')     #Nombre del .zip
            
            import time
            filetools.rmdirtree(torrents_path_zip)                      #Borramos la carpeta temporal
            time.sleep(1)                                               #Hay que esperar, porque si no da error
            filetools.mkdir(torrents_path_zip)                          #La creamos de nuevo
            
            if filetools.write(torrents_path_zip_file, torrent_file):   #Salvamos el .zip
                torrent_file = ''                                       #Borramos el contenido en memoria
                try:                                                    #Extraemos el .zip
                    from core import ziptools
                    unzipper = ziptools.ziptools()
                    unzipper.extract(torrents_path_zip_file, torrents_path_zip)
                except:
                    import xbmc
                    xbmc.executebuiltin('XBMC.Extract("%s", "%s")' % (torrents_path_zip_file, torrents_path_zip))
                    time.sleep(1)
                
                import os
                for root, folders, files in os.walk(torrents_path_zip): #Recorremos la carpeta para leer el .torrent
                    for file in files:
                        if file.endswith(".torrent"):
                            input_file = filetools.join(root, file)                 #nombre del .torrent
                            torrent_file = filetools.read(input_file)               #leemos el .torrent

            filetools.rmdirtree(torrents_path_zip)                                  #Borramos la carpeta temporal

        #Si no es un archivo .torrent (RAR, HTML,..., vacío) damos error
        if not scrapertools.find_single_match(torrent_file, '^d\d+:.*?\d+:'):
            logger.error('No es un archivo Torrent: ' + url)
            torrents_path = ''
            if data_torrent:
                return (torrents_path, torrent_file)
            return torrents_path                                            #Si hay un error, devolvemos el "path" vacío
        
        #Salvamos el .torrent
        if not lookup:
            if not filetools.write(torrents_path_encode, torrent_file):
                logger.error('ERROR: Archivo .torrent no escrito: ' + torrents_path_encode)
                torrents_path = ''                                          #Si hay un error, devolvemos el "path" vacío
                torrent_file = ''                                           #... y el buffer del .torrent
                if data_torrent:
                    return (torrents_path, torrent_file)
                return torrents_path
    except:
        torrents_path = ''                                                  #Si hay un error, devolvemos el "path" vacío
        torrent_file = ''                                                   #... y el buffer del .torrent
        logger.error('Error en el proceso de descarga del .torrent: ' + url + ' / ' + torrents_path_encode)
        logger.error(traceback.format_exc())
    
    #logger.debug(torrents_path)
    if data_torrent:
        return (torrents_path, torrent_file)
    return torrents_path
    
    
def verify_url_torrent(url, timeout=5):
    """
    Verifica si el archivo .torrent al que apunta la url está disponible, descargándolo en un area temporal
    Entrada:    url
    Salida:     True o False dependiendo del resultado de la operación
    """

    if not url or url == 'javascript:;':                                            #Si la url viene vacía...
        return False                                                                #... volvemos con error
    torrents_path = caching_torrents(url, timeout=timeout, lookup=True)             #Descargamos el .torrent
    if torrents_path:                                                               #Si ha tenido éxito...
        return True
    else:
        return False
